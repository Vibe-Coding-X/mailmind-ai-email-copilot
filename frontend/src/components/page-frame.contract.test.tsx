import type { ComponentProps } from "react";

import { PageFrame } from "./page-frame";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;
type Assert<T extends true> = T;

type PageFrameProps = ComponentProps<typeof PageFrame>;
type BadgeLabelContract = Assert<
  Equal<PageFrameProps["badgeLabel"], string | undefined>
>;

const assertions: [BadgeLabelContract] = [true];

void assertions;
