/**
 * Typed API client placeholder for MailMind (T005 scaffold).
 *
 * IMPORTANT: This file deliberately does NOT perform any real network calls,
 * authentication, Gmail sync, digest generation, or mark-read/unread behavior.
 * Every method is an unimplemented placeholder so that page components cannot
 * accidentally rely on fake success states. Real wiring (fetch + TanStack
 * Query) is the responsibility of later, in-scope tasks.
 *
 * The design-preview round intentionally kept this as a safe placeholder: no
 * page in the preview imports or calls it. Wire real fetch here only during a
 * dedicated integration task, strictly following docs/api/API_DESIGN.md.
 */

import { API_ROUTES } from "./api-routes";
import type { ApiResult } from "./api-types";

function notImplemented(operation: string): never {
  throw new Error(
    `Not implemented: ${operation} is a T005 placeholder. Real API wiring lands in a later task.`,
  );
}

/**
 * Method names map 1:1 to documented routes in docs/api/API_DESIGN.md. Return
 * types use the documented success/error envelope. No defaults, mock data, or
 * optimistic states are returned — calling any method throws.
 */
export const apiClient = {
  auth: {
    register(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.auth.register}`);
    },
    login(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.auth.login}`);
    },
    logout(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.auth.logout}`);
    },
    me(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.auth.me}`);
    },
  },

  digest: {
    today(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.digest.today}`);
    },
    generateToday(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.digest.todayGenerate}`);
    },
    refreshToday(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.digest.todayRefresh}`);
    },
    byId(digestId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.digest.byId(digestId)}`);
    },
  },

  emails: {
    today(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.emails.today}`);
    },
    new(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.emails.new}`);
    },
    byId(emailId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.emails.byId(emailId)}`);
    },
    markRead(emailId: string): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.emails.markRead(emailId)}`);
    },
    markUnread(emailId: string): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.emails.markUnread(emailId)}`);
    },
  },

  mailboxes: {
    list(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.mailboxes.list}`);
    },
    byId(mailboxId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.mailboxes.byId(mailboxId)}`);
    },
    syncStatus(mailboxId: string): Promise<ApiResult> {
      return notImplemented(
        `GET ${API_ROUTES.mailboxes.syncStatus(mailboxId)}`,
      );
    },
    sync(mailboxId: string): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.mailboxes.sync(mailboxId)}`);
    },
  },

  jobs: {
    byId(jobId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.jobs.byId(jobId)}`);
    },
  },

  actions: {
    create(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.actions.create}`);
    },
    forDigestItem(digestItemId: string): Promise<ApiResult> {
      return notImplemented(
        `GET ${API_ROUTES.actions.forDigestItem(digestItemId)}`,
      );
    },
  },

  users: {
    me(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.users.me}`);
    },
    updateMe(): Promise<ApiResult> {
      return notImplemented(`PATCH ${API_ROUTES.users.me}`);
    },
    updatePassword(): Promise<ApiResult> {
      return notImplemented(`PATCH ${API_ROUTES.users.mePassword}`);
    },
  },
} as const;
