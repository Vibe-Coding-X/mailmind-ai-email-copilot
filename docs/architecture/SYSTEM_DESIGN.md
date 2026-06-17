# AI Email Copilot 系统架构设计

**版本**：v1.3-r1
**最后更新**：2026-06-17
**产品阶段**：MVP
**架构目标**：支持公网部署前置安全模型、Gmail 状态同步、多邮箱扩展、Daily Digest 版本化、AI 调用可追踪、用户行为闭环。

---

## 1. 架构目标

当前系统架构围绕 MVP 设计，优先满足以下目标：

1. **系统登录与用户隔离**
   MVP 阶段即支持系统登录，所有邮箱、邮件、日报、AI 调用、用户行为均归属于具体用户。未来部署公网服务器时，必须保证用户只能访问自己的数据。

2. **Gmail 接入稳定可靠**
   MVP 支持 Gmail OAuth 授权、Token 刷新、当日邮件同步，并支持已读/未读状态真实同步至 Gmail。

3. **Daily Digest 是系统主入口**
   产品首页不是传统收件箱列表，而是今日 AI 邮件决策看板。用户优先查看“必须处理、建议查看、可忽略、待办事项、风险提醒”。

4. **AI 输出可执行、可解析、可追踪**
   AI 输出必须为结构化 JSON，包含明确的行动建议。每次 AI 调用需要记录到 `ai_runs`，便于调试、评估与回溯。

5. **Digest 版本化，避免刷新失败破坏旧日报**
   每次生成或刷新 Daily Digest 均创建新版本。新版本生成成功后才切换为当前版本；失败时保留旧版本。

6. **用户行为闭环**
   AI 建议与用户实际行为分离。系统通过 `user_actions` 记录用户对邮件、看板条目和 Gmail 状态同步的实际操作。

7. **数据安全可控**
   Token 与未来 IMAP 凭据必须加密存储。邮件正文、Token、完整 Prompt、AI API Key 不得进入日志。

8. **后续可扩展**
   虽然 MVP 仅支持 Gmail，但表结构和 Provider Adapter 需要支持未来扩展 Outlook、IMAP、多邮箱统一收件箱和桌面客户端。

---

## 2. 总体架构

系统采用：

> 前后端分离 + 系统登录 + Provider Adapter + 异步任务 + AI Pipeline + 版本化 Daily Digest + 用户行为审计

整体结构如下：

```text
┌──────────────────────────────────────────┐
│              Frontend Web                │
│         Next.js + TypeScript             │
│                                          │
│  登录 / 今日 AI 看板 / 邮件详情 / 设置    │
└───────────────────┬──────────────────────┘
                    │ HTTP API
                    ▼
┌──────────────────────────────────────────┐
│              Backend API                 │
│               FastAPI                    │
│                                          │
│ Auth / Mailbox / Digest / Email / Jobs   │
└──────────┬───────────────┬───────────────┘
           │               │
           ▼               ▼
┌──────────────────┐ ┌────────────────────┐
│ Identity Layer   │ │ Core Services       │
│ Users/Sessions   │ │ Digest/Email/Action │
└──────────┬───────┘ └──────────┬─────────┘
           │                    │
           ▼                    ▼
┌──────────────────┐ ┌────────────────────┐
│ Provider Adapter │ │ AI Pipeline         │
│ Gmail/Outlook/...│ │ LLM/Parser/Decision │
└──────────┬───────┘ └──────────┬─────────┘
           │                    │
           └──────────┬─────────┘
                      ▼
┌──────────────────────────────────────────┐
│           Async Task System              │
│             Celery + Redis               │
│                                          │
│ sync_today_emails / generate_digest      │
│ refresh_digest / check_new_emails        │
│ refresh_token                            │
└───────────────────┬──────────────────────┘
                    ▼
┌──────────────────────────────────────────┐
│              Storage Layer               │
│          PostgreSQL + Redis              │
│                                          │
│ users / sessions / mailboxes             │
│ mailbox_credentials / emails             │
│ daily_digests / digest_items             │
│ user_actions / ai_runs / sync_jobs       │
└──────────────────────────────────────────┘
```

---

## 3. 核心设计原则

### 3.1 Dashboard-first

前端首页不以收件箱为主入口，而以 Daily Digest 看板为主入口。

用户打开系统后，首先看到的是：

1. 日报时效状态；
2. 今日邮件概览；
3. 必须处理；
4. 建议查看；
5. 可忽略；
6. 今日待办；
7. 风险提醒。

邮件列表和邮件详情是支撑页面，不是产品主入口。

MVP 仍必须提供以下辅助视图，保证产品需求闭环：

1. `/emails` 今日邮件列表视图；
2. `/emails/new` 日报后新邮件视图；
3. AI 生成失败时可回退到原始邮件列表视图，而不是空白页。

---

### 3.2 系统登录与邮箱授权分离

系统中存在两种身份：

#### 系统用户身份

表示谁登录 AI Email Copilot。

用于控制：

* 登录；
* 会话；
* 数据访问权限；
* 用户自己的邮箱连接；
* 用户自己的日报和操作记录。

#### 邮箱授权身份

表示用户连接的外部邮箱账号。

例如：

* Gmail；
* Outlook；
* IMAP 邮箱。

一个系统用户未来可以绑定多个邮箱。

因此：

> 用户登录系统 ≠ 用户授权 Gmail。

即使未来支持 Google 登录系统，也不能等同于 Gmail 邮件读取授权。

---

### 3.3 Provider Adapter

MVP 只实现 Gmail，但从第一天起抽象邮箱 Provider。

```python
class EmailProvider:
    def list_messages_for_window(self, mailbox, window_start, window_end) -> list[EmailMessage]: ...
    def get_message_detail(self, mailbox, message_id: str) -> EmailMessage: ...
    def get_new_messages_after(self, mailbox, timestamp) -> list[EmailMessage]: ...
    def mark_as_read(self, mailbox, message_id: str) -> bool: ...
    def mark_as_unread(self, mailbox, message_id: str) -> bool: ...
```

Provider Adapter 契约补充：

1. Provider 返回的时间统一转换为 UTC `TIMESTAMPTZ` 再入库；
2. 当日窗口由业务层根据 `users.timezone` 计算，Provider 只接收 `window_start/window_end`；
3. Provider 侧错误必须映射为稳定错误类型，例如认证失败、限流、临时网络失败、不可重试失败；
4. `mark_as_read/mark_as_unread` 只有在 Provider 成功后，业务层才可提交本地状态变更。

Provider 实现规划：

| Provider          | 状态     | 说明                    |
| ----------------- | ------ | --------------------- |
| `GmailProvider`   | MVP 实现 | Gmail API + OAuth 2.0 |
| `OutlookProvider` | 后续版本   | Microsoft Graph API   |
| `IMAPProvider`    | 后续版本   | 通用 IMAP 协议            |

---

### 3.4 AI 建议与用户行为分离

系统中有三类状态：

| 类型      | 表示什么                   | 存储位置           |
| ------- | ---------------------- | -------------- |
| 邮箱真实状态  | Gmail 中邮件是否已读、Labels 等 | `emails`       |
| AI 建议状态 | AI 认为这封邮件或事项应如何处理      | `digest_items` |
| 用户行为状态  | 用户实际做了什么               | `user_actions` |

三者不能混用。

例如：

* Gmail 已读，不代表用户已经在 AI 看板中处理；
* AI 建议 `reply_today`，不代表用户真的回复；
* 用户点击“忽略”，不一定要修改 Gmail 状态。

---

### 3.5 Daily Digest 版本化

Daily Digest 是核心业务对象，因此刷新日报时不直接覆盖旧日报。

规则：

1. 每次生成或刷新日报均创建新版本；
2. 新版本生成成功后才成为当前版本；
3. 新版本失败时，旧版本继续作为当前日报展示；
4. 首页只展示 `is_current = true` 的 Daily Digest；
5. 失败版本保留，便于排查问题。

---

### 3.6 AI Provider Configuration Layer

MVP 通过 `.env` 配置单一 AI Provider，`LLMClient` 接口已抽象 provider 差异。

V1 演进方向（详见 PRD §13）：

```text
AI Pipeline (业务层)
        ↓
AI Routing Service（选择使用哪个模型）
        ↓
AI Model Profile（model_name + 参数）
        ↓
AI Provider Config（API Key、base_url、加密存储）
        ↓
LLM Provider Adapter（AnthropicClient / OpenAIClient / ...）
```

V1 核心原则：

1. API Key 必须加密存储（复用 `APP_ENCRYPTION_KEY` + `encryption_key_version`）；
2. 自定义 `base_url` 必须通过 SSRF 防护校验；
3. Codex / Claude Code 等 Coding Agent 不得作为 LLM Provider 类型，须在 V2 单独管理；
4. `ai_runs` 增加 `ai_provider_config_id` 外键追踪每次 AI 调用使用的 provider。

---

## 4. 专题文档索引

系统总体设计只保留架构目标、模块关系、核心原则和关键决策。具体字段、接口、任务、部署和安全细节分别维护在下列专题文档中：

| 主题 | 文档 | 内容边界 |
|---|---|---|
| 前端设计 | [`../frontend/FRONTEND_DESIGN.md`](../frontend/FRONTEND_DESIGN.md) | 页面结构、Dashboard 区域、前端状态原则 |
| API 设计 | [`../api/API_DESIGN.md`](../api/API_DESIGN.md) | Auth / Gmail OAuth / Digest / Email / Mailbox / Job / User Action API |
| Gmail 权限与安全 | [`../security/SECURITY.md`](../security/SECURITY.md) | Gmail OAuth scope、Token 加密、日志规范、AI 调用安全 |
| 核心数据流 | [`DATA_FLOWS.md`](DATA_FLOWS.md) | 注册登录、Gmail 授权、同步、生成日报、刷新日报等流程 |
| 数据库设计 | [`../database/DATABASE_DESIGN.md`](../database/DATABASE_DESIGN.md) | 表结构、字段、枚举、约束、索引、迁移策略 |
| AI Pipeline | [`../ai/AI_PIPELINE.md`](../ai/AI_PIPELINE.md) | Prompt、JSON Schema、解析、置信度、失败重试、token 控制 |
| 异步任务 | [`../engineering/ASYNC_TASKS.md`](../engineering/ASYNC_TASKS.md) | Celery 任务类型、并发规则、任务交互模式、定时任务配置 |
| 增量同步 | [`../engineering/INCREMENTAL_SYNC.md`](../engineering/INCREMENTAL_SYNC.md) | 新邮件检测、轻量快照检查、后续 Gmail Push 增强 |
| 时区规则 | [`../engineering/TIMEZONE_RULES.md`](../engineering/TIMEZONE_RULES.md) | UTC 存储 + `users.timezone` 计算业务窗口 |
| 开发与部署 | [`../engineering/DEVELOPMENT.md`](../engineering/DEVELOPMENT.md) | 服务组成、推荐开发部署方式、目录结构、docker-compose 示意 |
| AI Provider 配置 | PRD §13 | MVP `.env` → V1 用户可配置 Provider → V2 Model Profile / Agent |

## 5. 文档维护规则

1. `SYSTEM_DESIGN.md` 只维护系统级目标、原则、模块关系和架构决策。
2. 数据库字段、索引、约束只维护在 `DATABASE_DESIGN.md`。
3. API 请求参数、响应结构、错误码和鉴权规则只维护在 `API_DESIGN.md`。
4. AI Prompt、输出 Schema、解析和重试策略只维护在 `AI_PIPELINE.md`。
5. 安全、OAuth、Token、日志、密钥和公网部署风险只维护在 `SECURITY.md`。
6. 如果某个设计同时影响多个专题，`SYSTEM_DESIGN.md` 只保留原则和链接，细节放到对应专题文档。

## 6. MVP 最小闭环

MVP 第一版需要跑通以下完整链路：

```text
用户注册 / 登录
        ↓
连接 Gmail
        ↓
授权 gmail.readonly + gmail.modify
        ↓
Token 加密存储
        ↓
同步今日邮件
        ↓
生成 Daily Digest v1
        ↓
首页展示 AI 决策看板
        ↓
检测新邮件并提示
        ↓
用户刷新日报
        ↓
生成 Daily Digest v2
        ↓
v2 成功后成为当前版本
        ↓
用户点击邮件详情
        ↓
用户标记已读 / 未读
        ↓
同步 Gmail 状态
        ↓
记录 user_actions
```

---

## 7. 架构决策总结

| 决策点       | 方案                                                 | 原因                  |
| --------- | -------------------------------------------------- | ------------------- |
| 产品入口      | Daily Digest 看板优先                                  | 符合 AI 决策产品定位        |
| 用户身份      | MVP 即支持系统登录                                        | 为公网部署和用户数据隔离做准备     |
| 邮箱接入      | MVP 仅 Gmail                                        | 降低复杂度，验证核心价值        |
| 多邮箱扩展     | Provider Adapter + mailboxes + mailbox_credentials | 支持未来 Outlook / IMAP |
| Gmail 权限  | 自用完整体验权限集：`gmail.readonly + gmail.modify`          | 支持真实已读/未读同步         |
| Digest 模型 | Daily Digest 版本化                                   | 刷新失败时保护旧日报          |
| 看板条目      | 所有展示项统一进入 `digest_items`                           | 避免 todos/risks 多处存储 |
| AI 调用记录   | 使用 `ai_runs`                                       | 原始 AI 输出和业务结果分离     |
| 用户行为      | 使用 `user_actions`                                  | 形成 AI 建议与用户采纳闭环     |
| 新邮件检测     | Redis TTL 缓存                                       | 避免频繁调用 Gmail API    |
| 定时任务      | Celery Beat + 并发控制                                 | 避免重复生成和任务打架         |
| 安全模型      | 登录鉴权、Token 加密、敏感信息不入日志                             | 支持未来公网部署            |
| 时区规则      | UTC 存储 + `users.timezone` 计算业务窗口，默认 `Asia/Shanghai`     | 避免容器化部署时区不可控      |
| AI Provider   | MVP `.env` + `LLMClient`，V1 用户可配置，V2 Model Profile / Agent | 渐进式扩展，不膨胀 MVP       |
| 部署模式      | 开发期混合部署，后续全容器化                                     | 降低早期开发复杂度           |

---

## 8. 后续文档拆分状态

原第 17 节提出的拆分已经执行。后续如果新增专题，应优先新建专题文档，并在“专题文档索引”中补充链接，避免 `SYSTEM_DESIGN.md` 重新膨胀。
