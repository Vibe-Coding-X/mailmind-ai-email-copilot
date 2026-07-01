import { DEFAULT_THEME } from "./theme";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;
type Assert<T extends true> = T;

type DefaultPresetContract = Assert<
  Equal<typeof DEFAULT_THEME.preset, "dense-minimal">
>;
type DefaultModeContract = Assert<Equal<typeof DEFAULT_THEME.mode, "light">>;

const assertions: [DefaultPresetContract, DefaultModeContract] = [true, true];

void assertions;
