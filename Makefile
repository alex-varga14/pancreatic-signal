ROOT := $(abspath .)
PILOT_PROXY_COMPOSE := docker compose -f docker-compose.yml -f docker-compose.pilot.yml -f docker-compose.pilot.proxy-demo.yml
PILOT_HEADER_COMPOSE := docker compose -f docker-compose.yml -f docker-compose.pilot.yml -f docker-compose.pilot.header-demo.yml

ifeq ($(wildcard $(ROOT)/apps/api/.venv/bin/python),)
PYTHON ?= python3
else
PYTHON ?= $(ROOT)/apps/api/.venv/bin/python
endif

ifeq ($(wildcard $(ROOT)/apps/api/.venv/bin/uvicorn),)
UVICORN ?= uvicorn
else
UVICORN ?= $(ROOT)/apps/api/.venv/bin/uvicorn
endif

api-install:
	cd apps/api && $(PYTHON) -m pip install -e .[dev]

api-dev:
	cd apps/api && $(UVICORN) app.main:app --reload --port 8000

web-dev:
	cd apps/web && npm run dev

bootstrap:
	$(PYTHON) scripts/bootstrap_demo_data.py

test-api:
	cd apps/api && $(PYTHON) -m pytest -q

validate:
	$(PYTHON) scripts/validate_repo.py

validate-strict:
	$(PYTHON) scripts/validate_repo.py --strict

benchmark-demo:
	$(PYTHON) scripts/write_demo_benchmark.py

refresh-demo-proof:
	$(PYTHON) scripts/write_demo_benchmark.py --out-dir docs/examples --basename demo-benchmark-current

benchmark-external:
	@test -n "$(LABELS)" || (echo "Usage: make benchmark-external LABELS=path/to/labels.jsonl PREDICTIONS=path/to/predictions.jsonl" && exit 2)
	@test -n "$(PREDICTIONS)" || (echo "Usage: make benchmark-external LABELS=path/to/labels.jsonl PREDICTIONS=path/to/predictions.jsonl" && exit 2)
	$(PYTHON) scripts/run_external_eval.py \
		--labels "$(LABELS)" \
		--predictions "$(PREDICTIONS)" \
		--threshold "$(or $(THRESHOLD),0.2)" \
		--top-k "$(or $(TOP_K),25)" \
		$(if $(OUT_DIR),--out-dir "$(OUT_DIR)",) \
		$(if $(BASENAME),--basename "$(BASENAME)",) \
		$(if $(DATASET_NAME),--dataset-name "$(DATASET_NAME)",) \
		$(if $(DATASET_SPLIT),--dataset-split "$(DATASET_SPLIT)",) \
		$(if $(PROJECT_NAME),--project-name "$(PROJECT_NAME)",) \
		$(if $(REPOSITORY_URL),--repository-url "$(REPOSITORY_URL)",) \
		$(if $(COMMIT_SHA),--commit-sha "$(COMMIT_SHA)",) \
		$(if $(NOTES),--notes "$(NOTES)",)

benchmark-external-sample:
	$(PYTHON) scripts/run_external_eval.py \
		--labels docs/examples/retrospective-benchmark-sample-labels.jsonl \
		--predictions docs/examples/retrospective-benchmark-sample-predictions.jsonl \
		--threshold 0.30 \
		--top-k 4 \
		--out-dir artifacts/benchmarks \
		--basename retrospective-benchmark-sample \
		--dataset-name deidentified-retrospective-sample \
		--dataset-split validation \
		--project-name "Pancreatic Signal" \
		--strength "High-confidence positives concentrate near the top of the review queue." \
		--strength "Reviewer-facing label cues remain visible in the generated casebook." \
		--limitation "Sample remains small and deidentified for repository use." \
		--limitation "One follow-up-only cyst surveillance case remains below threshold."

refresh-external-sample-proof:
	$(PYTHON) scripts/run_external_eval.py \
		--labels docs/examples/retrospective-benchmark-sample-labels.jsonl \
		--predictions docs/examples/retrospective-benchmark-sample-predictions.jsonl \
		--threshold 0.30 \
		--top-k 4 \
		--out-dir docs/examples \
		--basename retrospective-benchmark-sample-current \
		--dataset-name deidentified-retrospective-sample \
		--dataset-split validation \
		--project-name "Pancreatic Signal" \
		--strength "High-confidence positives concentrate near the top of the review queue." \
		--strength "Reviewer-facing label cues remain visible in the generated casebook." \
		--limitation "Sample remains small and deidentified for repository use." \
		--limitation "One follow-up-only cyst surveillance case remains below threshold."

pilot-smoke-evidence:
	@test -n "$(SUMMARY_DIR)" || (echo "Usage: make pilot-smoke-evidence SUMMARY_DIR=path/to/downloaded/pilot-smoke-artifacts [OUT_DIR=path] [HL7_DECISION=pending|keep-manual|promote-default] [HL7_RATIONALE='reason']" && exit 2)
	$(PYTHON) scripts/build_pilot_smoke_evidence.py \
		--summary-dir "$(SUMMARY_DIR)" \
		--out-json "$(or $(OUT_JSON),$(or $(OUT_DIR),$(SUMMARY_DIR))/pilot-smoke-evidence.json)" \
		--out-markdown "$(or $(OUT_MARKDOWN),$(or $(OUT_DIR),$(SUMMARY_DIR))/pilot-smoke-evidence.md)" \
		--hl7-decision "$(or $(HL7_DECISION),pending)" \
		$(if $(HL7_RATIONALE),--hl7-rationale "$(HL7_RATIONALE)",)

validate-benchmark-submission:
	@test -n "$(SUBMISSION)" || (echo "Usage: make validate-benchmark-submission SUBMISSION=path/to/submission.json" && exit 2)
	$(PYTHON) scripts/validate_benchmark_submission.py "$(SUBMISSION)"

smoke-proxy-auth:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode "$(or $(SMOKE_AUTH_MODE),proxy)" \
		--provider-preset "$(or $(SMOKE_PROVIDER_PRESET),generic)" \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),smoke-reviewer)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Smoke Reviewer)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),reviewer)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_BASE64)),--base64,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_CHECK_WEB)),--check-web,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_CHECK_IMPORTS_PAGE)),--check-imports-page,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_SEED_DEMO)),--seed-demo,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_DEMO)),--import-demo,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_SHARED_VISIBILITY)),--import-shared-visibility,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_ADAPTER_SHARED_VISIBILITY)),--import-adapter-shared-visibility,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_FHIR_DEMO)),--import-fhir-demo,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_HL7_DEMO)),--import-hl7-demo,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_DEMO_SITE_REJECTION)),--import-demo-site-rejection,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_ADAPTER_SITE_REJECTION)),--import-adapter-site-rejection,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_ADAPTER_AUDIT_VISIBILITY)),--import-adapter-audit-visibility,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_AUDIT_VISIBILITY)),--import-audit-visibility,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_FAILED_SHARED_VISIBILITY)),--import-failed-shared-visibility,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_ADAPTER_FAILED_SHARED_VISIBILITY)),--import-adapter-failed-shared-visibility,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_DEMO_PARSE_VALIDATION_FAILURE)),--import-demo-parse-validation-failure,) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_IMPORT_ADAPTER_FAILURES)),--import-adapter-failures,) \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_REJECTION_SITE),--rejection-site "$(SMOKE_REJECTION_SITE)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",) \
		$(if $(filter 1 true TRUE yes YES,$(SMOKE_SKIP_REVIEW)),--skip-review,) \
		--check-cases

pilot-proxy-demo-up:
	$(PILOT_PROXY_COMPOSE) up --build -d

pilot-proxy-demo-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-demo \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-shared-visibility \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-fhir-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-fhir-demo \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-hl7-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-hl7-demo \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-site-rejection-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-demo-site-rejection \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-adapter-site-rejection-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-site-rejection \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-parse-validation-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-demo-parse-validation-failure \
		--skip-review \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-adapter-failure-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-failures \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-adapter-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-shared-visibility \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-audit-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-audit-visibility \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-adapter-audit-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-audit-visibility \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-failed-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-failed-shared-visibility \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-adapter-failed-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--provider-preset keycloak \
		--header-name "$(or $(SMOKE_HEADER_NAME),X-Trusted-Identity)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),pdac-navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--base64 \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-failed-shared-visibility \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-proxy-demo-down:
	$(PILOT_PROXY_COMPOSE) down

pilot-header-demo-up:
	$(PILOT_HEADER_COMPOSE) up --build -d

pilot-header-demo-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-demo \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-shared-visibility \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-fhir-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-fhir-demo \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-hl7-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-hl7-demo \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-site-rejection-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-demo-site-rejection \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-adapter-site-rejection-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-site-rejection \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-parse-validation-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-demo-parse-validation-failure \
		--skip-review \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-adapter-failure-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-failures \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-adapter-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-shared-visibility \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_ACTION),--review-action "$(SMOKE_REVIEW_ACTION)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-audit-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-audit-visibility \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_DEMO_FILE),--demo-file "$(SMOKE_DEMO_FILE)",) \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-failed-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-failed-shared-visibility \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-adapter-audit-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_GROUPS),--groups "$(SMOKE_GROUPS)",) \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-audit-visibility \
		--rejection-site "$(or $(SMOKE_REJECTION_SITE),Out of Scope Site)" \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-adapter-failed-shared-visibility-smoke:
	$(PYTHON) scripts/smoke_proxy_auth.py \
		--base-url "$(or $(SMOKE_BASE_URL),http://localhost:8000)" \
		--web-url "$(or $(SMOKE_WEB_URL),http://localhost:3000)" \
		--auth-mode header \
		--user-id-header-name "$(or $(SMOKE_USER_ID_HEADER_NAME),X-User-ID)" \
		--display-name-header-name "$(or $(SMOKE_DISPLAY_NAME_HEADER_NAME),X-User-Name)" \
		--role-header-name "$(or $(SMOKE_ROLE_HEADER_NAME),X-User-Role)" \
		--sites-header-name "$(or $(SMOKE_SITES_HEADER_NAME),X-User-Sites)" \
		--user-id "$(or $(SMOKE_USER_ID),pilot-navigator)" \
		--display-name "$(or $(SMOKE_DISPLAY_NAME),Pilot Navigator)" \
		--role-value "$(or $(SMOKE_ROLE_VALUE),navigator)" \
		--sites "$(or $(SMOKE_SITES),Demo Hospital)" \
		$(if $(SMOKE_AUDIT_ALT_USER_ID),--audit-alt-user-id "$(SMOKE_AUDIT_ALT_USER_ID)",) \
		$(if $(SMOKE_AUDIT_ALT_DISPLAY_NAME),--audit-alt-display-name "$(SMOKE_AUDIT_ALT_DISPLAY_NAME)",) \
		$(if $(SMOKE_AUDIT_ALT_ROLE_VALUE),--audit-alt-role-value "$(SMOKE_AUDIT_ALT_ROLE_VALUE)",) \
		$(if $(SMOKE_AUDIT_ALT_SITES),--audit-alt-sites "$(SMOKE_AUDIT_ALT_SITES)",) \
		$(if $(SMOKE_AUDIT_ALT_GROUPS),--audit-alt-groups "$(SMOKE_AUDIT_ALT_GROUPS)",) \
		--check-web \
		--check-imports-page \
		--check-cases \
		--import-adapter-failed-shared-visibility \
		--skip-review \
		$(if $(SMOKE_RUN_ID),--run-id "$(SMOKE_RUN_ID)",) \
		$(if $(SMOKE_REVIEW_NOTE),--review-note "$(SMOKE_REVIEW_NOTE)",) \
		$(if $(SMOKE_WAIT_SECONDS),--wait-seconds "$(SMOKE_WAIT_SECONDS)",)

pilot-header-demo-down:
	$(PILOT_HEADER_COMPOSE) down

format-api:
	cd apps/api && $(PYTHON) -m ruff check . --fix && $(PYTHON) -m ruff format .

lint-web:
	cd apps/web && npm run lint

package:
	bash scripts/package_release.sh
