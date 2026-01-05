# Production Runbook — Unified Media Asset Manager

This runbook summarizes essential production deployment, rollback, and monitoring procedures.

1) Prerequisites
- CI artifacts: backend/frontend container images published to a registry (GHCR or other).
- Secrets available in the target environment: `DATABASE_URL`, `JWT_SECRET`, `S3_BUCKET`, `S3_REGION`, provider API keys.
- Access to infra tooling (Terraform state, kubectl/az/gh/cloud CLI) and monitoring dashboards.

2) Deploy (Canary/Standard)
- Build & push images from CI (automated on `main`).
- Run DB migrations in a maintenance window (or on canary):
  - `alembic -c backend/alembic.ini upgrade head` against `DATABASE_URL`.
- Deploy backend image to staging canary (1 instance) and run smoke tests.
- Promote to full deployment when canary healthy (rolling update): update deployment image tag and perform rolling restart.

3) Smoke tests (post-deploy)
- Health endpoint: GET `/health` or GET `/` returns 200.
- Basic API flows: create universe, create element, generate image, upload media, attach component.
- Frontend UI load and key pages render (home, universe list, element page).

4) Rollback
- If critical issues appear (high error rate, data loss):
  - Roll back deployment to previous image tag via orchestration (kubectl rollout undo / restart previous task definition).
  - If DB migration caused incompatibility, restore from backup (follow DB restore runbook) and rollback app.
- Communicate to stakeholders and open incident channel.

5) Monitoring & Alerts (suggested)
- Error rate: Alert when 5xx error rate > 1% over 5 minutes.
- Latency: Alert when P95 response time > 2s for backend APIs.
- Disk/Storage: Alert when available storage < 20%.
- Job failures: Alert when CI or scheduled jobs fail consecutively.

6) Post-deploy checklist
- Verify CI artifacts and image tags.
- Verify migrations applied and DB schema version matches expectations.
- Run smoke tests and E2E (Playwright) suite.
- Confirm metrics show normal functioning for 15–30 minutes.

7) Secrets & Compliance
- Use a secrets manager (e.g., Azure Key Vault, AWS Secrets Manager) and never commit secrets to repo.
- Rotate `JWT_SECRET` and provider keys on a scheduled basis; update deployment with zero-downtime key rollout if possible.

8) Contacts & Escalation
- Primary on-call: team mailbox / PagerDuty (configure in your organization).
- In urgent incidents, escalate to the platform/ops owner and DB admin.

9) Notes
- This is a concise runbook; expand it with provider-specific commands (kubectl, az, gcloud) and internal contact info before production.
