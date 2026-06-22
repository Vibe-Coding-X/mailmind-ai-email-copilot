Task ID: BE-v04-job-compatibility
Branch: feat/v04-job-experience
Parent branch: master
Goal: Verify whether the v0.3 Jobs API needs backend compatibility fixes for the v0.4 frontend job experience.
Scope:
- Checked the v0.3 jobs contract against backend routes, schemas, services, and tests.
- Confirmed the frontend can use existing endpoint paths and response fields.
- Confirmed `job_id` is the canonical frontend field.
- Confirmed retry returns the newly queued retry job.
Files changed:
- docs/contracts/v0.4/job-experience-contract-check.md
- docs/autonomous/backend/BE-v04-job-compatibility.md
Backend code changes:
- None.
API contract changes:
- No backend API shape change.
- Added a v0.4 contract check document that records actual endpoints, enums, fields, and non-blocking mismatches.
Database changes:
- None.
Migration added:
- None.
Environment variables:
- None.
Compatibility result:
- No backend compatibility fix was required.
Known risks:
- Completed digest job `result` may not always include `digest_id`; frontend falls back to `GET /api/digest/today`.
Next suggested task:
- Keep backend unchanged unless validation finds a concrete contract mismatch.
