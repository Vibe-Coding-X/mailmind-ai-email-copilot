# MailMind

**MailMind** is a local-first AI email copilot designed to help users understand and process daily emails more efficiently.

Instead of acting as a traditional inbox client, MailMind focuses on generating an actionable **Daily Digest** from Gmail emails. It analyzes the emails received during the day, identifies what needs attention, and organizes them into a decision-oriented dashboard.

## Overview

Modern inboxes are often noisy, time-consuming, and difficult to prioritize. Important emails may be buried under notifications, newsletters, and low-value messages.

MailMind aims to solve this by turning daily email flow into a structured AI decision board.

The core idea is simple:

> Do not make users read every email first. Let AI summarize, prioritize, and suggest what should be handled today.

## Product Positioning

MailMind is not intended to replace Gmail or become a full-featured email client.

It is designed as an AI-powered decision layer on top of email.

The product helps users answer questions such as:

* Which emails require my attention today?
* Which emails should I reply to?
* Which emails can be safely ignored?
* What tasks or risks are hidden inside today’s emails?
* Has anything new arrived since the last digest was generated?

## MVP Scope

The current MVP focuses on a single-user, local-first workflow.

### Included in MVP

* Gmail OAuth integration
* Daily email synchronization
* AI-generated Daily Digest
* Actionable email recommendations
* Email priority classification
* Email detail view
* New email detection after digest generation
* Manual and scheduled digest generation
* Gmail read / unread status synchronization
* Local Docker-based development environment

### Not Included in MVP

* Outlook integration
* IMAP integration
* Multi-inbox aggregation
* AI auto-reply
* Automatic email sending
* Attachment analysis
* Mobile app
* Desktop app
* SaaS multi-tenant support

## Core Features

### Daily Digest Dashboard

MailMind uses a dashboard-first design. The homepage is not a traditional inbox list. Instead, it displays the current day’s AI-generated email digest.

The dashboard includes:

* Daily email overview
* Must-handle emails
* Recommended-to-review emails
* Ignorable emails
* Extracted action items
* Risk reminders
* Digest freshness status
* New email notification after digest generation

### Actionable AI Suggestions

MailMind does not only summarize emails. It generates structured action suggestions such as:

* Reply today
* Review today
* Handle before deadline
* Ignore
* Follow up later
* No action required

Each suggestion may include:

* Related email
* Suggested action
* Priority
* Reason
* Deadline
* Confidence score

### Digest Freshness Tracking

A Daily Digest is treated as a time-bounded snapshot.

Each digest records:

* Generation time
* Coverage start time
* Coverage end time
* Number of analyzed emails
* Number of new emails received after generation
* Current status: fresh, stale, refreshing, or failed

If new emails arrive after the digest is generated, MailMind does not silently overwrite the dashboard. Instead, it informs the user that new emails have not yet been included and allows the user to refresh the digest manually.

### Gmail Read / Unread Sync

MailMind supports syncing read and unread status back to Gmail.

This requires the Gmail `gmail.modify` scope. The project currently targets personal and local-first usage. If the project is later developed into a public SaaS product, Google OAuth verification and restricted scope security requirements must be reassessed.

## Architecture

MailMind uses a frontend-backend separated architecture with asynchronous task processing.

```text
Frontend Web
Next.js + TypeScript
Dashboard / Email Detail / Settings
        ↓
Backend API
FastAPI
Auth API / Digest API / Email API
        ↓
Core Services
Auth Layer / Email Layer / AI Layer
        ↓
Provider Adapter
GmailProvider
        ↓
Async Task System
Celery + Redis
        ↓
Storage
PostgreSQL + Redis
```

## Planned Tech Stack

### Frontend

* Next.js
* TypeScript
* Dashboard-first UI
* Email detail page
* Gmail authorization settings

### Backend

* FastAPI
* Gmail OAuth 2.0
* Gmail Provider Adapter
* Digest API
* Email API
* Job API

### Async Tasks

* Celery
* Redis
* Email synchronization
* AI digest generation
* Token refresh
* New email detection

### Storage

* PostgreSQL
* Redis
* Local Docker volumes

### AI Pipeline

The AI layer is designed as an independent pipeline:

```text
EmailPreprocessor
        ↓
DigestInputBuilder
        ↓
LLMClient
        ↓
StructuredOutputParser
        ↓
DigestDecisionEngine
        ↓
SafetyFilter
```

The AI output is expected to follow a structured JSON schema so that it can be parsed, stored, and displayed reliably.

## Data Model Draft

The planned core tables include:

* `users`
* `mailboxes`
* `emails`
* `daily_digests`
* `digest_items`
* `sync_jobs`

Where:

* `daily_digests` represents a daily AI-generated email digest snapshot.
* `digest_items` represents individual AI decision items inside a digest.
* `emails` stores synchronized Gmail email metadata and cleaned text content.
* `mailboxes` stores connected mailbox information and encrypted OAuth tokens.

## Security Principles

MailMind follows a local-first security model during the MVP stage.

Key principles:

* Do not store Gmail passwords
* Use OAuth 2.0 authorization
* Encrypt refresh tokens
* Cache access tokens only temporarily
* Minimize email body storage
* Do not log access tokens, refresh tokens, full email bodies, full prompts, or AI API keys
* Allow users to disconnect Gmail authorization
* Do not analyze attachments by default
* Let users provide their own AI API key in local configuration

## Gmail Permissions

The MVP may use the following Gmail API scopes:

| Scope            | Purpose                                     |
| ---------------- | ------------------------------------------- |
| `gmail.readonly` | Read email list, metadata, and body content |
| `gmail.modify`   | Modify read / unread status                 |

The `gmail.modify` scope is a restricted Gmail scope. It is acceptable for local personal testing, but public distribution or SaaS usage may require additional Google verification and security review.

## Development Status

Current status:

> MVP design and documentation stage.

This repository currently stores product and architecture documents. Implementation will be added gradually after the core engineering documents are finalized.

## Planned Documentation

```text
docs/
  PRD.md
  SYSTEM_DESIGN.md
  DATABASE_DESIGN.md
  API_DESIGN.md
  AI_PIPELINE.md
  SECURITY.md
  TASK_BREAKDOWN.md
```

Currently available:

* Product Requirements Document
* System Architecture Design

Planned next:

* Database Design
* API Design
* AI Pipeline Design
* Security Design
* Task Breakdown for implementation

## Roadmap

### MVP

* Gmail OAuth integration
* Daily email synchronization
* AI Daily Digest generation
* Actionable email recommendations
* Email detail view
* New email detection
* Gmail read / unread status synchronization

### V1

* Outlook integration
* IMAP integration
* AI reply draft generation
* Email thread summary
* Semantic email search

### V2

* Multi-inbox aggregation
* Incremental AI analysis
* Desktop client
* Auto-archive suggestions
* Smart labels

### V3

* SaaS version
* Multi-tenant support
* Privacy and compliance hardening
* Team collaboration features

## Repository Name

The repository name is:

```text
mailmind-ai-email-copilot
```

The product name is:

```text
MailMind
```

## Disclaimer

MailMind is currently a personal learning and engineering practice project. It is not yet a production-ready SaaS product.

If you use Gmail API, OAuth scopes, email content processing, or third-party AI model APIs, please evaluate the corresponding privacy, security, and compliance risks based on your own use case.

## License

TBD.
