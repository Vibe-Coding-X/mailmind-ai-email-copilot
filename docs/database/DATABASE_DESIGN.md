# AI Email Copilot 数据库设计

**版本**：v1.3-r1
**最后更新**：2026-06-17
**适用阶段**：MVP
**文档角色**：PostgreSQL 持久化层唯一详细设计来源

> 系统级背景、模块关系和专题边界请先阅读 `../architecture/SYSTEM_DESIGN.md`。
> 本文档是数据库层单一事实源。表结构、字段、枚举、约束、索引、迁移和一致性规则只在这里维护。

---

## 1. 设计目标

本版数据库设计直接服务于以下实现目标：

1. 支撑以 **Daily Digest Dashboard** 为主入口的产品体验。
2. 支撑 AI 结构化 JSON 输出的解析、落库、追踪与回放。
3. 支撑 Gmail 已读 / 未读真实同步，并为 Outlook / IMAP 预留扩展位。
4. 明确区分“邮箱真实状态”“AI 建议”“用户实际操作”，避免状态混用。
5. 支撑 Digest 版本化，保证刷新失败时旧版本仍可用。
6. 保持模型收敛，避免新增重复实体，例如独立的 `ai_actions`、`todos`、`risks` 表。

---

## 2. 单一事实源原则

数据库设计遵循以下归属规则：

| 业务事实 | 唯一存储位置 | 说明 |
|---|---|---|
| 系统用户身份 | `users` / `auth_accounts` / `sessions` | 与 Gmail 授权分离 |
| 外部邮箱连接与权限 | `mailboxes` / `mailbox_credentials` | Provider 抽象统一放这里 |
| 邮箱中的真实邮件状态 | `emails` | `is_read` 表示 Provider 当前真实状态 |
| Digest 版本与概览 | `daily_digests` | 一天可有多个版本，仅一个当前版本 |
| Digest 看板条目 | `digest_items` | 所有“必须处理 / 建议查看 / 可忽略 / 待办 / 风险”统一建模 |
| AI 原始输出与运行追踪 | `ai_runs` | 原始结构化 JSON、模型信息、失败原因只在这里追踪 |
| 用户真实操作 | `user_actions` | AI 建议不等于用户已执行 |
| 异步任务执行过程 | `sync_jobs` | Celery 任务与状态跟踪 |

明确禁止的重复建模：

1. 不新增 `ai_actions` 表，AI 建议统一体现在 `digest_items.suggested_action`。
2. 不新增 `todos` / `risks` 独立表，统一使用 `digest_items.item_type`。
3. 不在 `daily_digests` 中重复存 `todos_json`、`risks_json`、`items_json`。
4. 不在 `emails` 中重复存 AI 结论字段，例如 `ai_priority`、`ai_summary`；这些属于某个 Digest 版本，应落在 `digest_items`。

---

## 3. PostgreSQL 约定

### 3.1 类型约定

1. 所有时间字段使用 `TIMESTAMPTZ`。
2. 业务上的“日报日期”使用 `DATE`，表示用户本地时区下的自然日。
3. 主键统一使用 `UUID`。
4. 枚举字段 MVP 阶段优先使用 `VARCHAR/TEXT + CHECK`，不优先使用 PostgreSQL 原生 `ENUM`，以降低后续演进成本。
5. 规则明确但结构可能变化的字段使用 `JSONB`。
6. 简单字符串列表优先使用 `TEXT[]`，例如 `granted_scopes`、`provider_labels`。

### 3.2 命名约定

1. 表名使用复数小写下划线风格。
2. 外部 Provider 原始主键统一命名为 `external_id` / `external_thread_id` / `provider_account_id`。
3. 所有状态字段命名为 `status` 或带业务前缀的状态名，不混用布尔字段表达复杂状态。
4. 所有审计时间统一命名为 `created_at`、`updated_at`，任务执行时间统一使用 `started_at`、`finished_at`。

### 3.3 删除策略

1. `users` 删除时，相关数据允许级联删除。
2. `mailboxes` 默认建议软删除或断连：`status = 'disconnected'`，同时清空凭据。
3. 如果用户明确执行“清除本地数据”，可对 `mailboxes` 执行物理删除并级联删除其 `emails`、`daily_digests`、`digest_items`、`ai_runs`、`user_actions`、`sync_jobs`。

---

## 4. 核心表关系

```text
users
  ├── auth_accounts
  ├── sessions
  └── mailboxes
        ├── mailbox_credentials
        ├── emails
        ├── daily_digests
        │     └── digest_items
        ├── ai_runs
        ├── user_actions
        └── sync_jobs
```

---

## 5. 枚举定义

以下为数据库层标准可选值。实现时应使用 `CHECK` 约束保证取值一致。

### 5.1 通用 Provider 枚举

```text
gmail
outlook
imap
```

### 5.2 `users.status`

```text
active
disabled
```

### 5.3 `mailboxes.permission_mode`

```text
readonly
write_enabled
```

### 5.4 `mailboxes.status`

```text
active
reauth_required
disconnected
error
```

### 5.5 `mailbox_credentials.credential_type`

```text
oauth2
imap_password
```

### 5.6 `daily_digests.status`

```text
generating
fresh
stale
refreshing
failed
```

说明：

1. `generating`：新版本 Digest 已创建，正在生成。
2. `fresh`：当前版本成功且无未纳入分析的新邮件。
3. `stale`：当前版本成功，但 `coverage_end` 后已发现新邮件。
4. `refreshing`：当前版本仍被展示，但系统正在生成更新版本。
5. `failed`：该版本生成失败。

### 5.7 `digest_items.item_type`

```text
email
todo
risk
```

### 5.8 `digest_items.section`

```text
urgent
review
ignore
todo
risk
```

### 5.9 `digest_items.category`

```text
work
notification
marketing
social
other
```

### 5.10 `digest_items.suggested_action`

```text
reply_today
review_today
handle_before_deadline
ignore
archive_candidate
follow_up_later
no_action_required
```

### 5.11 `digest_items.priority`

```text
high
medium
low
```

### 5.12 `ai_runs.run_type`

```text
daily_digest
single_email
new_mail_preview
```

### 5.13 `ai_runs.status`

```text
queued
running
succeeded
failed
cancelled
```

### 5.14 `sync_jobs.job_type`

```text
sync_today_emails
generate_daily_digest
refresh_daily_digest
check_new_emails_after_digest
refresh_access_token
```

### 5.15 `sync_jobs.status`

```text
queued
running
succeeded
failed
cancelled
```

### 5.16 `user_actions.action_status`

```text
pending
executed
failed
cancelled
```

### 5.17 `user_actions.source`

```text
dashboard
email_detail
settings
system
```

### 5.18 `user_actions.provider_effect`

```text
none
local_only
gmail_synced
outlook_synced
imap_synced
```

### 5.19 触发来源枚举

以下字段共用：`daily_digests.trigger_source`、`ai_runs.trigger_source`、`sync_jobs.trigger_source`。

```text
manual
scheduled
refresh
initial_sync
oauth_callback
system
detail_view
```

---

## 6. 表结构详细设计

### 6.1 `users`

系统用户表。系统登录身份与邮箱授权身份必须分离。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 用户主键 |
| `email` | `VARCHAR(255)` | NOT NULL | 系统登录邮箱，入库前需标准化为小写 |
| `display_name` | `VARCHAR(100)` | NULL | 展示名 |
| `password_hash` | `TEXT` | NULL | 密码登录哈希，若仅第三方登录可为空 |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK | `active` / `disabled` |
| `timezone` | `VARCHAR(64)` | NOT NULL | IANA 时区，MVP 默认 `Asia/Shanghai` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 更新时间 |

约束与索引：

1. `UNIQUE (email)`，前提是应用层已做小写标准化；若不依赖应用层，推荐改为 `CITEXT` 或 `UNIQUE INDEX ON LOWER(email)`。
2. 索引：`INDEX users_status_idx (status)`。

---

### 6.2 `auth_accounts`

系统登录方式表，不代表 Gmail 邮件读取授权。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户 |
| `provider` | `VARCHAR(30)` | NOT NULL | 例如 `password`、`google` |
| `provider_user_id` | `VARCHAR(255)` | NOT NULL | 第三方身份唯一标识 |
| `provider_email` | `VARCHAR(255)` | NULL | 第三方返回邮箱 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |

约束与索引：

1. `UNIQUE (provider, provider_user_id)`。
2. 索引：`INDEX auth_accounts_user_id_idx (user_id)`。

---

### 6.3 `sessions`

登录会话表。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户 |
| `session_token_hash` | `TEXT` | NOT NULL | Session Token 哈希值 |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL | 过期时间 |
| `last_used_at` | `TIMESTAMPTZ` | NULL | 最近使用时间 |
| `ip_address` | `INET` | NULL | 登录 IP |
| `user_agent` | `TEXT` | NULL | 客户端 UA |
| `revoked_at` | `TIMESTAMPTZ` | NULL | 主动失效时间 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |

约束与索引：

1. `UNIQUE (session_token_hash)`。
2. 索引：`INDEX sessions_user_id_idx (user_id)`。
3. 索引：`INDEX sessions_active_idx (user_id, expires_at)`，用于查询有效会话。

---

### 6.4 `mailboxes`

外部邮箱连接主体表。MVP 虽然只实现 Gmail，但此表必须自带多 Provider 扩展能力。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户 |
| `provider` | `VARCHAR(20)` | NOT NULL, CHECK | `gmail` / `outlook` / `imap` |
| `provider_account_id` | `VARCHAR(255)` | NOT NULL | Provider 侧稳定账号标识；Gmail 可存 Google `sub` 或 profile id |
| `email_address` | `VARCHAR(255)` | NOT NULL | 邮箱地址，标准化为小写 |
| `display_name` | `VARCHAR(255)` | NULL | 邮箱展示名 |
| `permission_mode` | `VARCHAR(20)` | NOT NULL DEFAULT `'write_enabled'`, CHECK | `readonly` / `write_enabled` |
| `granted_scopes` | `TEXT[]` | NOT NULL DEFAULT `'{}'` | 已授予 Scope 列表 |
| `status` | `VARCHAR(20)` | NOT NULL DEFAULT `'active'`, CHECK | 邮箱连接状态 |
| `last_sync_at` | `TIMESTAMPTZ` | NULL | 最近一次同步尝试时间 |
| `last_successful_sync_at` | `TIMESTAMPTZ` | NULL | 最近一次成功同步时间 |
| `last_history_id` | `VARCHAR(128)` | NULL | Gmail History API 游标预留 |
| `sync_cursor` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | 未来 Outlook / IMAP 游标预留 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 更新时间 |

约束与索引：

1. `UNIQUE (user_id, provider, provider_account_id)`。
2. `UNIQUE (user_id, provider, email_address)`。
3. `CHECK (jsonb_typeof(sync_cursor) = 'object')`。
4. 索引：`INDEX mailboxes_user_status_idx (user_id, status)`。
5. GIN 索引可选：`mailboxes_granted_scopes_gin_idx`，仅在存在按 Scope 查询需求时添加。

实现说明：

1. `permission_mode` 决定是否允许真实写回 Provider 已读 / 未读状态。
2. `status = 'reauth_required'` 表示 Refresh Token 失效或 Scope 不足，需要重新授权。

---

### 6.5 `mailbox_credentials`

邮箱凭据表。敏感信息必须与 `mailboxes` 拆分。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `mailbox_id` | `UUID` | PK, FK -> `mailboxes(id)` | 一对一主键 |
| `credential_type` | `VARCHAR(20)` | NOT NULL, CHECK | `oauth2` / `imap_password` |
| `refresh_token_encrypted` | `TEXT` | NULL | OAuth Refresh Token，加密存储 |
| `imap_password_encrypted` | `TEXT` | NULL | IMAP 密码或应用专用密码，加密存储 |
| `scopes_snapshot` | `TEXT[]` | NOT NULL DEFAULT `'{}'` | 授权时的 Scope 快照 |
| `credentials_json` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | 额外 Provider 凭据信息，例如租户、授权端点标识 |
| `encryption_key_version` | `VARCHAR(20)` | NULL | 用于标识加密密钥版本，便于未来密钥轮换 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 更新时间 |

约束与索引：

1. `CHECK (jsonb_typeof(credentials_json) = 'object')`。
2. `credential_type = 'oauth2'` 时至少应有 `refresh_token_encrypted`。
3. `credential_type = 'imap_password'` 时至少应有 `imap_password_encrypted`。

实现说明：

1. **Access Token 不作为 PostgreSQL 长久字段保存**。MVP 仍按安全文档要求，短期缓存于 Redis。
2. 凭据加密统一使用 `APP_ENCRYPTION_KEY`。

---

### 6.6 `emails`

邮件主表，承载 Provider 同步下来的真实邮件状态与清洗后正文。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户，冗余便于权限过滤 |
| `mailbox_id` | `UUID` | NOT NULL, FK -> `mailboxes(id)` | 所属邮箱 |
| `provider` | `VARCHAR(20)` | NOT NULL, CHECK | 与 `mailboxes.provider` 保持一致 |
| `external_id` | `VARCHAR(255)` | NOT NULL | Provider 消息主键；Gmail 为 message id |
| `external_thread_id` | `VARCHAR(255)` | NULL | Provider 线程 id |
| `internet_message_id` | `VARCHAR(500)` | NULL | 邮件头 `Message-ID`，用于跨 Provider 去重和排障 |
| `subject` | `TEXT` | NULL | 主题 |
| `from_name` | `VARCHAR(255)` | NULL | 发件人名称 |
| `from_address` | `VARCHAR(255)` | NULL | 发件人邮箱 |
| `to_addresses` | `JSONB` | NOT NULL DEFAULT `'[]'::jsonb` | 收件人列表 |
| `cc_addresses` | `JSONB` | NOT NULL DEFAULT `'[]'::jsonb` | 抄送列表 |
| `snippet` | `TEXT` | NULL | Provider 摘要 |
| `body_text` | `TEXT` | NULL | 清洗、去 HTML、去引用、截断后的正文文本 |
| `body_text_truncated` | `BOOLEAN` | NOT NULL DEFAULT `FALSE` | 是否已做正文截断 |
| `received_at` | `TIMESTAMPTZ` | NOT NULL | 收件时间 |
| `is_read` | `BOOLEAN` | NOT NULL DEFAULT `FALSE` | Provider 当前真实已读状态 |
| `provider_labels` | `TEXT[]` | NOT NULL DEFAULT `'{}'` | Provider 标签或分类 |
| `gmail_history_id` | `VARCHAR(128)` | NULL | Gmail 增量同步游标预留 |
| `first_synced_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 首次同步时间 |
| `last_synced_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 最近同步时间 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 更新时间 |

约束与索引：

1. `UNIQUE (mailbox_id, external_id)`。
2. `CHECK (jsonb_typeof(to_addresses) = 'array')`。
3. `CHECK (jsonb_typeof(cc_addresses) = 'array')`。
4. 索引：`INDEX emails_mailbox_received_idx (mailbox_id, received_at DESC)`。
5. 索引：`INDEX emails_user_received_idx (user_id, received_at DESC)`。
6. 索引：`INDEX emails_mailbox_thread_idx (mailbox_id, external_thread_id)`。
7. 索引：`INDEX emails_mailbox_read_received_idx (mailbox_id, is_read, received_at DESC)`。
8. GIN 索引可选：`emails_provider_labels_gin_idx`。

实现说明：

1. 不保存完整 MIME 原文，不保存附件二进制。
2. `body_text` 是为 Digest 和详情页服务的“最小必要正文”。
3. `is_read` 是邮箱真实状态，不表示用户已在 Digest 中处理。

---

### 6.7 `daily_digests`

Daily Digest 版本表。每次手动生成、定时生成、刷新生成都创建新版本，不覆盖旧版本。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户 |
| `mailbox_id` | `UUID` | NOT NULL, FK -> `mailboxes(id)` | 所属邮箱 |
| `digest_date` | `DATE` | NOT NULL | 用户本地时区下的“今日” |
| `version` | `INTEGER` | NOT NULL | 从 1 开始递增 |
| `is_current` | `BOOLEAN` | NOT NULL DEFAULT `FALSE` | 是否为该邮箱该日当前展示版本 |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK | Digest 状态 |
| `trigger_source` | `VARCHAR(20)` | NOT NULL, CHECK | 手动 / 定时 / 刷新等来源 |
| `generation_started_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 本版本开始生成时间 |
| `generated_at` | `TIMESTAMPTZ` | NULL | 本版本生成成功时间 |
| `coverage_start` | `TIMESTAMPTZ` | NOT NULL | 覆盖起点，通常为用户本地当天 00:00:00 |
| `coverage_end` | `TIMESTAMPTZ` | NOT NULL | 覆盖终点，通常为生成时刻 |
| `mail_count` | `INTEGER` | NOT NULL DEFAULT `0` | 进入分析范围的邮件数 |
| `new_mail_count_after_digest` | `INTEGER` | NOT NULL DEFAULT `0` | 生成后检测到但未纳入当前版本的邮件数 |
| `overview_json` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | Digest 概览 JSON，来源于 AI 输出 `overview` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 更新时间 |

约束与索引：

1. `UNIQUE (mailbox_id, digest_date, version)`。
2. 部分唯一索引：`UNIQUE (mailbox_id, digest_date) WHERE is_current = TRUE`。
3. `CHECK (version > 0)`。
4. `CHECK (mail_count >= 0)`。
5. `CHECK (new_mail_count_after_digest >= 0)`。
6. `CHECK (coverage_end >= coverage_start)`。
7. `CHECK (jsonb_typeof(overview_json) = 'object')`。
8. 建议状态一致性检查：
   `status IN ('fresh', 'stale', 'refreshing') -> generated_at IS NOT NULL`。
9. 索引：`INDEX daily_digests_current_lookup_idx (user_id, digest_date, is_current)`。
10. 索引：`INDEX daily_digests_mailbox_date_idx (mailbox_id, digest_date DESC, version DESC)`。

实现说明：

1. 首页默认只读 `is_current = TRUE` 的版本。
2. 刷新时先创建新版本 `generating`，成功后再切换 `is_current`。
3. 若新版本失败，旧版本继续保留为当前版本。

---

### 6.8 `digest_items`

Digest 看板条目表。所有首页看板项统一进入此表，不再拆 `todos`、`risks`、`actions` 等重复模型。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `digest_id` | `UUID` | NOT NULL, FK -> `daily_digests(id)` | 所属 Digest 版本 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户 |
| `mailbox_id` | `UUID` | NOT NULL, FK -> `mailboxes(id)` | 所属邮箱 |
| `email_id` | `UUID` | NULL, FK -> `emails(id)` | 关联邮件；`item_type = 'email'` 时必须存在 |
| `item_type` | `VARCHAR(20)` | NOT NULL, CHECK | `email` / `todo` / `risk` |
| `section` | `VARCHAR(20)` | NOT NULL, CHECK | Dashboard 展示区域 |
| `title` | `TEXT` | NOT NULL | 卡片标题 |
| `summary` | `TEXT` | NULL | 卡片摘要 |
| `category` | `VARCHAR(30)` | NULL, CHECK | 邮件类型，仅邮件类常用 |
| `suggested_action` | `VARCHAR(50)` | NULL, CHECK | AI 建议动作 |
| `priority` | `VARCHAR(10)` | NOT NULL, CHECK | 高 / 中 / 低 |
| `reason` | `TEXT` | NULL | 给出建议的原因 |
| `deadline` | `DATE` | NULL | 截止日期 |
| `confidence` | `NUMERIC(4,3)` | NOT NULL | 0.000 - 1.000 |
| `display_order` | `INTEGER` | NOT NULL DEFAULT `0` | 同一分区内排序 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 更新时间 |

约束与索引：

1. `CHECK (confidence >= 0 AND confidence <= 1)`。
2. `CHECK (display_order >= 0)`。
3. 约束：`item_type = 'email' -> email_id IS NOT NULL`。
4. 约束：`section = 'todo' -> item_type = 'todo'`。
5. 约束：`section = 'risk' -> item_type = 'risk'`。
6. 约束：`section IN ('urgent', 'review', 'ignore') -> item_type = 'email'`。
7. 部分唯一索引：`UNIQUE (digest_id, email_id) WHERE item_type = 'email'`，避免同一 Digest 中同一邮件生成多个主卡片。
8. 索引：`INDEX digest_items_digest_section_order_idx (digest_id, section, display_order)`。
9. 索引：`INDEX digest_items_digest_priority_idx (digest_id, priority, display_order)`。
10. 索引：`INDEX digest_items_email_id_idx (email_id)`。

实现说明：

1. 邮件类条目直接驱动“必须处理 / 建议查看 / 可忽略”区域。
2. `todo` 与 `risk` 条目不另建表，直接驱动“今日待办 / 风险提醒”区域。
3. 低置信度条目可在业务层被强制降级到 `section = 'review'`。

---

### 6.9 `ai_runs`

AI 调用追踪表。原始 AI 输出、模型元数据、失败原因和 token 消耗统一在这里记录。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户 |
| `mailbox_id` | `UUID` | NOT NULL, FK -> `mailboxes(id)` | 所属邮箱 |
| `digest_id` | `UUID` | NULL, FK -> `daily_digests(id)` | 如为日报生成，则关联对应 Digest 版本 |
| `run_type` | `VARCHAR(30)` | NOT NULL, CHECK | `daily_digest` / `single_email` / `new_mail_preview` |
| `trigger_source` | `VARCHAR(20)` | NOT NULL, CHECK | 调用来源 |
| `model_provider` | `VARCHAR(50)` | NOT NULL | 如 `openai`、`anthropic` |
| `model_name` | `VARCHAR(100)` | NOT NULL | 模型名 |
| `prompt_version` | `VARCHAR(50)` | NOT NULL | Prompt 版本 |
| `output_schema_version` | `VARCHAR(50)` | NOT NULL | 输出 Schema 版本，例如 `digest.v1` |
| `input_hash` | `CHAR(64)` | NOT NULL | 输入摘要哈希，不存完整 Prompt |
| `input_summary_json` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | 输入统计摘要，例如邮件数、截断数 |
| `output_json` | `JSONB` | NULL | 原始结构化输出 |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK | 运行状态 |
| `error_code` | `VARCHAR(100)` | NULL | 错误码 |
| `error_message` | `TEXT` | NULL | 错误信息 |
| `prompt_tokens` | `INTEGER` | NULL | Prompt Token 用量 |
| `completion_tokens` | `INTEGER` | NULL | Completion Token 用量 |
| `total_tokens` | `INTEGER` | NULL | 总 Token 用量 |
| `latency_ms` | `INTEGER` | NULL | 耗时 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `started_at` | `TIMESTAMPTZ` | NULL | 开始执行时间 |
| `finished_at` | `TIMESTAMPTZ` | NULL | 完成时间 |

约束与索引：

1. `CHECK (jsonb_typeof(input_summary_json) = 'object')`。
2. `CHECK (prompt_tokens IS NULL OR prompt_tokens >= 0)`。
3. `CHECK (completion_tokens IS NULL OR completion_tokens >= 0)`。
4. `CHECK (total_tokens IS NULL OR total_tokens >= 0)`。
5. `CHECK (latency_ms IS NULL OR latency_ms >= 0)`。
6. 建议状态一致性检查：`status = 'succeeded' -> output_json IS NOT NULL AND finished_at IS NOT NULL`。
7. 索引：`INDEX ai_runs_digest_created_idx (digest_id, created_at DESC)`。
8. 索引：`INDEX ai_runs_mailbox_created_idx (mailbox_id, created_at DESC)`。
9. 索引：`INDEX ai_runs_status_created_idx (status, created_at DESC)`。

实现说明：

1. `digest_items` 是 AI 输出的业务化落地，`ai_runs.output_json` 是原始结构化结果。
2. 自用阶段允许保留 `output_json`；后续商业化可按合规要求收紧。
3. 不记录完整 Prompt 和邮件正文。

---

### 6.10 `user_actions`

用户行为记录表，用于审计、回放、统计 AI 建议采纳率，以及记录 Gmail 已读 / 未读同步结果。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 操作者 |
| `mailbox_id` | `UUID` | NOT NULL, FK -> `mailboxes(id)` | 所属邮箱 |
| `digest_id` | `UUID` | NULL, FK -> `daily_digests(id)` | 所在 Digest 上下文 |
| `digest_item_id` | `UUID` | NULL, FK -> `digest_items(id)` | 所操作的看板条目 |
| `email_id` | `UUID` | NULL, FK -> `emails(id)` | 所操作邮件 |
| `action_type` | `VARCHAR(50)` | NOT NULL | 用户行为类型 |
| `action_status` | `VARCHAR(20)` | NOT NULL, CHECK | 执行状态 |
| `source` | `VARCHAR(30)` | NOT NULL, CHECK | 操作入口 |
| `provider_effect` | `VARCHAR(30)` | NOT NULL DEFAULT `'none'`, CHECK | 是否同步到 Provider |
| `before_state` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | 操作前状态快照 |
| `after_state` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | 操作后状态快照 |
| `error_code` | `VARCHAR(100)` | NULL | 错误码 |
| `error_message` | `TEXT` | NULL | 错误信息 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `executed_at` | `TIMESTAMPTZ` | NULL | 完成时间 |

标准 `action_type`：

```text
open_email_detail
open_provider_message
mark_read
mark_unread
dismiss_item
snooze_item
mark_done
generate_digest
refresh_digest
disconnect_mailbox
```

约束与索引：

1. `CHECK (jsonb_typeof(before_state) = 'object')`。
2. `CHECK (jsonb_typeof(after_state) = 'object')`。
3. 索引：`INDEX user_actions_user_created_idx (user_id, created_at DESC)`。
4. 索引：`INDEX user_actions_digest_item_created_idx (digest_item_id, created_at DESC)`。
5. 索引：`INDEX user_actions_email_created_idx (email_id, created_at DESC)`。
6. 索引：`INDEX user_actions_status_created_idx (action_status, created_at DESC)`。

实现说明：

1. `mark_read` / `mark_unread` 成功时，`provider_effect` 应分别记录为 `gmail_synced`、`outlook_synced` 或 `imap_synced`。
2. 失败写回也必须保留一条 `user_actions`，`action_status = 'failed'`。
3. `dismiss_item`、`mark_done` 属于用户行为，不应反写 `digest_items` 持久状态，避免与 AI 建议混淆。

---

### 6.11 `sync_jobs`

异步任务跟踪表，对应 Celery 任务状态、去重和排障。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK -> `users(id)` | 所属用户 |
| `mailbox_id` | `UUID` | NULL, FK -> `mailboxes(id)` | 所属邮箱 |
| `digest_id` | `UUID` | NULL, FK -> `daily_digests(id)` | 关联 Digest |
| `celery_task_id` | `VARCHAR(255)` | NULL | Celery 任务 id |
| `job_type` | `VARCHAR(50)` | NOT NULL, CHECK | 任务类型 |
| `trigger_source` | `VARCHAR(20)` | NOT NULL, CHECK | 任务来源 |
| `job_key` | `VARCHAR(255)` | NULL | 幂等去重键，例如 `generate_daily_digest:{mailbox_id}:{digest_date}` |
| `target_date` | `DATE` | NULL | 目标业务日期 |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK | 任务状态 |
| `retry_count` | `INTEGER` | NOT NULL DEFAULT `0` | 重试次数 |
| `payload_json` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | 轻量任务参数 |
| `error_code` | `VARCHAR(100)` | NULL | 错误码 |
| `error_message` | `TEXT` | NULL | 错误信息 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `started_at` | `TIMESTAMPTZ` | NULL | 开始执行时间 |
| `finished_at` | `TIMESTAMPTZ` | NULL | 完成时间 |

约束与索引：

1. `CHECK (retry_count >= 0)`。
2. `CHECK (jsonb_typeof(payload_json) = 'object')`。
3. `UNIQUE (celery_task_id)`，当使用 Celery 时启用。
4. 部分唯一索引：`UNIQUE (job_key) WHERE status IN ('queued', 'running')`，用于活动任务去重。
5. 索引：`INDEX sync_jobs_mailbox_created_idx (mailbox_id, created_at DESC)`。
6. 索引：`INDEX sync_jobs_digest_created_idx (digest_id, created_at DESC)`。
7. 索引：`INDEX sync_jobs_status_created_idx (status, created_at DESC)`。
8. 索引：`INDEX sync_jobs_target_date_idx (mailbox_id, target_date, job_type)`。

实现说明：

1. 同一 `mailbox_id + target_date + generate_daily_digest` 应通过 `job_key` 保证并发去重。
2. 手动刷新优先级高于定时任务，但仍不应绕过去重机制。

---

## 7. AI JSON 到数据库的映射

AI 输出结构以 `docs/ai/AI_PIPELINE.md` 为准，数据库映射规则如下：

### 7.1 `overview` 映射

AI 输出：

```json
{
  "overview": {
    "mail_count": 24,
    "summary": "今天主要是项目协作和系统通知邮件，有 3 封需要今日处理。"
  }
}
```

落库规则：

1. `overview.mail_count` 写入 `daily_digests.mail_count`。
2. `overview` 原样业务化后写入 `daily_digests.overview_json`。

### 7.2 `items` 映射

AI 输出 `items[]` 中每个对象落一条 `digest_items`：

1. `item_type` -> `digest_items.item_type`
2. `section` -> `digest_items.section`
3. `email_id` 先通过本地 `emails.external_id` 解析，再写入 `digest_items.email_id`
4. `title` / `summary` / `category` / `suggested_action` / `priority` / `reason` / `deadline` / `confidence` 分别写入同名字段

### 7.3 原始输出保留位置

1. AI 原始结构化结果仅保留在 `ai_runs.output_json`。
2. `digest_items` 只保留解析后的业务字段，不再冗余保存整段原始 JSON。

---

## 8. 一致性规则

### 8.1 Digest 版本切换规则

Digest 版本切换属于**强一致性操作**，必须满足：

1. 生成新 Digest 时，先插入新行：`status = 'generating'`、`is_current = FALSE`；
2. 事务隔离级别至少为 `REPEATABLE READ`；
3. AI 成功后，先写入 `digest_items`，再在同一事务中：
   - 将旧当前版本 `is_current = FALSE`
   - 将新版本 `is_current = TRUE`
   - 将新版本 `status` 置为 `fresh` 或 `stale`
4. **回滚策略**：如果插入 `digest_items` 失败或任何约束冲突，整个事务必须回滚，保留旧版本 `is_current = TRUE`，不得留下半成品版本；
5. 前端读取当前版本时必须只读 `is_current = TRUE` 的行，避免读到中间状态。

### 8.2 Gmail 已读 / 未读同步规则

1. 用户点击“标记已读 / 未读”后，先调用 Provider API。
2. 只有 Provider API 成功，才更新 `emails.is_read`。
3. 成功后写入 `user_actions`，并设置 `provider_effect = 'gmail_synced'`。
4. 如果 Provider API 失败：
   - 不更新 `emails.is_read`
   - 仍写一条 `user_actions`，`action_status = 'failed'`

### 8.3 邮件、AI 建议、用户行为分离规则

1. `emails.is_read` 是邮箱真实状态。
2. `digest_items.suggested_action` 是 AI 建议，不代表用户已执行。
3. `user_actions` 才表示用户实际做了什么。
4. 不允许通过更新 `digest_items` 来冒充用户处理状态。

### 8.4 作用域一致性规则

以下关联必须在应用层和测试中强校验：

1. `digest_items.user_id`、`digest_items.mailbox_id` 必须与其 `digest_id` 指向的 `daily_digests` 保持一致。
2. `digest_items.email_id` 若非空，其 `emails.mailbox_id` 必须与 `digest_items.mailbox_id` 一致。
3. `user_actions.digest_item_id` 若非空，其 `digest_id`、`mailbox_id`、`user_id` 必须与 `user_actions` 主体一致。
4. `ai_runs.digest_id` 若非空，其 `mailbox_id`、`user_id` 必须与 `daily_digests` 一致。

### 8.5 新邮件检测规则

1. `new_mail_count_after_digest` 表示 `coverage_end` 之后已检测到的新邮件数量。
2. Redis 中的轻量缓存仅用于避免频繁调用 Gmail API，不是持久化事实源。
3. 一旦确认有新邮件，当前 Digest 应更新为 `stale` 或 `refreshing`。

---

## 9. 推荐索引总览

以下索引是 MVP 的高优先级集合：

| 表 | 索引 | 用途 |
|---|---|---|
| `users` | `UNIQUE(email)` | 登录查找 |
| `mailboxes` | `(user_id, status)` | 当前用户邮箱列表 |
| `mailboxes` | `UNIQUE(user_id, provider, provider_account_id)` | 防止重复连接同一外部邮箱 |
| `emails` | `(mailbox_id, received_at DESC)` | 今日邮件列表、Digest 输入构建 |
| `emails` | `(mailbox_id, is_read, received_at DESC)` | 已读 / 未读筛选 |
| `daily_digests` | `UNIQUE(mailbox_id, digest_date) WHERE is_current = TRUE` | 获取今日日报当前版本 |
| `daily_digests` | `(mailbox_id, digest_date DESC, version DESC)` | 版本查询 |
| `digest_items` | `(digest_id, section, display_order)` | 首页分区渲染 |
| `digest_items` | `UNIQUE(digest_id, email_id) WHERE item_type = 'email'` | 防止主卡片重复 |
| `ai_runs` | `(digest_id, created_at DESC)` | Digest 调用排障 |
| `user_actions` | `(email_id, created_at DESC)` | 邮件行为时间线 |
| `sync_jobs` | `UNIQUE(job_key) WHERE status IN ('queued', 'running')` | 异步任务去重 |

---

## 10. 迁移说明

如果当前仓库仍基于旧版 v1.2 草稿建表，升级到 v1.3 时应至少处理以下差异：

1. 所有 `TIMESTAMP` 统一迁移为 `TIMESTAMPTZ`。
2. `daily_digests.date` 统一重命名为 `digest_date`，避免与 SQL 保留语义混淆。
3. `daily_digests.overview` 文本字段迁移为 `overview_json`，旧文本可回填为 `{ "summary": "..." }`。
4. 如果旧表在 `daily_digests` 中保存了 `model_name`、`prompt_version`，应迁移到 `ai_runs` 作为 AI 元数据主存储。
5. `mailbox_credentials` 中若已有 `access_token_encrypted`，应迁移后废弃，不再长期存 PostgreSQL。
6. `mailboxes` 新增 `provider_account_id`、`last_successful_sync_at`、`sync_cursor`。
7. `digest_items` 需要补齐 `item_type + section + email_id` 的一致性约束和部分唯一索引。
8. `user_actions` 新增 `digest_id`，便于记录 `generate_digest`、`refresh_digest` 等非单 item 行为。
9. `sync_jobs` 新增 `job_key`、`target_date`、`trigger_source`，并添加活动任务部分唯一索引。

迁移顺序建议：

1. 先加新列并回填。
2. 回填完成后再加 `NOT NULL` 和 `CHECK` 约束。
3. 最后创建部分唯一索引，避免历史脏数据直接导致迁移失败。

---

## 11. PostgreSQL 实现注意事项

1. `updated_at` 建议通过应用层统一更新，或使用数据库触发器自动维护。
2. Digest 版本号分配建议在事务内执行，并结合 `SELECT ... FOR UPDATE` 或 advisory lock 锁定 `mailbox_id + digest_date`。
3. 切换 `is_current` 必须与插入 `digest_items` 放在同一事务或同一工作流最终提交阶段，避免首页读到半成品版本。
4. `JSONB` 只用于真正需要保留结构弹性的字段，不要把核心查询字段埋进 `JSONB`。
5. `TEXT[]` 比 `JSONB` 更适合存 Scope、Labels 这类简单列表。
6. 大文本 `body_text` 应在写入前完成清洗和截断，避免数据库层保存过长无用内容。
7. 对 `sync_jobs.job_key` 的并发去重，不要只依赖应用层判断，必须结合数据库唯一约束。
8. 如需进一步优化今日邮件查询，可考虑按 `received_at` 对 `emails` 做月级分区，但 MVP 不强制。

---

## 12. 最终结论

v1.3 数据库设计以 `daily_digests + digest_items + ai_runs + user_actions` 为核心闭环：

1. `emails` 保存邮箱真实状态。
2. `daily_digests` 保存版本化日报快照。
3. `digest_items` 保存 Dashboard 可渲染条目。
4. `ai_runs` 保存 AI 调用与原始 JSON 输出。
5. `user_actions` 保存用户真实行为与 Provider 同步结果。

该设计满足 MVP 当前 Gmail 场景，同时为 Outlook、IMAP、多邮箱与未来更严格的生产部署留出了清晰扩展边界。

---

## 13. V1 预留：AI Provider 配置表

> 本节为 V1 阶段预留设计。MVP 阶段**不创建**以下表，仅在文档层面定义 DDL，便于 V1 实现时直接使用。
> MVP 阶段 AI Provider 通过 `.env` 配置，`ai_runs.model_provider` / `model_name` 已满足追踪需求。

### 13.1 `ai_provider_configs`（V1 创建）

用户配置的 AI Provider 表。每条记录代表一个用户添加的 AI 服务配置。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | `UUID` | PK | 主键 |
| `user_id` | `UUID` | NOT NULL, FK → `users(id)` | 所属用户 |
| `provider` | `VARCHAR(50)` | NOT NULL, CHECK | `openai` / `anthropic` / `google` / `azure_openai` / `openrouter` / `ollama` / `custom` |
| `display_name` | `VARCHAR(100)` | NULL | 用户自定义名称 |
| `base_url` | `TEXT` | NULL | 自定义 endpoint（V1 必须通过 SSRF 防护校验） |
| `api_key_encrypted` | `TEXT` | NULL | 加密后的 API Key |
| `encryption_key_version` | `VARCHAR(20)` | NOT NULL DEFAULT `'v1'` | 密钥版本，便于未来轮换 |
| `capabilities` | `JSONB` | NOT NULL DEFAULT `'{}'::jsonb` | 支持的能力（json_mode、tool_use 等） |
| `status` | `VARCHAR(20)` | NOT NULL DEFAULT `'active'`, CHECK | `active` / `disabled` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `NOW()` | 更新时间 |

约束与索引：

1. `CHECK (jsonb_typeof(capabilities) = 'object')`；
2. `CHECK (status IN ('active', 'disabled'))`；
3. `CHECK (provider IN ('openai', 'anthropic', 'google', 'azure_openai', 'openrouter', 'ollama', 'custom'))`；
4. `UNIQUE (user_id, provider)` — 同一用户同类型 provider 仅一个；
5. 索引：`INDEX ai_provider_configs_user_status_idx (user_id, status)`。

实现说明：

1. **MVP 不创建此表**，仅作为 V1 DDL 预留；
2. API Key 加密复用 `APP_ENCRYPTION_KEY` + `encryption_key_version` 模式，与 `mailbox_credentials` 一致；
3. 自定义 `base_url` 必须通过 SSRF 防护（禁止内网 IP / metadata 地址 / 强制 HTTPS）；
4. **Codex / Claude Code 不属于此表的 provider 类型**，V2 需单独管理。

### 13.2 `ai_runs` 外键增强（V1 添加列）

V1 需要在 `ai_runs` 表增加以下外键列（`NULLABLE`，`ON DELETE SET NULL`）：

```sql
ALTER TABLE ai_runs
  ADD COLUMN ai_provider_config_id UUID NULL
    REFERENCES ai_provider_configs(id) ON DELETE SET NULL;
```

- MVP 期间这些列为 `NULL`，使用 `.env` 默认 provider；
- V1 开始记录每次 AI 调用的 provider 来源；
- 保留现有 `model_provider` / `model_name` VARCHAR 字段作为历史快照（不可变事实）。

### 13.3 V2 预留表（仅描述，不给 DDL）

以下表在 V2 阶段评估是否需要，MVP / V1 不创建：

| 表名 | 用途 | 状态 |
|------|------|------|
| `ai_model_profiles` | 用户为不同任务配置不同模型参数 | V2 评估 |
| `ai_routing_policies` | 按任务类型路由到不同 model profile | V2 评估 |
| `ai_usage_records` | AI 使用量与成本追踪（可由 `ai_runs` 聚合替代） | V2 评估 |
