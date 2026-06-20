import type { ComponentProps } from "react";

import { Button } from "./button";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type ButtonProps = ComponentProps<typeof Button>;
type ButtonDisabledReasonContract = Assert<
  Equal<ButtonProps["disabledReason"], string | undefined>
>;
type ButtonOnClickContract = Assert<
  Equal<ButtonProps["onClick"], React.MouseEventHandler<HTMLButtonElement> | undefined>
>;
type ButtonVariantContract = Assert<
  Equal<ButtonProps["variant"], "default" | "primary" | "ghost" | undefined>
>;

type ButtonAssertions = [
  ButtonDisabledReasonContract,
  ButtonOnClickContract,
  ButtonVariantContract,
];

const buttonAssertions: ButtonAssertions = [true, true, true];

void buttonAssertions;
