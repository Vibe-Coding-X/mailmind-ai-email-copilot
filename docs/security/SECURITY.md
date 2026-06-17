# AI Email Copilot 安全设计

> 本文档由 `docs/architecture/SYSTEM_DESIGN.md` 拆分而来，作为该专题的详细设计文档。
> 系统级背景、设计目标和模块关系请先阅读 `../architecture/SYSTEM_DESIGN.md`。

本文档集中维护 Gmail OAuth 权限、Token 加密、日志脱敏、AI 调用安全和未来公网部署安全要求。

## 邮箱接入与权限设计

### 1 Gmail OAuth Scope

MVP 自用阶段采用完整体验权限集：

| Scope            | 用途               |
| ---------------- | ---------------- |
| `gmail.readonly` | 读取邮件列表、正文、元数据    |
| `gmail.modify`   | 修改 Gmail 已读/未读状态 |

说明：

* `gmail.modify` 用于真实同步 Gmail 已读/未读；
* 该权限不是“最小权限”，而是“自用完整体验权限集”；
* 未来若 SaaS 化，需要重新评估 Google OAuth 审核、安全评估和合规成本；
* MVP 不申请 `gmail.send`，不支持在系统内发送邮件。

---

### 2 Gmail 已读/未读同步

Gmail 已读/未读本质是 `UNREAD` Label 操作。

| 操作   | Gmail 行为          |
| ---- | ----------------- |
| 标记已读 | 移除 `UNREAD` label |
| 标记未读 | 添加 `UNREAD` label |

流程：

```text
用户点击标记已读
        ↓
校验用户拥有该 email
        ↓
校验 mailbox 具备 write_enabled 权限
        ↓
调用 GmailProvider.mark_as_read()
        ↓
Gmail API 移除 UNREAD label
        ↓
更新 emails.is_read = true
        ↓
写入 user_actions
        ↓
返回成功
```

如果 Gmail API 失败：

1. 不更新 `emails.is_read`；
2. 写入失败状态的 `user_actions`；
3. 前端提示同步失败。

---

### 3 权限模式

`mailboxes.permission_mode`：

| 值               | 含义                     |
| --------------- | ---------------------- |
| `readonly`      | 只允许读取邮件，不允许修改 Gmail 状态 |
| `write_enabled` | 允许修改 Gmail 已读/未读状态     |

即使 MVP 默认使用 `write_enabled`，代码仍必须支持 `readonly`，以便未来开源和产品化。

---

## 安全架构

### 1 安全原则

```text
系统登录             所有 API 必须鉴权
用户数据隔离         用户只能访问自己的邮箱、邮件、日报、行为
自用完整体验权限集   Gmail 使用 gmail.readonly + gmail.modify
Token 加密           refresh_token / IMAP 密码必须加密存储
正文最小化存储       body_text 截断，不存完整原始邮件
敏感信息不进日志     Token、邮件正文、完整 Prompt、AI API Key 不进日志
用户可撤销授权       支持断开邮箱并清除凭据
```

---

### 2 APP_ENCRYPTION_KEY

系统使用 `APP_ENCRYPTION_KEY` 加密敏感凭据。

要求：

1. 从 `.env` 读取；
2. 不得提交 Git；
3. 生产和开发环境使用不同密钥；
4. 推荐使用 32 bytes 随机密钥，并进行 Base64 编码；
5. 密钥丢失后，已加密 Token 无法解密，用户需要重新授权 Gmail；
6. `mailbox_credentials` 必须记录 `encryption_key_version`；
7. 未来 SaaS 化后应迁移到云 KMS 或密钥管理服务。

生成示例：

```bash
python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

`.env.example`：

```env
APP_ENCRYPTION_KEY=replace-with-32-byte-base64-key
```

---

### 3 Token 处理流程

```text
OAuth callback 获取 token
        ↓
使用 APP_ENCRYPTION_KEY 加密 refresh_token
        ↓
写入 mailbox_credentials
        ↓
access_token 短期缓存至 Redis
        ↓
调用 Gmail API 前检查 access_token
        ↓
过期则解密 refresh_token
        ↓
刷新 access_token
        ↓
更新 Redis 缓存
```

补充规则：

1. Access Token Redis TTL 默认取 `expires_in - 300s`，若上游未返回则默认 3300 秒；
2. 同一 `mailbox_id` 的 token refresh 必须使用分布式锁，避免并发刷新导致 Refresh Token 失效；
3. 锁值必须是**唯一请求 ID**（如 UUID）；
4. 释放锁必须使用 Lua 脚本比对当前持有者是否与请求 ID 一致，一致才可 `DEL`，防止误删其他请求的锁；
5. 获取锁失败时，退避 1 秒后重试获取缓存；若缓存仍未就绪，返回 `MAILBOX_REAUTH_REQUIRED` 错误。

---

### 4 日志规范

允许记录：

```text
job_id
user_id
mailbox_id
任务类型
任务状态
耗时
错误类型
```

禁止记录：

```text
access_token
refresh_token
IMAP 密码
邮件正文
完整 AI Prompt
AI API Key
APP_ENCRYPTION_KEY
```

---

### 5 AI 调用安全

1. 用户自行配置 AI API Key；
2. 不默认发送附件内容；
3. 邮件正文进入 AI 前进行 HTML 清洗和长度裁剪；
4. 不记录完整 Prompt；
5. `ai_runs.output_json` 自用阶段可保留；
6. 未来商业化时需重新评估是否保留 AI 原始输出。

---

### 6 AI API Key 安全规则（V1 实现）

本节规则在 V1 引入 `ai_provider_configs` 时生效。MVP 阶段 AI Key 仅在 `.env` 中管理。

#### 6.1 加密存储

1. AI API Key 必须使用 `APP_ENCRYPTION_KEY` + AES-256-GCM（或 Fernet）加密存储；
2. `ai_provider_configs` 必须包含 `encryption_key_version` 字段，与 `mailbox_credentials` 保持一致；
3. 未来密钥轮换时，通过 `encryption_key_version` 识别需要重新加密的记录；
4. 加密/解密复用 `mailbox_credentials` 同一工具模块，不创建独立加密路径。

#### 6.2 SSRF 防护

1. MVP 阶段不允许自定义 `base_url`，仅支持预定义 provider 的固定 endpoint；
2. V1 若支持自定义 `base_url`（如 Ollama 本地部署），必须：
   - 拒绝所有 RFC 1918 私有 IP（10.x.x.x、172.16-31.x.x、192.168.x.x）；
   - 拒绝 loopback（127.0.0.1、localhost）和 link-local（169.254.x.x）；
   - 拒绝云 metadata 地址（169.254.169.254 等）；
   - 强制 HTTPS；
   - 实现 DNS rebinding 防护。

#### 6.3 前端回显

1. API 返回 AI Key 时必须 mask，格式为 `前7字符 + **** + 后4字符`；
2. API 的 GET / LIST 响应**不得**包含 `api_key_encrypted` 字段；
3. 返回 `has_key: boolean` 标识是否存在已配置的 Key；
4. Key 更新（PATCH）为写-only 操作，不提供解密回读路径。

#### 6.4 日志脱敏

1. 禁止在日志中记录：AI API Key、解密后的凭据、完整 Prompt、完整 AI Response；
2. `ai_runs` 和未来的 `ai_usage_records` 仅允许记录元数据（timestamp、model、token 数、latency、status code、cost）；
3. 异常堆栈、HTTP 请求/响应日志必须经过脱敏过滤器。

#### 6.5 测试连接端点

1. `POST /api/ai-providers/{id}/test` 用于验证 API Key 有效性；
2. 必须限流：每用户每分钟最多 5 次；
3. 仅返回 `success: boolean`，不暴露详细错误信息；
4. 使用与主请求相同的 SSRF 防护规则。

#### 6.6 Coding Agent 凭据

Codex / Claude Code / 其他 Coding Agent 的 Token / API Key 属于敏感凭据，安全要求与 AI API Key 同等：
- 加密存储
- 不进日志
- 前端 masked 回显
- V2 阶段实现
