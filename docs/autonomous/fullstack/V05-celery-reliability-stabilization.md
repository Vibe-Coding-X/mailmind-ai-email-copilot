# V05 Celery Reliability Stabilization

This task stabilizes Celery without removing it or adding inline execution.

## Decisions

- Keep Celery for async sync and digest work.
- Treat PostgreSQL as the only job fact source.
- Use Redis only for broker/result transport and mailbox locks.
- Require committed DB jobs before Celery dispatch.
- Record `celery_task_id` on all dispatched sync and digest jobs.
- Return serializable ignored results for orphaned and stale worker tasks.
- Scope digest generation to one selected mailbox per request.

## Manual Test Outline

1. start PostgreSQL and Redis
2. run backend migrations
3. start backend
4. start Celery worker with `--pool=solo`
5. start frontend
6. purge old Celery messages before a clean test run
7. connect multiple mailboxes
8. trigger three mailbox sync jobs and confirm all receive `celery_task_id`
9. stop the worker, queue a job, restart the worker, and confirm queued work resumes
10. generate digest for a Gmail mailbox
11. generate digest for an IMAP mailbox
12. confirm old stale/orphaned tasks are ignored without `UnpickleableExceptionWrapper`
