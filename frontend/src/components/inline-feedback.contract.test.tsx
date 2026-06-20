import type { ComponentProps } from "react";

import { InlineFeedback } from "./inline-feedback";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type InlineFeedbackProps = ComponentProps<typeof InlineFeedback>;
type InlineFeedbackToneContract = Assert<
  Equal<InlineFeedbackProps["tone"], "info" | "success" | "warning" | "danger">
>;
type InlineFeedbackTitleContract = Assert<
  Equal<InlineFeedbackProps["title"], string | undefined>
>;
type InlineFeedbackActionContract = Assert<
  Equal<InlineFeedbackProps["action"], React.ReactNode | undefined>
>;

type InlineFeedbackAssertions = [
  InlineFeedbackToneContract,
  InlineFeedbackTitleContract,
  InlineFeedbackActionContract,
];

const inlineFeedbackAssertions: InlineFeedbackAssertions = [true, true, true];

void inlineFeedbackAssertions;
