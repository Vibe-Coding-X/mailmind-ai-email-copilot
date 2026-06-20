import en from "./locales/en.json";
import zh from "./locales/zh.json";
import {
  LANGUAGE_STORAGE_KEY,
  SUPPORTED_LANGUAGES,
  type Language,
} from "./language";
import { useI18n } from "./provider";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type LanguageContract = Assert<Equal<Language, "en" | "zh">>;
type SupportedLanguagesContract = Assert<
  Equal<(typeof SUPPORTED_LANGUAGES)[number], Language>
>;
type StorageKeyContract = Assert<
  Equal<typeof LANGUAGE_STORAGE_KEY, "mailmind-language">
>;
type LocaleKeyParity = Assert<Equal<keyof typeof en, keyof typeof zh>>;
type UseI18nContract = Assert<
  Equal<
    ReturnType<typeof useI18n>,
    {
      language: Language;
      setLanguage: (language: Language) => void;
      t: (key: keyof typeof en) => string;
    }
  >
>;

const i18nAssertions: [
  LanguageContract,
  SupportedLanguagesContract,
  StorageKeyContract,
  LocaleKeyParity,
  UseI18nContract,
] = [true, true, true, true, true];

void i18nAssertions;
