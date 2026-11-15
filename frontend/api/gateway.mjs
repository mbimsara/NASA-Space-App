const reply = (status, code, message, headers = {}) => Response.json(
  { error: { code, message } }, { status, headers: { "Cache-Control": "no-store", ...headers } },
);

/** Server-only gateway. Never import this module into frontend/src/. */
export async function proxy(request, env = process.env, upstreamFetch = fetch) {
  const { RENDER_API_BASE_URL: upstream, STAGING_BACKEND_TOKEN: token,
    STAGING_FRONTEND_ORIGIN: origin } = env;
  let target;
  try {
    target = new URL(upstream);
    if (target.protocol !== "https:" || target.pathname !== "/" || target.search || target.hash
        || target.username || target.password || !token || token.length < 32 || !origin
        || new URL(origin).origin !== origin || !origin.startsWith("https://")) throw new Error();
  } catch {
    return reply(503, "SERVICE_UNAVAILABLE", "Staging gateway is not configured.");
  }
  const url = new URL(request.url);
  if (url.origin !== origin || (request.headers.has("origin") && request.headers.get("origin") !== origin)) {
    return reply(403, "CONTEXT_MISMATCH", "This staging origin is not allowed.");
  }
  if (!url.pathname.startsWith("/api/v1/")) return reply(404, "NOT_FOUND", "API route not found.");
  if (!["GET", "HEAD", "POST", "PATCH", "OPTIONS"].includes(request.method)) {
    return reply(405, "METHOD_NOT_ALLOWED", "Method not allowed.");
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(request.method) && request.headers.get("origin") !== origin) {
    return reply(403, "CONTEXT_MISMATCH", "Staging writes require the frontend origin.");
  }
  if (Number(request.headers.get("content-length")) > 1_048_576) return reply(413, "VALIDATION_ERROR", "Request is too large.");
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer();
  if (body && body.byteLength > 1_048_576) return reply(413, "VALIDATION_ERROR", "Request is too large.");
  target.pathname = url.pathname;
  target.search = url.search;
  try {
    const response = await upstreamFetch(target, {
      method: request.method, body, redirect: "manual", signal: AbortSignal.timeout(25_000),
      headers: { Authorization: `Bearer ${token}`, Origin: origin,
        "Content-Type": request.headers.get("content-type") ?? "application/json" },
    });
    // Do not follow upstream redirects or forward cookies/provider credentials.
    if (response.status >= 300 && response.status < 400) return reply(503, "SERVICE_UNAVAILABLE", "Unexpected upstream redirect.");
    const headers = new Headers({ "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
    for (const key of ["content-type", "x-observation-cache", "x-observation-expires-at"]) {
      if (response.headers.has(key)) headers.set(key, response.headers.get(key));
    }
    return new Response(response.body, { status: response.status, headers });
  } catch {
    return reply(503, "SERVICE_UNAVAILABLE", "Backend is unavailable or waking up. No demonstration data was substituted.");
  }
}

export default { fetch: request => proxy(request) };
