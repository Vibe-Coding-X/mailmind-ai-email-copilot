# AI Email Copilot 异步任务设计

> 本文档由 `docs/architecture/SYSTEM_DESIGN.md` 拆分而来，作为该专题的详细设计文档。
> 系统级背景、设计目标和模块关系请先阅读 `../architecture/SYSTEM_DESIGN.md`。

## 异步任务设计

异步任务使用 Celery + Redis。

### 1 任务类型

| 任务名                             | 触发时机                | 说明                    |
| ------------------------------- | ------------------- | --------------------- |
| `sync_today_emails`             | 首次授权、手动同步、刷新日报、定时任务 | 同步当日 Gmail 邮件         |
| `generate_daily_digest`         | 首次同步完成、手动触发、定时任务    | 生成今日 AI 日报            |
| `refresh_daily_digest`          | 用户点击刷新日报            | 同步新邮件并生成新版本           |
| `check_new_emails_after_digest` | 用户打开首页              | 检测日报生成后的新邮件           |
| `refresh_access_token`          | Access Token 过期     | 刷新 Gmail Access Token |

---

### 2 任务并发规则

1. 同一 `mailbox_id + date` 同一时间只能有一个 Digest 生成任务；
2. 如果存在 `generating / running / refreshing` 任务，新请求直接返回已有 `job_id`；
3. 手动刷新优先级高于定时任务；
4. 如果当日已有 `fresh` 当前日报，定时任务不覆盖；
5. 如果当日当前日报为 `failed`，允许自动重试；
6. 自动重试最多 3 次；
7. 服务在定时时间未运行，MVP 不做补偿执行。

v0.4.1 补充规则：

1. 同一用户同一 mailbox 只允许一个 queued/running `email_sync` job；
2. 手动同步与 scheduled sync 共享同一套去重逻辑；
3. worker 执行 sync 前获取 `sync:mailbox:{mailbox_id}` lock，value 为 job id，TTL 为 20 分钟；
4. lock 释放前校验 value，避免误删其他 worker 的 lock；
5. 可重试网络、TLS、timeout、rate limit 类错误，使用 backoff + jitter，最多 3 次；
6. reauth、permission、duplicate、lock conflict 类错误不重试；
7. 错误信息必须脱敏后进入 Job API。

---

### 3 异步任务交互模式

```text
POST /api/digest/today/generate
        ↓
返回 { "job_id": "xxx" }
        ↓
前端轮询 GET /api/jobs/{job_id}
        ↓
任务完成后 GET /api/digest/today
        ↓
展示当前版本日报
```

---

### 4 定时任务配置

```env
DIGEST_AUTO_GENERATE=true
DIGEST_GENERATE_TIME=08:00
```

说明：

* MVP 使用应用配置时区触发默认定时任务；
* Digest 统计窗口仍按 `users.timezone` 计算；
* 默认单用户场景下，应用配置时区必须与默认 `users.timezone`（`Asia/Shanghai`）一致；
* 后续多用户场景按用户 `users.timezone` 分别调度。

---
