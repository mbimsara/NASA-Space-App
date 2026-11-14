import { beforeEach, describe, expect, it } from "vitest";
import { initialEntries, loadCalendar, saveCalendar, sortedDated, toICS, validateCalendar, type CalendarEntry } from "./calendar";

const seasons = [
  { season_index: 1, crop_name: "Rice" },
  { season_index: 2, crop_name: "Cowpea" },
];
const e = (id: string, season_index: number, kind: CalendarEntry["kind"], date: string, note = ""): CalendarEntry => ({
  id,
  season_index,
  kind,
  date,
  note,
});

beforeEach(() => localStorage.clear());

describe("action calendar", () => {
  it("starts with one undated planting entry per season (no invented dates)", () => {
    const init = initialEntries(seasons);
    expect(init.map((x) => [x.season_index, x.kind, x.date])).toEqual([
      [1, "planting", ""],
      [2, "planting", ""],
    ]);
  });

  it("flags invalid dates and harvest before planting", () => {
    const errs = validateCalendar([
      e("p1", 1, "planting", "2026-11-01"),
      e("h1", 1, "harvest", "2026-10-01"),
      e("x", 2, "other", "2026-02-30"),
    ]);
    expect(errs.h1).toMatch(/on or after/);
    expect(errs.x).toMatch(/valid date/);
    expect(errs.p1).toBeUndefined();
  });

  it("sorts dated entries chronologically and skips undated ones", () => {
    const sorted = sortedDated([e("b", 2, "planting", "2027-04-10"), e("u", 1, "monitoring", ""), e("a", 1, "planting", "2026-11-01")]);
    expect(sorted.map((x) => x.id)).toEqual(["a", "b"]);
  });

  it("exports valid all-day .ics events with escaped text", () => {
    const ics = toICS(
      "plan-1",
      [e("a", 1, "planting", "2026-11-01", "Field A, north; check seed")],
      seasons,
      (k) => (k === "planting" ? "Planting" : k),
      "Farmer-entered",
      new Date("2026-11-14T10:00:00Z"),
    );
    expect(ics).toContain("BEGIN:VCALENDAR\r\n");
    expect(ics).toContain("DTSTART;VALUE=DATE:20261101");
    expect(ics).toContain("DTEND;VALUE=DATE:20261102");
    expect(ics).toContain("SUMMARY:Planting: Rice (season 1)");
    expect(ics).toContain("DESCRIPTION:Field A\\, north\\; check seed\\nFarmer-entered");
    expect(ics.trim().endsWith("END:VCALENDAR")).toBe(true);
  });

  it("persists per plan", () => {
    saveCalendar("plan-1", [e("a", 1, "planting", "2026-11-01")]);
    expect(loadCalendar("plan-1")).toHaveLength(1);
    expect(loadCalendar("plan-2")).toBeNull();
  });
});
