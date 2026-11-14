import { describe, expect, it } from "vitest";
import { createLatestRequest, isAbortError } from "./requestGuard";

describe("createLatestRequest (stale-response guard)", () => {
  it("only the newest ticket is current, and older ones are aborted", () => {
    const g = createLatestRequest();
    const first = g.next();
    const second = g.next();
    expect(first.isCurrent()).toBe(false);
    expect(first.signal.aborted).toBe(true);
    expect(second.isCurrent()).toBe(true);
  });

  it("a slow old response cannot be applied after a newer request starts", async () => {
    const g = createLatestRequest();
    const applied: string[] = [];
    const run = (label: string, ms: number) => {
      const ticket = g.next();
      return new Promise<void>((r) => setTimeout(r, ms)).then(() => {
        if (ticket.isCurrent()) applied.push(label);
      });
    };
    await Promise.all([run("farm-A (slow)", 30), run("farm-B (fast)", 5)]);
    expect(applied).toEqual(["farm-B (fast)"]);
  });

  it("cancel invalidates the in-flight ticket", () => {
    const g = createLatestRequest();
    const t = g.next();
    g.cancel();
    expect(t.isCurrent()).toBe(false);
  });

  it("recognises abort errors", () => {
    expect(isAbortError(new DOMException("x", "AbortError"))).toBe(true);
    expect(isAbortError(new Error("x"))).toBe(false);
  });
});
