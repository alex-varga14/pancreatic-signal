# Go-Public Checklist

One-time steps for flipping this repository from private to public. Items marked (done) were completed on 2026-06-10/11; the rest require the repo to already be public or are maintainer-only decisions.

## Before flipping

- [x] No secrets, PHI, or database files in the tree or git history (audited 2026-06-10)
- [x] Sample data is synthetic and labeled as such
- [x] LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CITATION.cff present
- [x] Issue templates, PR template, dependabot config present
- [x] Stale merged branches deleted
- [x] Repo description and topics set
- [x] Discussions enabled
- [x] CI green: validate, pilot smoke, research watchtower
- [ ] Decide: commit author email exposure is acceptable (history contains a personal address on some commits; rewriting history is the only alternative and is not recommended)
- [ ] Tag and publish the v0.2.0 release with release notes

## Immediately after flipping

- [ ] Enable private vulnerability reporting (Settings → Code security, or `PUT /repos/{owner}/{repo}/private-vulnerability-reporting` — API returns 404 while the repo is private)
- [ ] Confirm secret scanning + push protection are active (automatic and free for public repos)
- [ ] Add branch protection on `main` (require PR + green `validate-strict`)
- [ ] Create a "Use cases & interest" Discussions category (landing zone for outreach replies)
- [ ] Seed 5–10 labeled issues, including `good first issue` items, so outreach doesn't land on an empty tracker
- [ ] Connect Zenodo for a citable DOI, then add the DOI to CITATION.cff and README

## Nice-to-have

- [ ] GitHub Pages or hosted read-only demo of `/proof` and `/research-intel`
- [ ] Short walkthrough video linked from README
- [ ] Devcontainer / Codespaces config for one-click classroom setup
