# AI Email Copilot API 设计

> 本文档由 `docs/architecture/SYSTEM_DESIGN.md` 拆分而来，作为该专题的详细设计文档。
> 系统级背景、设计目标和模块关系请先阅读 `../architecture/SYSTEM_DESIGN.md`。

本文档定义后端 API 边界、路由分组、鉴权前置条件、错误响应格式和关键交互规则。

## 通用响应约定

### 0.1 成功响应

```json
{
  "data": {},
  "meta": {}
}
```

### 0.2 错误响应

```json
{
  "error": {
    "code": "DIGEST_NOT_READY",
    "message": "今日日报尚未生成完成",
    "retryable": true,
    "details": {}
  }
}
```

错误码至少覆盖：

* `UNAUTHORIZED`
* `FORBIDDEN`
* `MAILBOX_REAUTH_REQUIRED`
* `DIGEST_NOT_READY`
* `DIGEST_GENERATION_FAILED`
* `PROVIDER_RATE_LIMITED`
* `PROVIDER_SYNC_FAILED`
* `INVALID_REQUEST`

## 后端 API 架构

后端使用 FastAPI，按业务边界拆分 Router。

### 1 Auth API

```text
/api/auth
  POST /register              用户注册
  POST /login                 用户登录
  POST /logout                退出登录
  GET  /me                    获取当前登录用户
```

---

### 2 Gmail OAuth API

```text
/api/auth/gmail
  GET  /login                 生成 Gmail OAuth 授权链接
  GET  /callback              处理 Gmail OAuth 回调
  POST /disconnect            断开 Gmail 授权并清除凭据
```

说明：

* 系统登录与 Gmail 授权分离；
* 用户必须先登录系统，才能连接 Gmail；
* Gmail OAuth 回调后创建或更新 `mailboxes` 和 `mailbox_credentials`。

---

### 3 Digest API

```text
/api/digest
  GET  /today                 获取当前用户今日日报
  POST /today/generate        手动触发生成今日日报
  POST /today/refresh         刷新日报
  GET  /{digest_id}           获取指定日报详情
```

说明：

* `GET /today` 只返回当前版本日报；
* `POST /today/refresh` 创建新版本 Digest；
* 新版本生成失败时，旧版本仍作为当前日报。

---

### 4 Email API

```text
/api/emails
  GET  /today                 获取今日邮件列表
  GET  /new                   获取当前 Digest 之后的新邮件列表
  GET  /{email_id}            获取邮件详情
  POST /{email_id}/mark-read  标记为已读，同步至 Gmail
  POST /{email_id}/mark-unread 标记为未读，同步至 Gmail
```

标记已读/未读前必须校验：

1. 当前用户拥有该邮件所属 mailbox；
2. `mailboxes.permission_mode = write_enabled`；
3. `granted_scopes` 包含 `gmail.modify`；
4. Gmail API 操作成功后再更新本地 `emails.is_read`。

`GET /api/emails/today` 查询参数：

```text
sort=received_at_desc
is_read=true|false
priority=high|medium|low
source=current_digest|all
```

规则：

1. `priority` 筛选仅在 `source=current_digest` 时有效；
2. `source=current_digest` 表示以当前 `is_current = true` 的 Digest 为准，将 `digest_items(item_type='email')` 与 `emails` 关联；
3. `source=all` 表示只看邮件事实源，不附带 AI 优先级筛选；
4. `GET /api/emails/new` 返回 `coverage_end` 之后的新邮件列表。

---

### 5 Mailbox API

```text
/api/mailboxes
  GET  /                         获取当前用户已连接邮箱
  GET  /{mailbox_id}             获取邮箱详情
  GET  /{mailbox_id}/sync-status 获取同步状态
  POST /{mailbox_id}/sync        手动同步今日邮件
```

---

### 6 Job API

```text
/api/jobs
  GET /{job_id}                  查询异步任务状态
```

轮询规则：

1. 前 30 秒每 2 秒轮询一次；
2. 30 秒后退避为每 5 秒一次；
3. 单次前端轮询最长 5 分钟；
4. 超时后前端提示用户刷新页面或稍后查看。

---

### 7 User Action API

```text
/api/actions
  POST /                         创建用户行为记录
  GET  /digest-items/{id}        获取某条 Digest Item 的用户行为
```

典型行为包括：

* 打开邮件详情；
* 打开 Gmail 原始邮件；
* 标记已读；
* 标记未读；
* 忽略；
* 稍后处理；
* 标记完成。

---

### 8 Users API

```text
/api/users
  GET  /me                      获取当前用户配置
  PATCH /me                     更新当前用户配置
  PATCH /me/password            修改系统登录密码
```

补充规则：

1. `PATCH /me` 支持更新 `users.timezone`（IANA 格式）、显示偏好等；
2. 更新时区后，Digest 的日期窗口计算必须即时生效；
3. 密码修改需要当前密码验证。

---

### 9 AI Provider API（V1 预留）

> 本节为 V1 阶段预留设计。MVP 阶段不实现这些 API，AI Provider 仅通过 `.env` 配置。

```text
/api/settings/ai-providers
  GET    /                        获取当前用户的 AI Provider 列表（返回 masked key）
  POST   /                        添加 AI Provider
  GET    /{provider_config_id}    获取单个 Provider 详情
  PATCH  /{provider_config_id}    更新 Provider（API Key 为写-only）
  DELETE /{provider_config_id}    删除 Provider
  POST   /{provider_config_id}/test  测试 API Key 连接性

/api/settings/ai-routing          （V2 预留）
  GET    /                        获取各任务的 model 路由配置
  PATCH  /{task_type}             更新某任务的默认 model
```

安全规则：

1. 所有路由必须按 `user_id` 从 JWT/session 上下文过滤，禁止越权访问；
2. 不存在的或属于其他用户的 resource 统一返回 `404`（防止枚举攻击）；
3. `GET /` / `GET /{id}` 返回 masked key（`前7字符 + **** + 后4字符`），**不得**包含 `api_key_encrypted`；
4. `POST /{id}/test` 必须限流（每用户每分钟最多 5 次），仅返回 `success: boolean`；
5. 自定义 `base_url` 必须通过 SSRF 防护校验（禁止内网 IP / metadata 地址 / 强制 HTTPS）；
6. `DELETE` 使用 `ON DELETE SET NULL` 保护 `ai_runs` 审计历史。

错误码补充：

| 错误码 | HTTP | 说明 |
|--------|------|------|
| `PROVIDER_CONFIG_NOT_FOUND` | 404 | Provider 不存在或无权访问 |
| `INVALID_BASE_URL` | 400 | base_url 未通过 SSRF 防护校验 |
| `PROVIDER_TEST_FAILED` | 400 | API Key 测试连接失败 |
| `PROVIDER_TEST_RATE_LIMITED` | 429 | 测试端点调用频率超限 |
