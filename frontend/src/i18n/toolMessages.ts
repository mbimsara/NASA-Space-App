import type { TFunction } from "i18next";
import en from "./locales/en.json";
import { STANDARD_COST_CATEGORIES } from "../finance/calculator";

// Localize diagnostics at display time, keeping calculator results and saved inputs
// independent of language. Unrecognized server/source text retains its exact wording.
const templates = [
  ...Object.entries(en.financial.messages).map(([key, text]) => [`financial.messages.${key}`, text]),
  ...Object.entries(en.catalog.messages).map(([key, text]) => [`catalog.messages.${key}`, text]),
  ["calendar.invalidDate", en.calendar.invalidDate],
  ["calendar.harvestDate", en.calendar.harvestDate],
  ["catalog.empty", en.catalog.empty],
  ["catalog.draftNote", en.catalog.draftNote],
  ["catalog.unknownWaterNote", en.catalog.unknownWaterNote],
].map(([key, text]) => {
  const names: string[] = [];
  const escaped = text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = escaped.replace(/\\\{\\\{(\w+)\\\}\\\}/g, (_, name: string) => {
    names.push(name);
    return "(.+?)";
  });
  return { key, names, pattern: new RegExp(`^${pattern}$`) };
});

export function localizeToolMessage(message: string, t: TFunction): string {
  for (const { key, names, pattern } of templates) {
    const match = pattern.exec(message);
    if (!match) continue;
    const values = Object.fromEntries(names.map((name, i) => [name, match[i + 1]]));
    if (key === "financial.messages.unknownCost" || key === "financial.messages.omitted") {
      values.value = values.value.split(", ").map((label) => {
        const category = STANDARD_COST_CATEGORIES.find((c) => c.name === label);
        return category ? t(`financial.categories.${category.key}`, { defaultValue: label }) : label;
      }).join(", ");
    }
    return t(key, { ...values, defaultValue: message });
  }
  return message;
}
