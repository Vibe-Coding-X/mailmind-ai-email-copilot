# MailMind Documentation

MailMind 文档入口。

正式产品名：MailMind  
产品类型 / 副标题：AI Email Copilot  
仓库名：`mailmind-ai-email-copilot`

## 推荐阅读顺序

1. [`product/PRD.md`](product/PRD.md) — 产品目标、MVP 范围和用户流程。
2. [`architecture/SYSTEM_DESIGN.md`](architecture/SYSTEM_DESIGN.md) — 系统级目标、总体架构、核心原则和专题文档索引。
3. [`architecture/DATA_FLOWS.md`](architecture/DATA_FLOWS.md) — 注册登录、Gmail 授权、同步、日报生成和刷新流程。
4. [`database/DATABASE_DESIGN.md`](database/DATABASE_DESIGN.md) — 表结构、字段、枚举、约束和迁移策略。
5. [`api/API_DESIGN.md`](api/API_DESIGN.md) — API 路由、鉴权前置条件和交互规则。
6. [`ai/AI_PIPELINE.md`](ai/AI_PIPELINE.md) — AI Pipeline、LLM 接口、结构化输出和安全约束。
7. [`security/SECURITY.md`](security/SECURITY.md) — OAuth、Token、日志、密钥和公网部署安全。
8. [`frontend/FRONTEND_DESIGN.md`](frontend/FRONTEND_DESIGN.md) — 前端页面结构、Dashboard 区域和状态原则。
9. [`engineering/DEVELOPMENT.md`](engineering/DEVELOPMENT.md) — 本地开发、服务组成、目录结构和 Docker Compose。
10. [`engineering/TASK_BREAKDOWN.md`](engineering/TASK_BREAKDOWN.md) — Codex 可执行任务说明书。
11. [`engineering/AGENTS.md`](engineering/AGENTS.md) — Codex 执行规则和禁止事项。
12. [`engineering/DECISION_LOG.md`](engineering/DECISION_LOG.md) — 关键架构决策记录。
13. [`engineering/DOCS_FREEZE_CHECKLIST.md`](engineering/DOCS_FREEZE_CHECKLIST.md) — 进入实现前的文档冻结检查。
14. [`engineering/REVIEW_CHECKLIST.md`](engineering/REVIEW_CHECKLIST.md) — 后续任务和 PR 审查清单。

## 专题文档

| 主题 | 文档 |
|---|---|
| 前端设计 | [`frontend/FRONTEND_DESIGN.md`](frontend/FRONTEND_DESIGN.md) |
| 核心数据流 | [`architecture/DATA_FLOWS.md`](architecture/DATA_FLOWS.md) |
| 异步任务 | [`engineering/ASYNC_TASKS.md`](engineering/ASYNC_TASKS.md) |
| Job 执行模型 | [`architecture/JOB_EXECUTION_MODEL.md`](architecture/JOB_EXECUTION_MODEL.md) |
| 增量同步 | [`engineering/INCREMENTAL_SYNC.md`](engineering/INCREMENTAL_SYNC.md) |
| 时区规则 | [`engineering/TIMEZONE_RULES.md`](engineering/TIMEZONE_RULES.md) |
| 任务拆分 | [`engineering/TASK_BREAKDOWN.md`](engineering/TASK_BREAKDOWN.md) |
| Agent 协作说明 | [`engineering/AGENTS.md`](engineering/AGENTS.md) |
| 架构决策记录 | [`engineering/DECISION_LOG.md`](engineering/DECISION_LOG.md) |
| 文档冻结检查 | [`engineering/DOCS_FREEZE_CHECKLIST.md`](engineering/DOCS_FREEZE_CHECKLIST.md) |
| 审查清单 | [`engineering/REVIEW_CHECKLIST.md`](engineering/REVIEW_CHECKLIST.md) |
| Release notes | [`release-notes/v0.2.0-digest-ai.md`](release-notes/v0.2.0-digest-ai.md) |
