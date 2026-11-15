import { describe, expect, it } from "vitest";
import { remindersDue } from "./reminders";

describe("calendar reminders", () => {
  it("selects today and tomorrow without including past or later actions", () => {
    const entries = [
      { id: "past", season_index: 1, kind: "other", date: "2026-01-01", note: "" },
      { id: "today", season_index: 1, kind: "planting", date: "2026-01-02", note: "" },
      { id: "tomorrow", season_index: 1, kind: "monitoring", date: "2026-01-03", note: "" },
      { id: "later", season_index: 1, kind: "harvest", date: "2026-01-04", note: "" },
    ] as const;
    expect(remindersDue([...entries], "2026-01-02", 1).map((item) => item.id)).toEqual(["today", "tomorrow"]);
  });
});
