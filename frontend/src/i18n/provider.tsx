"use client";

import i18next, { type i18n as I18nInstance } from "i18next";
import {
  I18nextProvider,
  initReactI18next,
} from "react-i18next";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import en from "./locales/en.json";
import zh from "./locales/zh.json";
import {
  persistLanguage,
  resolveInitialLanguage,
  type Language,
} from "./language";

export type TranslationKey = keyof typeof en;

interface I18nContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

const resources = {
  en: { translation: en },
  zh: { translation: zh },
} as const;

function createI18n(language: Language): I18nInstance {
  const instance = i18next.createInstance();
  void instance.use(initReactI18next).init({
    lng: language,
    fallbackLng: "en",
    resources,
    interpolation: {
      escapeValue: false,
    },
  });
  return instance;
}

export function MailMindI18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");
  const [instance] = useState(() => createI18n("en"));

  useEffect(() => {
    const resolved = resolveInitialLanguage();
    setLanguageState(resolved);
    void instance.changeLanguage(resolved);
    document.documentElement.lang = resolved === "zh" ? "zh-CN" : "en";
  }, [instance]);

  const setLanguage = useCallback(
    (nextLanguage: Language) => {
      setLanguageState(nextLanguage);
      persistLanguage(nextLanguage);
      void instance.changeLanguage(nextLanguage);
      document.documentElement.lang = nextLanguage === "zh" ? "zh-CN" : "en";
    },
    [instance],
  );

  const t = useCallback<I18nContextValue["t"]>(
    (key) => instance.t(key),
    [instance],
  );

  const value = useMemo<I18nContextValue>(
    () => ({ language, setLanguage, t }),
    [language, setLanguage, t],
  );

  return (
    <I18nextProvider i18n={instance}>
      <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
    </I18nextProvider>
  );
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (ctx === null) {
    throw new Error("useI18n must be used within MailMindI18nProvider");
  }
  return ctx;
}
