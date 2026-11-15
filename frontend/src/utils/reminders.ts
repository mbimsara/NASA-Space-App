import type { CalendarEntry } from "./calendar";

export function remindersDue(entries: CalendarEntry[], today: string, daysAhead = 1): CalendarEntry[] {
  const start = new Date(`${today}T00:00:00Z`);
  const end = new Date(start); end.setUTCDate(end.getUTCDate() + daysAhead);
  return entries.filter((entry) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(entry.date)) return false;
    const date = new Date(`${entry.date}T00:00:00Z`);
    return date >= start && date <= end;
  }).sort((left, right) => left.date.localeCompare(right.date));
}

const key = (planId: string, entryId: string, date: string) => `agrosphere_reminded_${planId}_${entryId}_${date}`;

export function wasReminded(planId: string, entry: CalendarEntry): boolean {
  return localStorage.getItem(key(planId, entry.id, entry.date)) === "1";
}

export function markReminded(planId: string, entry: CalendarEntry) {
  localStorage.setItem(key(planId, entry.id, entry.date), "1");
}
