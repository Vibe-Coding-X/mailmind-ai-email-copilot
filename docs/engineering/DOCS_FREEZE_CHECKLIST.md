# Docs Freeze Checklist

Use this checklist to decide whether the documentation is ready to freeze before implementation begins. A `PASS` means the current documents appear aligned enough for implementation. A `NEEDS REVIEW` or `NEEDS DECISION` item should be resolved or accepted as an explicit risk before development starts.

## Status Legend

- PASS
- FAIL
- NEEDS REVIEW
- NEEDS DECISION

## Checklist

| Area | Check | Status | Notes |
|---|---|---|---|
| Product / Architecture | PRD and SYSTEM_DESIGN are aligned | NEEDS REVIEW | Core direction is aligned, but PRD describes `gmail.modify` in minimum-permission wording while SECURITY/SYSTEM_DESIGN define it as self-use full-experience scope. |
| Database / API | DATABASE and API are aligned | PASS | API resources map to documented tables and ownership model. Implementation must still preserve `is_current` and user filtering. |
| AI / Database | AI_PIPELINE `suggested_action` enum matches DATABASE | PASS | Both define `reply_today`, `review_today`, `handle_before_deadline`, `ignore`, `archive_candidate`, `follow_up_later`, `no_action_required`. |
| Security / Database | SECURITY requirements are reflected in DATABASE | PASS | `mailbox_credentials`, `encryption_key_version`, and no long-term Access Token storage are documented. |
| Security / API | SECURITY requirements are reflected in API | PASS | API docs require auth, ownership, `gmail.modify`, `write_enabled`, and provider success before local read-state updates. |
| Data Flows / Database | DATA_FLOWS digest switch matches DATABASE transaction rules | PASS | Both require new version creation, item write, current switch after success, and old-current preservation on failure. |
| Task Harness | TASK_BREAKDOWN is executable | NEEDS REVIEW | Tasks are bounded with allowed files and acceptance criteria; dependency order should be reviewed before opening implementation issues. |
| Agent Harness | AGENTS defines execution rules and forbidden changes | PASS | Agent behavior, source-of-truth priority, and forbidden changes are defined. |
| README | README reflects current documentation status | PASS | README has been updated to describe documentation hardening before MVP implementation and list current docs. |
| Scope | No unresolved P0 architecture conflicts | NEEDS DECISION | No blocking architecture conflict found, but the `gmail.modify` wording should be decided before OAuth implementation. |
| GitHub Workflow | Issue and PR templates support task-driven work | PASS | Templates exist for task issues, design review, bugs, and PRs. |
| MVP Boundaries | Non-MVP features are deferred | PASS | Outlook, IMAP, AI Provider UI, Coding Agent config, and automatic sending remain outside MVP. |
