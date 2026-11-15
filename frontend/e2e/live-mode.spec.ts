import { expect, test, type Page } from "@playwright/test";

const backendBaseURL = `http://localhost:${process.env.E2E_BACKEND_PORT ?? "8000"}/api/v1`;
const liveNASA = process.env.E2E_LIVE_NASA === "1";
const emptyCatalog = process.env.E2E_CATALOG === "empty";
const fixtureMode = process.env.E2E_FRONTEND_FIXTURES === "1";

async function createFarm(page: Page) {
  await page.goto("/farms/new");
  await page.locator("#farm-name").fill("Browser test farm — explicitly synthetic test entry");
  const created = page.waitForResponse(r => r.url().endsWith("/api/v1/farms") && r.request().method() === "POST");
  await page.locator("form").getByRole("button", { name: /save/i }).click();
  const response = await created;
  expect(response.status()).toBe(201);
  const farm = await response.json();
  await expect(page).toHaveURL(new RegExp(`/farms/${farm.id}$`));
  return farm;
}

async function observations(page: Page) {
  await page.locator("#obs-start").fill("2024-02-28");
  await page.locator("#obs-end").fill("2024-03-01");
  const loaded = page.waitForResponse(r => /\/observations\?/.test(r.url()) && r.url().includes("2024-02-28"));
  await page.getByRole("button", { name: /^load/i }).click();
  const response = await loaded;
  expect(response.status()).toBe(200);
  return response.json();
}

test("complete browser journey over real FastAPI HTTP (explicit synthetic server inputs)", async ({ page }) => {
  test.skip(liveNASA || emptyCatalog || fixtureMode);
  const farm = await createFarm(page);
  const obs = await observations(page);
  expect(obs.data_kind).toBe("synthetic");
  await page.goto(`/farms/${farm.id}/rotations`);
  await page.getByRole("radio", { name: /drought/i }).check();
  const generated = page.waitForResponse(r => r.url().endsWith("/rotations") && r.request().method() === "POST");
  await page.getByRole("button", { name: /generate|run rotation/i }).click();
  const response = await generated;
  expect(response.status()).toBe(201);
  const analysis = await response.json();
  expect(analysis.observation_id).toBe(obs.observation_id);
  expect(analysis.planning_mode).toBe("drought_recovery");
  expect(analysis.candidates[0].planning_evidence.mode).toBe("drought_recovery");
  expect(analysis.candidates).toHaveLength(1);
  await expect(page.getByText(/planning-mode evidence/i)).toBeVisible();
  await expect(page.getByText("Synthetic browser crop", { exact: false }).first()).toBeVisible();
  await page.goto(`/farms/${farm.id}/scenario`);
  const scenarioResponse = page.waitForResponse(r => r.url().endsWith("/scenarios") && r.request().method() === "POST");
  await page.getByRole("button", { name: /run|apply/i }).click();
  const scenario = await (await scenarioResponse).json();
  expect(scenario.baseline_analysis_id).toBe(analysis.analysis_id);
  await page.goto(`/farms/${farm.id}/assistant`);
  await page.locator("#assistant-input").fill("Show full analysis");
  const answered = page.waitForResponse(r => r.url().endsWith("/assistant/messages"));
  await page.getByRole("button", { name: /^send/i }).click();
  expect((await answered).status()).toBe(200);
  await expect(page.getByRole("log")).toContainText(/synthetic/i);
  await page.goto(`/farms/${farm.id}/scenario`);
  const saved = page.waitForResponse(r => r.url().endsWith("/plans") && r.request().method() === "POST");
  await page.getByRole("button", { name: /save.*plan/i }).click();
  const { plan_id } = await (await saved).json();
  await expect(page).toHaveURL(`/plans/${plan_id}`);
  await expect(page.getByText("Synthetic browser crop", { exact: false }).first()).toBeVisible();
  await page.reload();
  await expect(page.getByText("Synthetic browser crop", { exact: false }).first()).toBeVisible();
  await page.goto(`/farms/${farm.id}/weed-shield`);
  await expect(page.getByRole("heading", { name: /field-photo triage/i })).toBeVisible();
  await expect(page.getByText(/not a trained weed detector/i)).toBeVisible();
  await expect(page.getByText(/cannot identify individual weeds/i)).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("weedshield-desktop.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".app-main")).toHaveCSS("margin-left", "0px");
  await page.screenshot({ path: test.info().outputPath("weedshield-mobile.png"), fullPage: true });
});

test("missing observations disable generation; backend keeps 404/409/422 semantics", async ({ page, request }) => {
  test.skip(liveNASA || emptyCatalog || fixtureMode);
  const farm = await createFarm(page);
  // Clear only this browser's selected observation to exercise the live prerequisite.
  await page.evaluate(() => {
    for (const key of Object.keys(localStorage).filter(k => k.startsWith("agrosphere_app_"))) {
      const stored = JSON.parse(localStorage.getItem(key)!);
      stored.state.latestObservation = null;
      localStorage.setItem(key, JSON.stringify(stored));
    }
  });
  await page.goto(`/farms/${farm.id}/rotations`);
  await expect(page.getByRole("button", { name: /generate|run rotation/i })).toBeDisabled();
  expect((await request.get(`${backendBaseURL}/plans/missing`)).status()).toBe(404);
  expect((await request.patch(`${backendBaseURL}/farms/${farm.id}`, {
    data: { expected_input_version: 999, profile: farm.profile },
  })).status()).toBe(409);
  expect((await request.post(`${backendBaseURL}/farms/${farm.id}/rotations`, { data: {
    input_version: 1, observation_id: null, seasons: 3, season_labels: ["maha", "yala", "maha"],
    catalog_version: "invalid-test-version", priority_weights: farm.profile.priority_weights,
  } })).status()).toBe(422);
});

test("network and HTTP errors never turn into demo farms or cached fake success", async ({ page }) => {
  test.skip(liveNASA || emptyCatalog || fixtureMode);
  for (const status of [404, 409, 422, 503]) {
    await page.route("**/api/v1/farms/missing", route => route.fulfill({ status, contentType: "application/json",
      body: JSON.stringify({ error: { code: "TEST_ERROR", message: `Isolated HTTP error ${status}` } }) }));
    await page.goto("/farms/missing");
    await expect(page.getByRole("alert")).toContainText(`Isolated HTTP error ${status}`);
    await page.unroute("**/api/v1/farms/missing");
  }
  await page.route("**/api/v1/farms/missing", route => route.abort("connectionrefused"));
  await page.goto("/farms/missing");
  await expect(page.getByRole("alert")).toContainText(/network|connection/i);
});

test("empty catalog remains an honest empty analysis; scenarios and assistant still work", async ({ page }) => {
  test.skip(!emptyCatalog || liveNASA || fixtureMode);
  const farm = await createFarm(page);
  await observations(page);
  await page.goto(`/farms/${farm.id}/rotations`);
  const generated = page.waitForResponse(r => r.url().endsWith("/rotations") && r.request().method() === "POST");
  await page.getByRole("button", { name: /generate|run rotation/i }).click();
  const analysis = await (await generated).json();
  expect(analysis.candidates).toEqual([]);
  await expect(page.getByText(/no feasible rotation plans/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /save.*plan/i })).toHaveCount(0);
  await page.goto(`/farms/${farm.id}/scenario`);
  await page.getByRole("button", { name: /run|apply/i }).click();
  await expect(page.getByText(/no feasible rotation plans/i)).toBeVisible();
  await page.goto(`/farms/${farm.id}/assistant`);
  await page.locator("#assistant-input").fill("Explain the farm area");
  const answered = page.waitForResponse(r => r.url().endsWith("/assistant/messages"));
  await page.getByRole("button", { name: /^send/i }).click();
  expect((await answered).status()).toBe(200);
});

test("actual live NASA request uses the production catalog without fixture substitution", async ({ page }) => {
  test.skip(!liveNASA || fixtureMode);
  const farm = await createFarm(page);
  const obs = await observations(page);
  expect(obs.data_kind).toBe("modeled");
  expect(obs.source_url).not.toContain("example.invalid");
  await page.goto(`/farms/${farm.id}/rotations`);
  const generated = page.waitForResponse(r => r.url().endsWith("/rotations") && r.request().method() === "POST");
  await page.getByRole("button", { name: /generate|run rotation/i }).click();
  expect((await (await generated).json()).candidates).toEqual([]);
});

test("Sinhala/Tamil return 422 and the existing UI retries in English; stale context returns 409", async ({ page, request }) => {
  test.skip(liveNASA || emptyCatalog || fixtureMode);
  const farm = await createFarm(page);
  await observations(page);
  await page.goto(`/farms/${farm.id}/rotations`);
  const generated = page.waitForResponse(r => r.url().endsWith("/rotations") && r.request().method() === "POST");
  await page.getByRole("button", { name: /generate|run rotation/i }).click();
  expect((await generated).status()).toBe(201);
  await page.goto(`/farms/${farm.id}/assistant`);
  for (const language of ["si", "ta"]) {
    await page.locator("#lang-select").selectOption(language);
    await page.locator("#assistant-input").fill("Explain the farm area");
    const rejected = page.waitForResponse(r => r.url().endsWith("/assistant/messages"));
    await page.locator("#assistant-input").press("Enter");
    const response = await rejected;
    expect(response.status()).toBe(422);
    expect((await response.json()).error.code).toBe("UNSUPPORTED_LANGUAGE");
    const retried = page.waitForResponse(r => r.url().endsWith("/assistant/messages"));
    await page.getByTestId("assistant-english-retry").click();
    expect((await retried).status()).toBe(200);
  }
  await page.locator("#lang-select").selectOption("en");
  const edited = await request.patch(`${backendBaseURL}/farms/${farm.id}`, {
    data: { expected_input_version: farm.input_version, profile: { ...farm.profile, name: "Concurrent farm edit" } },
  });
  expect(edited.status()).toBe(200);
  await page.locator("#assistant-input").fill("Explain the farm area");
  const conflicted = page.waitForResponse(r => r.url().endsWith("/assistant/messages"));
  await page.locator("#assistant-input").press("Enter");
  expect((await conflicted).status()).toBe(409);
  await expect(page.getByRole("alert")).toBeVisible();
  await page.goto(`/farms/${farm.id}/rotations`);
  await expect(page.getByRole("button", { name: /generate|re-run|rerun|run rotation/i })).toBeDisabled();
});

test("explicit fixture mode stays labeled and makes no FastAPI requests", async ({ page }) => {
  test.skip(!fixtureMode);
  const apiCalls: string[] = [];
  page.on("request", request => {
    if (request.url().startsWith(backendBaseURL)) apiCalls.push(request.url());
  });
  await page.goto("/");
  await expect(page.locator(".fixture-ribbon")).toBeVisible();
  await page.getByRole("button", { name: "View demo" }).click();
  await expect(page).toHaveURL(/\/farms\//);
  await expect(page.locator(".fixture-ribbon")).toBeVisible();
  await expect(page.getByText(/synthetic/i).first()).toBeVisible();
  expect(apiCalls).toEqual([]);
});
