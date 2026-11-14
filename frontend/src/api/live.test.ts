import { afterEach, describe, expect, it, vi } from "vitest";

const { request, fixtureRead } = vi.hoisted(() => ({ request: vi.fn(), fixtureRead: vi.fn() }));
vi.mock("axios", () => ({ default: { create: () => ({ request }), isAxiosError: (e: { isAxiosError?: boolean }) => e.isAxiosError } }));
vi.mock("./fixtures", async (importOriginal) => ({
  ...await importOriginal<typeof import("./fixtures")>(), getFarmFixture: fixtureRead,
}));

afterEach(() => { vi.unstubAllEnvs(); vi.clearAllMocks(); vi.resetModules(); });

describe("live API facade", () => {
  it.each([404, 409, 422, 503])("propagates %s without calling fixtures", async (status) => {
    vi.stubEnv("VITE_USE_FIXTURES", "false");
    const { api, USE_FIXTURES } = await import("./index");
    request.mockRejectedValue({ isAxiosError: true, response: { status,
      data: { error: { code: "TEST_ERROR", message: "Recorded backend error", fields: { input_version: "Check version" } } } } });
    expect(USE_FIXTURES).toBe(false);
    await expect(api.getFarm("farm-1")).rejects.toMatchObject({ status, code: "TEST_ERROR", fields: { input_version: "Check version" } });
    expect(fixtureRead).not.toHaveBeenCalled();
  });
  it("keeps backend unavailable as a network error, never demo success", async () => {
    vi.stubEnv("VITE_USE_FIXTURES", "false");
    const { api } = await import("./index");
    request.mockRejectedValue({ isAxiosError: true, code: "ECONNREFUSED" });
    await expect(api.getFarm("farm-1")).rejects.toMatchObject({ status: 0, code: "network" });
    expect(fixtureRead).not.toHaveBeenCalled();
  });
  it("preserves user cancellation", async () => {
    const { getFarm } = await import("./client");
    request.mockRejectedValue({ isAxiosError: true, code: "ERR_CANCELED" });
    await expect(getFarm("farm-1")).rejects.toMatchObject({ name: "AbortError" });
  });
  it("uses fixture functions only in explicit demo mode", async () => {
    vi.stubEnv("VITE_USE_FIXTURES", "true");
    const { api } = await import("./index");
    fixtureRead.mockResolvedValue({ id: "synthetic-demo" });
    await expect(api.getFarm("demo")).resolves.toEqual({ id: "synthetic-demo" });
    expect(request).not.toHaveBeenCalled();
  });
  it("preserves field errors and recovers from malformed proxy error envelopes", async () => {
    const { getFarm } = await import("./client");
    request.mockRejectedValue({ isAxiosError: true, message: "Bad gateway", response: { status: 503, data: { error: "upstream offline" } } });
    await expect(getFarm("farm-1")).rejects.toMatchObject({ status: 503, code: "UNAVAILABLE" });
  });
});
