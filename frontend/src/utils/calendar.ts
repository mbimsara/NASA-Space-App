/**
 * Action calendar for a saved plan (IMPLEMENTATION_PLAN follow-on: "Action calendar
 * and reminders — selected plan and planting dates saved; choose reminder delivery
 * separately"). Owner: Shehani; backend records: Dulanjaya.
 *
 * Only farmer-entered dates are used. No planting windows, intervals or agronomic
 * timings are generated here (those would need Bhagya's review). Entries are stored
 * on this device until the calendar endpoint exists. Export is an .ics file; no
 * reminders are sent.
 */
import { isIsoDate } from "./validation";

export const ACTION_KINDS = ["planting", "monitoring", "soil_test", "harvest", "other"] as const;
export type ActionKind = (typeof ACTION_KINDS)[number];

export interface CalendarEntry {
  id: string;
  season_index: number;
  kind: ActionKind;
  /** YYYY-MM-DD, or "" while not yet chosen. */
  date: string;
  note: string;
}

export interface SeasonInfo {
  season_index: number;
  crop_name: string;
}

const key = (planId: string) => `agrosphere_calendar_${planId}`;

export function loadCalendar(planId: string): CalendarEntry[] | null {
  try {
    const raw = localStorage.getItem(key(planId));
    const v = raw ? JSON.parse(raw) : null;
    return Array.isArray(v) ? v : null;
  } catch {
    return null;
  }
}

export function saveCalendar(planId: string, entries: CalendarEntry[]) {
  try {
    localStorage.setItem(key(planId), JSON.stringify(entries));
  } catch {
    /* storage unavailable */
  }
}

/** One empty planting entry per season to start from. */
export function initialEntries(seasons: SeasonInfo[]): CalendarEntry[] {
  return seasons.map((s) => ({ id: `s${s.season_index}-planting`, season_index: s.season_index, kind: "planting", date: "", note: "" }));
}

/** Field errors keyed by entry id. */
export function validateCalendar(entries: CalendarEntry[]): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const e of entries) {
    if (e.date !== "" && !isIsoDate(e.date)) errors[e.id] = "Use a valid date (YYYY-MM-DD)";
  }
  const seasons = new Set(entries.map((e) => e.season_index));
  for (const s of seasons) {
    const plantings = entries.filter((e) => e.season_index === s && e.kind === "planting" && isIsoDate(e.date)).map((e) => e.date);
    if (plantings.length === 0) continue;
    const firstPlanting = plantings.sort()[0];
    for (const h of entries.filter((e) => e.season_index === s && e.kind === "harvest" && isIsoDate(e.date))) {
      if (h.date < firstPlanting) errors[h.id] = "Harvest must be on or after the season's planting date";
    }
  }
  return errors;
}

/** Dated entries in chronological order (undated entries are left out). */
export function sortedDated(entries: CalendarEntry[]): CalendarEntry[] {
  return entries
    .filter((e) => isIsoDate(e.date))
    .sort((a, b) => a.date.localeCompare(b.date) || a.season_index - b.season_index || a.kind.localeCompare(b.kind));
}

function icsEscape(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/,/g, "\\,").replace(/;/g, "\\;");
}

function nextDay(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

/** RFC 5545 calendar with one all-day event per dated entry. */
export function toICS(
  planId: string,
  entries: CalendarEntry[],
  seasons: SeasonInfo[],
  kindLabel: (k: ActionKind) => string,
  disclaimer: string,
  now: Date = new Date(),
): string {
  const stamp = now.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const crop = (i: number) => seasons.find((s) => s.season_index === i)?.crop_name ?? `Season ${i}`;
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AgroSphere AI//Action calendar//EN", "CALSCALE:GREGORIAN"];
  for (const e of sortedDated(entries)) {
    lines.push(
      "BEGIN:VEVENT",
      `UID:${planId}-${e.id}@agrosphere.local`,
      `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${e.date.replace(/-/g, "")}`,
      `DTEND;VALUE=DATE:${nextDay(e.date).replace(/-/g, "")}`,
      `SUMMARY:${icsEscape(`${kindLabel(e.kind)}: ${crop(e.season_index)} (season ${e.season_index})`)}`,
      `DESCRIPTION:${icsEscape([e.note, disclaimer].filter(Boolean).join("\n"))}`,
      "END:VEVENT",
    );
  }
  lines.push("END:VCALENDAR");
  return lines.join("\r\n") + "\r\n";
}
