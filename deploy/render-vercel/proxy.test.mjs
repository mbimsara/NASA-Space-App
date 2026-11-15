import test from "node:test";
import assert from "node:assert/strict";
import { proxy } from "../../frontend/api/gateway.mjs";

const env = { RENDER_API_BASE_URL: "https://backend.example", STAGING_BACKEND_TOKEN: "t".repeat(48),
  STAGING_FRONTEND_ORIGIN: "https://frontend.example" };
const req = (path = "/api/v1/farms", options = {}) => new Request(env.STAGING_FRONTEND_ORIGIN + path,
  { ...options, headers: { ...options.headers } });

test("fails closed without server configuration", async () => {
  assert.equal((await proxy(req(), {})).status, 503);
  assert.equal((await proxy(req(), { ...env, RENDER_API_BASE_URL: "http://backend.example" })).status, 503);
});
test("rejects mismatched origins, writes without Origin, and arbitrary routes", async () => {
  assert.equal((await proxy(req("/api/v1/farms", { method: "POST" }), env)).status, 403);
  assert.equal((await proxy(req("/api/v1/farms", { headers: { Origin: "https://evil.example" } }), env)).status, 403);
  assert.equal((await proxy(req("/api/not-an-api"), env)).status, 404);
  assert.equal((await proxy(req("/api/v1/farms", { method: "DELETE" }), env)).status, 405);
});
test("forwards original JSON, query and statuses without exposing credentials", async () => {
  for (const status of [200, 201, 404, 409, 422, 503]) {
    const response = await proxy(req("/api/v1/farms?test=one", { method: "POST", body: '{"test":true}',
      headers: { Origin: env.STAGING_FRONTEND_ORIGIN, Cookie: "private", "Content-Type": "application/json" } }), env,
    async (url, options) => {
      assert.equal(url.href, "https://backend.example/api/v1/farms?test=one");
      assert.equal(options.headers.Authorization, `Bearer ${env.STAGING_BACKEND_TOKEN}`);
      assert.equal(options.headers.Cookie, undefined);
      assert.equal(Buffer.from(options.body).toString(), '{"test":true}');
      assert.equal(options.redirect, "manual");
      return Response.json({ test: true }, { status, headers: { "Set-Cookie": "private", "X-Observation-Cache": "hit" } });
    });
    assert.equal(response.status, status);
    assert.deepEqual(await response.json(), { test: true });
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.equal(response.headers.get("set-cookie"), null);
    assert.equal(response.headers.get("x-observation-cache"), "hit");
  }
});
test("network failures and redirects produce honest unavailability, never fixtures", async () => {
  const failure = await proxy(req(), env, async () => { throw new Error("private upstream details"); });
  assert.equal(failure.status, 503);
  assert.doesNotMatch(await failure.text(), /private upstream details/);
  assert.equal((await proxy(req(), env, async () => new Response(null, { status: 302, headers: { Location: "https://evil.example" } }))).status, 503);
});
test("oversized bodies are rejected before forwarding", async () => {
  assert.equal((await proxy(req("/api/v1/farms", { method: "POST", body: "x".repeat(1_048_577),
    headers: { Origin: env.STAGING_FRONTEND_ORIGIN } }), env)).status, 413);
});
