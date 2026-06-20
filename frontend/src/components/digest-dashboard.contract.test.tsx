import { ApiRequestError } from "@/lib/api-client";
import { digestErrorView } from "./digest-dashboard";
import type { TranslationKey } from "@/i18n/provider";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type DigestErrorViewParameters = Assert<
  Equal<
    Parameters<typeof digestErrorView>,
    [error: unknown, t: (key: TranslationKey) => string]
  >
>;
type DigestErrorViewSignature = Assert<
  Equal<
    ReturnType<typeof digestErrorView>,
    {
      state: "empty" | "unauthorized" | "backend_unavailable" | "error";
      title: string;
      message: string;
    }
  >
>;

const t = (key: TranslationKey) => key;
const digestAuthError = digestErrorView(
  new ApiRequestError("Authentication required.", "UNAUTHORIZED", 401),
  t,
);
const digestMailboxError = digestErrorView(
  new ApiRequestError(
    "Gmail authorization is no longer valid.",
    "MAILBOX_REAUTH_REQUIRED",
    401,
  ),
  t,
);

const digestErrorAssertions: [
  DigestErrorViewParameters,
  DigestErrorViewSignature,
] = [true, true];

void digestErrorAssertions;
void digestAuthError;
void digestMailboxError;
