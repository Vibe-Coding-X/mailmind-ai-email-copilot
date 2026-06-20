import type { EmailSummary } from "./api-types";
import {
  buildEmailListHref,
  displayBodyText,
  filterEmailsByQuery,
  parseEmailReadFilter,
} from "./emails";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type FilterEmailsByQueryParameters = Assert<
  Equal<Parameters<typeof filterEmailsByQuery>, [EmailSummary[], string]>
>;
type FilterEmailsByQuerySignature = Assert<
  Equal<ReturnType<typeof filterEmailsByQuery>, EmailSummary[]>
>;
type ParseEmailReadFilterParameters = Assert<
  Equal<Parameters<typeof parseEmailReadFilter>, [string | null]>
>;
type BuildEmailListHrefParameters = Assert<
  Equal<
    Parameters<typeof buildEmailListHref>,
    [{ filter?: string | null; query?: string | null }]
  >
>;
type BuildEmailListHrefSignature = Assert<
  Equal<ReturnType<typeof buildEmailListHref>, string>
>;
type DisplayBodyTextParameters = Assert<
  Equal<
    Parameters<typeof displayBodyText>,
    [bodyText: string | null, snippet: string]
  >
>;
type DisplayBodyTextSignature = Assert<
  Equal<ReturnType<typeof displayBodyText>, string>
>;

type EmailHelperAssertions = [
  FilterEmailsByQueryParameters,
  FilterEmailsByQuerySignature,
  ParseEmailReadFilterParameters,
  BuildEmailListHrefParameters,
  BuildEmailListHrefSignature,
  DisplayBodyTextParameters,
  DisplayBodyTextSignature,
];

const emailHelperAssertions: EmailHelperAssertions = [
  true,
  true,
  true,
  true,
  true,
  true,
  true,
];

void emailHelperAssertions;
