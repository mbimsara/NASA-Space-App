/**
 * LanguageSwitcher — switches app language without losing farm/analysis state.
 * Owner: Shehani. Translation accuracy must be verified by fluent reviewers.
 * NOTE: Sinhala and Tamil translations require fluent-speaker review before go-live.
 */
import { useTranslation } from "react-i18next";
import { useAppStore } from "../../hooks/useAppStore";
import type { Language } from "../../types/api";

const LANGUAGES: { code: Language; label: string }[] = [
  { code: "en", label: "English" },
  { code: "si", label: "සිංහල" },
  { code: "ta", label: "தமிழ்" },
];

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const setLanguage = useAppStore((s) => s.setLanguage);

  const handleChange = (lang: Language) => {
    i18n.changeLanguage(lang);
    setLanguage(lang);
    // Farm/analysis state is preserved in Zustand — no reset here
  };

  return (
    <div className="language-switcher">
      <label htmlFor="lang-select">
        {t("nav.language")}
      </label>
      <select
        id="lang-select"
        value={i18n.language}
        onChange={(e) => handleChange(e.target.value as Language)}
      >
        {LANGUAGES.map((l) => (
          <option key={l.code} value={l.code}>{l.label}</option>
        ))}
      </select>
    </div>
  );
}

