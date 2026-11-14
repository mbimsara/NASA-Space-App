import { describe, expect, it } from "vitest";
import { createInstance } from "i18next";
import en from "./locales/en.json";
import si from "./locales/si.json";
import ta from "./locales/ta.json";
import { localizeToolMessage } from "./toolMessages";

function flatten(value: object, prefix = ""): Record<string, string> {
  return Object.fromEntries(Object.entries(value).flatMap(([key, entry]) =>
    typeof entry === "object" ? Object.entries(flatten(entry, `${prefix}${key}.`)) : [[`${prefix}${key}`, entry]],
  ));
}

describe("Tools translations", () => {
  const english = flatten(en);
  const sections = /^(rotation|financial|calendar|plan|catalog|roadmap|irrigationNotice|common|offline)\./;
  for (const [language, resource] of Object.entries({ si, ta })) {
    const translated = flatten(resource);
    it(`${language} covers every Tools interface key without English fallback`, () => {
      expect(Object.keys(english).filter((key) => sections.test(key) && !translated[key])).toEqual([]);
    });
    it(`${language} preserves interpolation fields`, () => {
      for (const key of Object.keys(english).filter((key) => sections.test(key))) {
        expect(translated[key]?.match(/{{\w+}}/g)?.sort() ?? [], key)
          .toEqual(english[key].match(/{{\w+}}/g)?.sort() ?? []);
      }
    });
    it(`${language} translates calculator diagnostics and preserves user content`, async () => {
      const instance = createInstance();
      await instance.init({ lng: language, fallbackLng: "en", resources: { en: { translation: en }, [language]: { translation: resource } } });
      const t = instance.t.bind(instance);
      expect(localizeToolMessage("Must be a non-negative number", t)).toBe(resource.financial.messages.nonNegative);
      expect(localizeToolMessage('Cost "Seed / planting material" is unknown', t))
        .toBe(t("financial.messages.unknownCost", { value: resource.financial.categories.seed }));
      expect(localizeToolMessage("Not entered (not assumed zero): Seed / planting material, Transport.", t))
        .toBe(t("financial.messages.omitted", { value: `${resource.financial.categories.seed}, ${resource.financial.categories.transport}` }));
      expect(localizeToolMessage('Cost "My own category" is unknown', t))
        .toBe(t("financial.messages.unknownCost", { value: "My own category" }));
      expect(localizeToolMessage("2 crop(s) are drafts and will not be used for recommendations.", t))
        .toBe(t("catalog.draftNote", { count: 2 }));
      expect(localizeToolMessage("Harvest must be on or after the season's planting date", t))
        .toBe(resource.calendar.harvestDate);
      expect(localizeToolMessage('Duplicate crop ID "rice" (also at crops[0])', t))
        .toBe(t("catalog.messages.duplicate", { id: "rice", index: 0 }));
      expect(localizeToolMessage("A source's original wording", t)).toBe("A source's original wording");
      await instance.changeLanguage("en");
      expect(localizeToolMessage("Must be a non-negative number", t)).toBe("Must be a non-negative number");
    });
  }
});
