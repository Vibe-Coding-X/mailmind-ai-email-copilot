import type { ComponentProps } from "react";

import { AccountMenu } from "./account-menu";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type AccountMenuProps = ComponentProps<typeof AccountMenu>;
type AccountMenuCompactContract = Assert<
  Equal<AccountMenuProps["compact"], boolean | undefined>
>;

const accountMenuAssertions: [AccountMenuCompactContract] = [true];

void accountMenuAssertions;
