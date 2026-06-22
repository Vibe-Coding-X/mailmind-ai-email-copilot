export const SUPPORTED_LANGUAGES = ["en", "zh"] as const;

export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const LANGUAGE_STORAGE_KEY = "mailmind-language";

export function isLanguage(value: unknown): value is Language {
  return (
    typeof value === "string" &&
    (SUPPORTED_LANGUAGES as readonly string[]).includes(value)
  );
}

export function resolveInitialLanguage(): Language {
  if (typeof window === "undefined") {
    return "en";
  }

  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (isLanguage(stored)) {
      return stored;
    }
  } catch {
    // localStorage may be unavailable; fall through to navigator language.
  }

  const browserLanguage = window.navigator.language.toLowerCase();
  return browserLanguage.startsWith("zh") ? "zh" : "en";
}

export function persistLanguage(language: Language): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch {
    // Preference persistence is best-effort only.
  }
}
