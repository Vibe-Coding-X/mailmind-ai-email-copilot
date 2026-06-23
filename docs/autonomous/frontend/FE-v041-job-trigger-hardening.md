# FE v0.4.1 Job Trigger Hardening

## Scope

- Prevent repeated Sync Today, Generate Digest, and Refresh Digest triggers while jobs are active.
- Restore active job state after page refresh via the Jobs API.
- Keep existing v0.4 job card and retry UX.

## Implemented

- Mailbox sync button disables when the mailbox has a queued/running active job.
- Mailbox settings restores active email sync jobs from recent jobs.
- Digest dashboard disables Generate and Refresh while a digest job is queued/running.
- Digest dashboard restores active digest jobs from recent jobs.

## Limitations

- The frontend still relies on backend dedupe as the authority.
- If the worker is offline, active jobs remain visible until they reach a terminal state or polling times out.
