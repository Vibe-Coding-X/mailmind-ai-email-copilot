import { ApiRequestError } from "./api-client";
import type { EmailMutation, EmailSummary } from "./api-types";

export type EmailReadFilter = "all" | "unread" | "read";

export type EmailErrorKind =
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "backend_unavailable"
  | "error";

export interface EmailErrorView {
  kind: EmailErrorKind;
  title: string;
  message: string;
}

export const EMAIL_READ_FILTERS: Array<{
  value: EmailReadFilter;
  label: string;
}> = [
  { value: "all", label: "All" },
  { value: "unread", label: "Unread" },
  { value: "read", label: "Read" },
];

export function emailErrorView(error: unknown): EmailErrorView {
  if (error instanceof ApiRequestError) {
    if (error.status === 401 || error.code === "UNAUTHORIZED") {
      return {
        kind: "unauthorized",
        title: "Not signed in",
        message: "Sign in with your MailMind account to load emails.",
      };
    }

    if (error.status === 403 || error.code === "FORBIDDEN") {
      return {
        kind: "forbidden",
        title: "Access denied",
        message: error.message,
      };
    }

    if (error.status === 404 || error.code === "NOT_FOUND") {
      return {
        kind: "not_found",
        title: "Email not found",
        message: error.message,
      };
    }

    if (
      error.status === 0 ||
      error.code === "NETWORK_ERROR" ||
      error.code === "BACKEND_UNAVAILABLE"
    ) {
      return {
        kind: "backend_unavailable",
        title: "Backend unavailable",
        message: "Unable to reach the server. Check that the backend is running.",
      };
    }

    return {
      kind: "error",
      title: "Email error",
      message: error.message,
    };
  }

  return {
    kind: "error",
    title: "Email error",
    message: "Something went wrong. Please try again.",
  };
}

export function filterEmails(
  emails: EmailSummary[],
  filter: EmailReadFilter,
): EmailSummary[] {
  if (filter === "unread") {
    return emails.filter((email) => !email.is_read);
  }

  if (filter === "read") {
    return emails.filter((email) => email.is_read);
  }

  return emails;
}

export function mergeEmailMutation<TEmail extends { id: string }>(
  email: TEmail,
  mutation: EmailMutation,
): TEmail {
  if (email.id !== mutation.id) {
    return email;
  }

  return { ...email, ...mutation };
}

export function formatEmailDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export function formatRecipients(recipients: string[]): string {
  if (recipients.length === 0) {
    return "No recipients";
  }

  return recipients.join(", ");
}

export function displaySubject(subject: string): string {
  const trimmed = subject.trim();
  return trimmed.length > 0 ? trimmed : "(No subject)";
}

export function displaySnippet(snippet: string): string {
  const trimmed = snippet.trim();
  return trimmed.length > 0 ? trimmed : "No preview text.";
}
