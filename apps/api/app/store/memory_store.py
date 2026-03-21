from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.db.session import SessionLocal, engine, init_db
from app.models import (
    Base,
    CaseRecord,
    FindingRecord,
    ImportRunItemRecord,
    ImportRunRecord,
    ReportRecord,
    ReviewActionRecord,
)
from app.schemas.case import CaseDetail, CaseListItem, ReviewAction, ReviewActionInput
from app.schemas.feedback import FeedbackSummary, ReviewerFeedbackInput, ReviewerFeedbackRecord
from app.schemas.imports import ImportAuditItem, ImportRunDetail, ImportRunSummary
from app.schemas.triage import ImportMetadata, ReportInput, TriageResult
from app.services.hybrid_analysis import analyze_hybrid_report
from app.services.ontology import load_ontology
from app.services.review_feedback import parse_feedback_note, serialize_feedback_note, summarize_feedback
from app.services.text_utils import normalize_text

_EPOCH = datetime.fromtimestamp(0, tz=timezone.utc)
_URGENCY_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


class SqlAlchemyCaseStore:
    def __init__(self) -> None:
        self._initialized = False

    def _ensure_db(self) -> None:
        if not self._initialized:
            init_db()
            self._initialized = True

    def reset(self) -> None:
        self._ensure_db()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def upsert_from_triage(self, payload: ReportInput, result: TriageResult) -> None:
        self._ensure_db()
        labels_by_code = self._labels_by_code()
        normalized = normalize_text(payload.report_text)
        import_metadata = payload.import_metadata

        with SessionLocal.begin() as session:
            case = session.get(CaseRecord, payload.case_id)
            if case is None:
                case = CaseRecord(
                    case_id=payload.case_id,
                    report_id=payload.report_id,
                    score=result.score,
                    urgency=result.urgency,
                    status="new",
                    site=payload.site,
                    assigned_to=None,
                    rationale_codes=result.rationale_codes,
                )
                session.add(case)
                session.flush()
            else:
                case.report_id = payload.report_id
                case.score = result.score
                case.urgency = result.urgency
                case.site = payload.site or case.site
                case.rationale_codes = result.rationale_codes

            report = session.get(ReportRecord, payload.report_id)
            if report is None:
                report = ReportRecord(
                    report_id=payload.report_id,
                    case_id=payload.case_id,
                    report_datetime=payload.report_datetime,
                    modality=payload.modality,
                    site=payload.site,
                    raw_text=payload.report_text,
                    normalized_text=normalized,
                )
                self._merge_report_import_metadata(report, import_metadata, overwrite_missing=True)
                session.add(report)
            else:
                report.case_id = payload.case_id
                report.report_datetime = payload.report_datetime
                report.modality = payload.modality
                report.site = payload.site
                report.raw_text = payload.report_text
                report.normalized_text = normalized
                self._merge_report_import_metadata(report, import_metadata)

            # Postgres enforces the findings -> reports foreign key immediately, so make sure
            # the report row exists before we replace evidence records for this case.
            session.flush()
            session.execute(delete(FindingRecord).where(FindingRecord.case_id == payload.case_id))
            for sort_order, item in enumerate(result.evidence):
                session.add(
                    FindingRecord(
                        case_id=payload.case_id,
                        report_id=payload.report_id,
                        code=item.code,
                        label=labels_by_code.get(item.code),
                        section=item.section,
                        sentence_index=item.sentence_index,
                        char_start=item.start,
                        char_end=item.end,
                        evidence_text=item.text,
                        score_contribution=self._score_contribution(item.code),
                        sort_order=sort_order,
                    )
                )

    def list_cases(
        self,
        *,
        status: str | None = None,
        urgency: str | None = None,
        site: str | None = None,
        accessible_sites: list[str] | None = None,
        reviewer: str | None = None,
        modality: str | None = None,
        rationale: str | None = None,
        feedback_label: str | None = None,
        needs_feedback: bool = False,
        disagreement_only: bool = False,
        hybrid_delta_min: float | None = None,
        hybrid_review_priority: str | None = None,
        active_learning_priority: str | None = None,
        active_learning_only: bool = False,
        include_hybrid: bool = False,
        q: str | None = None,
        sort_by: str = "score",
        sort_dir: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[CaseListItem]:
        self._ensure_db()

        with SessionLocal() as session:
            rows = session.execute(
                select(CaseRecord, ReportRecord)
                .join(ReportRecord, ReportRecord.report_id == CaseRecord.report_id, isouter=True)
            ).all()

            items: list[CaseListItem] = []
            status_l = status.lower() if status else None
            urgency_l = urgency.lower() if urgency else None
            site_l = site.lower() if site else None
            reviewer_l = reviewer.lower() if reviewer else None
            modality_l = modality.lower() if modality else None
            rationale_l = rationale.lower() if rationale else None
            accessible_sites_l = (
                {item.strip().lower() for item in accessible_sites if item.strip()}
                if accessible_sites is not None
                else None
            )
            feedback_label_l = feedback_label.lower() if feedback_label else None
            hybrid_review_priority_l = hybrid_review_priority.lower() if hybrid_review_priority else None
            active_learning_priority_l = active_learning_priority.lower() if active_learning_priority else None
            query_l = q.lower() if q else None
            needs_hybrid = (
                include_hybrid
                or sort_by == "hybrid_score"
                or sort_by == "hybrid_delta"
                or hybrid_review_priority_l is not None
                or active_learning_priority_l is not None
                or active_learning_only
                or disagreement_only
                or hybrid_delta_min is not None
            )

            for case, report in rows:
                if accessible_sites_l is not None and (case.site or "").lower() not in accessible_sites_l:
                    continue
                if status_l and case.status.lower() != status_l:
                    continue
                if urgency_l and case.urgency.lower() != urgency_l:
                    continue
                if site_l and (case.site or "").lower() != site_l:
                    continue
                if modality_l and (report.modality if report else "").lower() != modality_l:
                    continue
                if rationale_l and not any(
                    rationale_l in code.lower() for code in (case.rationale_codes or [])
                ):
                    continue
                if reviewer_l and not self._matches_reviewer(case, reviewer_l):
                    continue
                if query_l and query_l not in case.case_id.lower() and query_l not in case.report_id.lower():
                    continue

                review_actions = self._load_review_actions(session, case.case_id)
                feedback_records = self._feedback_records(review_actions)
                if needs_feedback and feedback_records:
                    continue
                if feedback_label_l and not any(
                    feedback.label.lower() == feedback_label_l for feedback in feedback_records
                ):
                    continue

                latest_feedback = feedback_records[-1] if feedback_records else None

                hybrid_analysis = None
                hybrid_delta = None
                disagreement_level = None
                if needs_hybrid:
                    hybrid_analysis = self._build_hybrid_analysis(
                        session=session,
                        case=case,
                        report=report,
                    )
                    hybrid_delta = round(hybrid_analysis.calibrated_score - case.score, 4)
                    disagreement_level = self._disagreement_level(hybrid_delta)
                    if disagreement_only and disagreement_level is None:
                        continue
                    if hybrid_delta_min is not None and hybrid_delta < hybrid_delta_min:
                        continue
                    if hybrid_review_priority_l and hybrid_analysis.review_priority.lower() != hybrid_review_priority_l:
                        continue
                    if active_learning_priority_l and (
                        hybrid_analysis.active_learning_priority.lower() != active_learning_priority_l
                    ):
                        continue
                    if active_learning_only and hybrid_analysis.active_learning_priority.lower() == "low":
                        continue

                items.append(
                    CaseListItem(
                        case_id=case.case_id,
                        report_id=case.report_id,
                        report_datetime=(report.report_datetime if report else None),
                        modality=(report.modality if report else None),
                        score=case.score,
                        urgency=case.urgency,
                        status=case.status,
                        site=case.site,
                        assigned_to=case.assigned_to,
                        top_rationale=(case.rationale_codes[0] if case.rationale_codes else None),
                        hybrid_score=(
                            hybrid_analysis.calibrated_score
                            if hybrid_analysis is not None
                            else None
                        ),
                        hybrid_delta=hybrid_delta,
                        hybrid_confidence=(
                            hybrid_analysis.confidence_label
                            if hybrid_analysis is not None
                            else None
                        ),
                        hybrid_review_priority=(
                            hybrid_analysis.review_priority
                            if hybrid_analysis is not None
                            else None
                        ),
                        active_learning_priority=(
                            hybrid_analysis.active_learning_priority
                            if hybrid_analysis is not None
                            else None
                        ),
                        disagreement_level=disagreement_level,
                        review_feedback_count=len(feedback_records),
                        latest_feedback_label=(
                            latest_feedback.label
                            if latest_feedback is not None
                            else None
                        ),
                        latest_feedback_disposition=(
                            latest_feedback.disposition
                            if latest_feedback is not None
                            else None
                        ),
                    )
                )

            ordered = self._sort_case_items(items, sort_by=sort_by, sort_dir=sort_dir)
            return ordered[offset : offset + limit]

    def get_case(self, case_id: str) -> CaseDetail | None:
        self._ensure_db()

        with SessionLocal() as session:
            case = session.get(CaseRecord, case_id)
            if case is None:
                return None

            report = session.get(ReportRecord, case.report_id)
            findings = session.execute(
                select(FindingRecord)
                .where(FindingRecord.case_id == case_id)
                .order_by(FindingRecord.sort_order, FindingRecord.char_start, FindingRecord.id)
            ).scalars().all()
            review_actions = self._load_review_actions(session, case_id)
            feedback_records = self._feedback_records(review_actions)

            return CaseDetail(
                case_id=case.case_id,
                report_id=case.report_id,
                report_datetime=(report.report_datetime if report else None),
                modality=(report.modality if report else None),
                score=case.score,
                urgency=case.urgency,
                status=case.status,
                site=case.site,
                assigned_to=case.assigned_to,
                report_text=(report.raw_text if report else ""),
                import_metadata=self._report_import_metadata(report),
                rationale_codes=case.rationale_codes or [],
                evidence=[
                    {
                        "text": finding.evidence_text,
                        "section": finding.section,
                        "start": finding.char_start,
                        "end": finding.char_end,
                        "code": finding.code,
                        "sentence_index": finding.sentence_index,
                    }
                    for finding in findings
                ],
                review_actions=[
                    ReviewAction(
                        action=action.action,
                        reviewer=action.reviewer,
                        note=(
                            summarize_feedback(feedback)
                            if action.action == "feedback"
                            and (feedback := parse_feedback_note(
                                reviewer=action.reviewer,
                                note=action.note,
                                created_at=action.created_at,
                            ))
                            else action.note
                        ),
                        assigned_to=action.assigned_to,
                        created_at=action.created_at,
                    )
                    for action in review_actions
                ],
                review_feedback=feedback_records,
            )

    def add_review_action(self, case_id: str, payload: ReviewActionInput) -> dict[str, str | None]:
        self._ensure_db()

        with SessionLocal.begin() as session:
            case = session.get(CaseRecord, case_id)
            if case is None:
                raise KeyError(case_id)

            assigned_to = payload.assigned_to or None
            if payload.action == "assign" and not assigned_to:
                assigned_to = payload.reviewer

            if assigned_to:
                case.assigned_to = assigned_to

            if payload.action in {"in_review", "escalate", "dismiss", "close", "reopen"}:
                case.status = {
                    "in_review": "in_review",
                    "escalate": "escalated",
                    "dismiss": "dismissed",
                    "close": "closed",
                    "reopen": "new",
                }[payload.action]

            session.add(
                ReviewActionRecord(
                    case_id=case_id,
                    action=payload.action,
                    reviewer=payload.reviewer,
                    note=payload.note,
                    assigned_to=assigned_to,
                )
            )
            session.flush()

            return {"status": case.status, "assigned_to": case.assigned_to}

    def add_review_feedback(self, case_id: str, payload: ReviewerFeedbackInput) -> ReviewerFeedbackRecord:
        self._ensure_db()

        with SessionLocal.begin() as session:
            case = session.get(CaseRecord, case_id)
            if case is None:
                raise KeyError(case_id)

            action = ReviewActionRecord(
                case_id=case_id,
                action="feedback",
                reviewer=payload.reviewer,
                note=serialize_feedback_note(payload),
                assigned_to=case.assigned_to,
            )
            session.add(action)
            session.flush()

            return ReviewerFeedbackRecord(
                reviewer=payload.reviewer,
                label=payload.label,
                disposition=payload.disposition,
                error_bucket=payload.error_bucket,
                notes=payload.notes,
                created_at=action.created_at,
            )

    def export_cases(
        self,
        *,
        status: str | None = None,
        urgency: str | None = None,
        site: str | None = None,
        accessible_sites: list[str] | None = None,
        reviewer: str | None = None,
    ) -> list[dict[str, object]]:
        self._ensure_db()

        rows: list[dict[str, object]] = []
        case_items = self.list_cases(
            status=status,
            urgency=urgency,
            site=site,
            accessible_sites=accessible_sites,
            reviewer=reviewer,
            include_hybrid=True,
            limit=10_000,
            offset=0,
        )
        for item in case_items:
            detail = self.get_case(item.case_id)
            rows.append(
                {
                    "case_id": item.case_id,
                    "report_id": item.report_id,
                    "report_datetime": item.report_datetime.isoformat() if item.report_datetime else None,
                    "modality": item.modality,
                    **self._export_import_metadata(detail.import_metadata if detail else None),
                    "score": item.score,
                    "hybrid_score": item.hybrid_score,
                    "hybrid_delta": item.hybrid_delta,
                    "urgency": item.urgency,
                    "disagreement_level": item.disagreement_level,
                    "status": item.status,
                    "site": item.site,
                    "assigned_to": item.assigned_to,
                    "top_rationale": item.top_rationale,
                    "review_feedback_count": item.review_feedback_count,
                    "latest_feedback_label": item.latest_feedback_label,
                    "latest_feedback_disposition": item.latest_feedback_disposition,
                    "rationale_codes": ";".join(detail.rationale_codes) if detail else "",
                    "evidence_count": len(detail.evidence) if detail else 0,
                    "review_action_count": len(detail.review_actions) if detail else 0,
                }
            )
        return rows

    def summarize_feedback(self, *, accessible_sites: list[str] | None = None) -> FeedbackSummary:
        self._ensure_db()

        with SessionLocal() as session:
            rows = session.execute(
                select(CaseRecord, ReportRecord)
                .join(ReportRecord, ReportRecord.report_id == CaseRecord.report_id, isouter=True)
            ).all()

            total_feedback = 0
            labeled_cases = 0
            unlabeled_cases = 0
            unlabeled_active_learning_cases = 0
            label_distribution: dict[str, int] = {}
            disposition_distribution: dict[str, int] = {}
            error_bucket_distribution: dict[str, int] = {}
            accessible_sites_l = (
                {item.strip().lower() for item in accessible_sites if item.strip()}
                if accessible_sites is not None
                else None
            )

            for case, report in rows:
                if accessible_sites_l is not None and (case.site or "").lower() not in accessible_sites_l:
                    continue
                review_actions = self._load_review_actions(session, case.case_id)
                feedback_records = self._feedback_records(review_actions)

                if feedback_records:
                    labeled_cases += 1
                    total_feedback += len(feedback_records)
                    for feedback in feedback_records:
                        label_distribution[feedback.label] = label_distribution.get(feedback.label, 0) + 1
                        disposition_distribution[feedback.disposition] = (
                            disposition_distribution.get(feedback.disposition, 0) + 1
                        )
                        if feedback.error_bucket:
                            error_bucket_distribution[feedback.error_bucket] = (
                                error_bucket_distribution.get(feedback.error_bucket, 0) + 1
                            )
                    continue

                unlabeled_cases += 1
                hybrid = self._build_hybrid_analysis(session=session, case=case, report=report)
                if hybrid.active_learning_priority != "low":
                    unlabeled_active_learning_cases += 1

            return FeedbackSummary(
                total_feedback=total_feedback,
                labeled_cases=labeled_cases,
                unlabeled_cases=unlabeled_cases,
                unlabeled_active_learning_cases=unlabeled_active_learning_cases,
                label_distribution=label_distribution,
                disposition_distribution=disposition_distribution,
                error_bucket_distribution=error_bucket_distribution,
            )

    def export_review_feedback(self, *, accessible_sites: list[str] | None = None) -> list[dict[str, object]]:
        self._ensure_db()

        with SessionLocal() as session:
            rows = session.execute(
                select(CaseRecord, ReportRecord)
                .join(ReportRecord, ReportRecord.report_id == CaseRecord.report_id, isouter=True)
            ).all()
            exported: list[dict[str, object]] = []
            accessible_sites_l = (
                {item.strip().lower() for item in accessible_sites if item.strip()}
                if accessible_sites is not None
                else None
            )

            for case, report in rows:
                if accessible_sites_l is not None and (case.site or "").lower() not in accessible_sites_l:
                    continue
                review_actions = session.execute(
                    select(ReviewActionRecord)
                    .where(ReviewActionRecord.case_id == case.case_id)
                    .order_by(ReviewActionRecord.created_at, ReviewActionRecord.id)
                ).scalars().all()
                feedback_records = self._feedback_records(review_actions)
                if not feedback_records:
                    continue

                hybrid = self._build_hybrid_analysis(session=session, case=case, report=report)
                evidence = session.execute(
                    select(FindingRecord)
                    .where(FindingRecord.case_id == case.case_id)
                    .order_by(FindingRecord.sort_order, FindingRecord.char_start, FindingRecord.id)
                ).scalars().all()
                evidence_texts = [finding.evidence_text for finding in evidence]

                for feedback in feedback_records:
                    exported.append(
                        {
                            "case_id": case.case_id,
                            "report_id": case.report_id,
                            "report_datetime": report.report_datetime.isoformat() if report else None,
                            "modality": report.modality if report else None,
                            **self._export_import_metadata(self._report_import_metadata(report)),
                            "site": case.site,
                            "score": case.score,
                            "hybrid_score": hybrid.calibrated_score,
                            "urgency": case.urgency,
                            "hybrid_review_priority": hybrid.review_priority,
                            "active_learning_priority": hybrid.active_learning_priority,
                            "rationale_codes": case.rationale_codes or [],
                            "evidence_texts": evidence_texts,
                            "report_text": report.raw_text if report else "",
                            "reviewer": feedback.reviewer,
                            "label": feedback.label,
                            "disposition": feedback.disposition,
                            "error_bucket": feedback.error_bucket,
                            "notes": feedback.notes,
                            "created_at": feedback.created_at.isoformat(),
                        }
                    )

            return exported

    def classify_import_upserts(self, reports: list[ReportInput]) -> dict[str, str]:
        self._ensure_db()

        report_ids = {report.report_id for report in reports}
        case_ids = {report.case_id for report in reports}

        with SessionLocal() as session:
            existing_report_ids = set(
                session.execute(
                    select(ReportRecord.report_id).where(ReportRecord.report_id.in_(report_ids))
                ).scalars().all()
            )
            existing_case_ids = set(
                session.execute(
                    select(CaseRecord.case_id).where(CaseRecord.case_id.in_(case_ids))
                ).scalars().all()
            )

        outcomes: dict[str, str] = {}
        for report in reports:
            outcomes[report.report_id] = (
                "updated"
                if report.report_id in existing_report_ids or report.case_id in existing_case_ids
                else "created"
            )
        return outcomes

    def record_import_run(
        self,
        *,
        source_format: str,
        source_name: str | None,
        actor_user_id: str,
        actor_role: str,
        actor_site_scope: list[str] | None,
        imported_sites: list[str],
        status: str,
        processed: int,
        flagged: int,
        created: int,
        updated: int,
        failed: int,
        failure_counts: dict[str, int],
        started_at: datetime,
        completed_at: datetime,
        items: list[ImportAuditItem],
    ) -> ImportRunSummary:
        self._ensure_db()

        with SessionLocal.begin() as session:
            run = ImportRunRecord(
                source_format=source_format,
                source_name=source_name,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                actor_site_scope=actor_site_scope,
                imported_sites=imported_sites,
                status=status,
                processed_count=processed,
                flagged_count=flagged,
                created_count=created,
                updated_count=updated,
                failed_count=failed,
                failure_counts=failure_counts,
                started_at=started_at,
                completed_at=completed_at,
            )
            session.add(run)
            session.flush()

            for item in items:
                session.add(
                    ImportRunItemRecord(
                        run_id=run.id,
                        item_index=item.item_index,
                        status=item.status,
                        source_identifier=item.source_identifier,
                        site=item.site,
                        case_id=item.case_id,
                        report_id=item.report_id,
                        error_bucket=item.error_bucket,
                        error_detail=item.error_detail,
                    )
                )

            session.flush()
            return self._import_run_summary(run)

    def list_import_runs(
        self,
        *,
        actor_user_id: str,
        accessible_sites: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ImportRunSummary]:
        self._ensure_db()

        with SessionLocal() as session:
            runs = session.execute(
                select(ImportRunRecord)
                .order_by(ImportRunRecord.started_at.desc(), ImportRunRecord.id.desc())
            ).scalars().all()

            accessible_sites_l = (
                {item.strip().lower() for item in accessible_sites if item.strip()}
                if accessible_sites is not None
                else None
            )
            visible_runs = [
                self._import_run_summary(run)
                for run in runs
                if self._run_visible_to_site_scope(run, actor_user_id=actor_user_id, accessible_sites=accessible_sites_l)
            ]
            return visible_runs[offset : offset + limit]

    def get_import_run(
        self,
        run_id: int,
        *,
        actor_user_id: str,
        accessible_sites: list[str] | None = None,
    ) -> ImportRunDetail | None:
        self._ensure_db()

        accessible_sites_l = (
            {item.strip().lower() for item in accessible_sites if item.strip()}
            if accessible_sites is not None
            else None
        )

        with SessionLocal() as session:
            run = session.get(ImportRunRecord, run_id)
            if run is None or not self._run_visible_to_site_scope(
                run,
                actor_user_id=actor_user_id,
                accessible_sites=accessible_sites_l,
            ):
                return None

            items = session.execute(
                select(ImportRunItemRecord)
                .where(ImportRunItemRecord.run_id == run_id)
                .order_by(ImportRunItemRecord.item_index, ImportRunItemRecord.id)
            ).scalars().all()

            summary = self._import_run_summary(run)
            return ImportRunDetail(
                **summary.model_dump(),
                items=[self._import_run_item(item) for item in items],
            )

    @staticmethod
    def _labels_by_code() -> dict[str, str]:
        ontology = load_ontology()
        return {
            family["code"]: family["label"]
            for family in ontology.get("families", [])
            if "code" in family and "label" in family
        }

    @staticmethod
    def _matches_reviewer(case: CaseRecord, reviewer: str) -> bool:
        if (case.assigned_to or "").lower() == reviewer:
            return True
        return any(action.reviewer.lower() == reviewer for action in case.review_actions)

    @staticmethod
    def _sort_case_items(
        items: list[CaseListItem],
        *,
        sort_by: str,
        sort_dir: str,
    ) -> list[CaseListItem]:
        reverse = sort_dir != "asc"

        if sort_by == "hybrid_score":
            return sorted(
                items,
                key=lambda item: (
                    item.hybrid_score if item.hybrid_score is not None else -1.0,
                    item.score,
                    _URGENCY_RANK.get(item.urgency.lower(), -1),
                    item.report_datetime or _EPOCH,
                    item.case_id,
                ),
                reverse=reverse,
            )

        if sort_by == "hybrid_delta":
            return sorted(
                items,
                key=lambda item: (
                    item.hybrid_delta if item.hybrid_delta is not None else -1.0,
                    item.hybrid_score if item.hybrid_score is not None else -1.0,
                    item.score,
                    item.case_id,
                ),
                reverse=reverse,
            )

        if sort_by == "review_feedback_count":
            return sorted(
                items,
                key=lambda item: (
                    item.review_feedback_count,
                    item.hybrid_score if item.hybrid_score is not None else -1.0,
                    item.score,
                    item.case_id,
                ),
                reverse=reverse,
            )

        if sort_by == "report_datetime":
            return sorted(
                items,
                key=lambda item: (
                    item.report_datetime or _EPOCH,
                    item.score,
                    item.case_id,
                ),
                reverse=reverse,
            )

        if sort_by == "urgency":
            return sorted(
                items,
                key=lambda item: (
                    _URGENCY_RANK.get(item.urgency.lower(), -1),
                    item.score,
                    item.case_id,
                ),
                reverse=reverse,
            )

        if sort_by == "case_id":
            return sorted(
                items,
                key=lambda item: item.case_id,
                reverse=reverse,
            )

        return sorted(
            items,
            key=lambda item: (
                item.score,
                _URGENCY_RANK.get(item.urgency.lower(), -1),
                item.report_datetime or _EPOCH,
                item.case_id,
            ),
            reverse=reverse,
        )

    @staticmethod
    def _build_hybrid_analysis(
        *,
        session,
        case: CaseRecord,
        report: ReportRecord | None,
    ):
        findings = session.execute(
            select(FindingRecord)
            .where(FindingRecord.case_id == case.case_id)
            .order_by(FindingRecord.sort_order, FindingRecord.char_start, FindingRecord.id)
        ).scalars().all()
        evidence = [
            {
                "text": finding.evidence_text,
                "section": finding.section,
                "start": finding.char_start,
                "end": finding.char_end,
                "code": finding.code,
                "sentence_index": finding.sentence_index,
            }
            for finding in findings
        ]
        return analyze_hybrid_report(
            report_text=(report.raw_text if report else ""),
            score=case.score,
            urgency=case.urgency,
            rationale_codes=case.rationale_codes or [],
            evidence=evidence,
        )

    @staticmethod
    def _feedback_records(review_actions: list[ReviewActionRecord]) -> list[ReviewerFeedbackRecord]:
        feedback_records: list[ReviewerFeedbackRecord] = []
        for action in review_actions:
            if action.action != "feedback":
                continue
            feedback = parse_feedback_note(
                reviewer=action.reviewer,
                note=action.note,
                created_at=action.created_at,
            )
            if feedback is not None:
                feedback_records.append(feedback)
        return feedback_records

    @staticmethod
    def _load_review_actions(session, case_id: str) -> list[ReviewActionRecord]:
        return session.execute(
            select(ReviewActionRecord)
            .where(ReviewActionRecord.case_id == case_id)
            .order_by(ReviewActionRecord.created_at, ReviewActionRecord.id)
        ).scalars().all()

    @staticmethod
    def _disagreement_level(hybrid_delta: float | None) -> str | None:
        if hybrid_delta is None:
            return None
        absolute_delta = abs(hybrid_delta)
        if absolute_delta >= 0.2:
            return "high"
        if absolute_delta >= 0.1:
            return "moderate"
        if absolute_delta >= 0.05:
            return "low"
        return None

    @staticmethod
    def _score_contribution(code: str) -> float | None:
        ontology = load_ontology()
        for family in ontology.get("families", []):
            if family.get("code") == code:
                return float(family["weight"])
        return None

    @staticmethod
    def _run_visible_to_site_scope(
        run: ImportRunRecord,
        *,
        actor_user_id: str,
        accessible_sites: set[str] | None,
    ) -> bool:
        if run.actor_user_id == actor_user_id:
            return True
        if accessible_sites is None:
            return True

        run_scope = {
            item.strip().lower()
            for item in (run.actor_site_scope or [])
            if isinstance(item, str) and item.strip()
        }
        imported_sites = {
            item.strip().lower()
            for item in (run.imported_sites or [])
            if isinstance(item, str) and item.strip()
        }

        if run_scope and not run_scope.issubset(accessible_sites):
            return False
        if imported_sites and not imported_sites.issubset(accessible_sites):
            return False
        return bool(run_scope or imported_sites)

    @staticmethod
    def _import_run_summary(run: ImportRunRecord) -> ImportRunSummary:
        return ImportRunSummary(
            run_id=run.id,
            source_format=run.source_format,
            source_name=run.source_name,
            actor_user_id=run.actor_user_id,
            actor_role=run.actor_role,
            actor_site_scope=run.actor_site_scope,
            imported_sites=run.imported_sites or [],
            status=run.status,
            processed=run.processed_count,
            flagged=run.flagged_count,
            created=run.created_count,
            updated=run.updated_count,
            failed=run.failed_count,
            failure_counts=run.failure_counts or {},
            started_at=run.started_at,
            completed_at=run.completed_at,
        )

    @staticmethod
    def _import_run_item(item: ImportRunItemRecord) -> ImportAuditItem:
        return ImportAuditItem(
            item_index=item.item_index,
            status=item.status,
            source_identifier=item.source_identifier,
            site=item.site,
            case_id=item.case_id,
            report_id=item.report_id,
            error_bucket=item.error_bucket,
            error_detail=item.error_detail,
        )

    @staticmethod
    def _merge_report_import_metadata(
        report: ReportRecord,
        metadata: ImportMetadata | None,
        *,
        overwrite_missing: bool = False,
    ) -> None:
        if metadata is None:
            return

        for field_name, value in metadata.model_dump().items():
            if value is None and not overwrite_missing:
                continue
            setattr(report, field_name, value)

    @staticmethod
    def _report_import_metadata(report: ReportRecord | None) -> ImportMetadata | None:
        if report is None:
            return None

        data = {
            "patient_identifier": report.patient_identifier,
            "encounter_identifier": report.encounter_identifier,
            "accession_number": report.accession_number,
            "ordering_provider": report.ordering_provider,
            "source_system": report.source_system,
            "source_format": report.source_format,
            "import_source_id": report.import_source_id,
        }
        populated = {key: value for key, value in data.items() if value is not None}
        if not populated:
            return None
        return ImportMetadata.model_validate(populated)

    @staticmethod
    def _export_import_metadata(metadata: ImportMetadata | None) -> dict[str, object]:
        fields = {
            "patient_identifier": None,
            "encounter_identifier": None,
            "accession_number": None,
            "ordering_provider": None,
            "source_system": None,
            "source_format": None,
            "import_source_id": None,
        }
        if metadata is None:
            return fields
        return {
            **fields,
            **metadata.model_dump(),
        }


CASE_STORE = SqlAlchemyCaseStore()
