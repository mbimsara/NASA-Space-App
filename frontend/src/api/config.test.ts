import { describe, expect, it } from "vitest";
import { apiConfiguration } from "./config";

describe("explicit live and demo configuration", () => {
  it("uses live HTTP by default and for false", () => {
    expect(apiConfiguration().useFixtures).toBe(false);
    expect(apiConfiguration("false").apiBaseUrl).toBe("http://localhost:8000/api/v1");
  });
  it("requires explicit true for synthetic demonstration data", () => {
    expect(apiConfiguration("true").useFixtures).toBe(true);
    expect(() => apiConfiguration("FALSE")).toThrow("must be true");
  });
  it("isolates fixture caches and different API deployments", () => {
    const live = apiConfiguration("false");
    expect(live.namespace).not.toBe(apiConfiguration("true").namespace);
    expect(live.namespace).not.toBe(apiConfiguration("false", "https://example.invalid/api/v1").namespace);
    expect(live.namespace).toBe(apiConfiguration("false", live.apiBaseUrl + "/").namespace);
  });
});
