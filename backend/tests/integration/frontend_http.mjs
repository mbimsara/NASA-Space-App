// Runs the UNMODIFIED frontend API facade through Vite against real HTTP.
// This is not a browser test. Dependencies come from the detached worktree.
import assert from 'node:assert/strict';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [frontend, mode] = process.argv.slice(2);
process.env.VITE_API_BASE_URL = 'http://localhost:8000/api/v1';
process.env.VITE_USE_FIXTURES = 'false';
const { createServer } = await import(pathToFileURL(path.join(frontend, 'node_modules/vite/dist/node/index.js')));
const server = await createServer({ root: frontend, envFile: false,
  server: { host: 'localhost', port: 5173, strictPort: true } });
const results = { mode, browser_e2e: false, checks: [] };
const pass = name => results.checks.push(name);
try {
  await server.listen();
  const { api, USE_FIXTURES } = await server.ssrLoadModule('/src/api/index.ts');
  assert.equal(USE_FIXTURES, false);
  assert.equal((await fetch('http://localhost:5173/')).status, 200);
  pass('Vite serves frontend at localhost:5173 in live API mode');
  const preflight = await fetch('http://127.0.0.1:8000/api/v1/farms', { method: 'OPTIONS', headers: {
    Origin: 'http://localhost:5173', 'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'content-type' } });
  assert.equal(preflight.status, 200);
  assert.equal(preflight.headers.get('access-control-allow-origin'), 'http://localhost:5173');
  pass('JSON CORS preflight');
  let farm = await api.createDemoFarm();
  assert.equal(farm.profile.data_kind, 'synthetic');
  assert.deepEqual(await api.getFarm(farm.id), farm);
  pass('create and retrieve farm');
  farm = await api.updateFarm(farm.id, 1, { ...farm.profile, name: 'Synthetic HTTP integration farm' });
  assert.equal(farm.input_version, 2);
  await assert.rejects(api.updateFarm(farm.id, 1, farm.profile), e => e.status === 409);
  pass('PATCH version increments and stale PATCH returns 409');
  let obs;
  try {
    obs = await api.getObservations(farm.id, '2024-02-28', '2024-03-01');
    assert.equal(obs.farm_id, farm.id);
    assert.equal(obs.input_version, 2);
    assert.ok(Array.isArray(obs.daily));
    assert.equal(obs.data_kind, mode === 'synthetic' ? 'synthetic' : 'modeled');
    pass('observation HTTP response, IDs, daily shape and provenance');
  } catch (e) {
    if (mode !== 'live' || ![0, 503].includes(e.status)) throw e;
    results.live_nasa = { status: e.status, code: e.code, outcome: 'unavailable; no synthetic fallback used' };
  }
  const body = { input_version: farm.input_version, observation_id: obs?.observation_id ?? null,
    seasons: 3, catalog_version: '0.1-draft', priority_weights: farm.profile.priority_weights };
  await assert.rejects(api.createRotation(farm.id, { ...body, observation_id: null }), e => e.status === 422);
  pass('null observation correctly returns typed 422 error');
  if (mode === 'synthetic') {
    body.catalog_version = 'integration-synthetic-v1';
    const empty = await api.createRotation(farm.id, body);
    assert.deepEqual(empty.candidates, []);
    assert.ok(empty.reasons.length);
    pass('count-only RotationPage body yields explained empty analysis');
    // Explicit test extension; current RotationPage does not send season_labels.
    const analysis = await api.createRotation(farm.id, { ...body, season_labels: ['maha', 'yala', 'maha'] });
    assert.equal(analysis.data_kind, 'synthetic');
    assert.equal(analysis.candidates.length, 1);
    const candidate = analysis.candidates[0];
    assert.equal(candidate.water_budget.deficit_mm, null);
    assert.equal(candidate.water_budget_range, null);
    const scenario = await api.createScenario(analysis.analysis_id, -20);
    assert.equal(scenario.baseline_analysis_id, analysis.analysis_id);
    assert.equal(scenario.hypothetical, true);
    assert.equal(scenario.candidates[0].candidate_id, candidate.candidate_id);
    pass('synthetic rotation and hypothetical scenario; null water preserved');
    for (const scenario_id of [undefined, scenario.scenario_id]) {
      const { plan_id } = await api.savePlan(farm.id, { analysis_id: analysis.analysis_id,
        scenario_id, candidate_id: candidate.candidate_id, expected_input_version: 2 });
      const plan = await api.getPlan(plan_id);
      assert.equal(plan.scenario_id, scenario_id ?? null);
      assert.equal(plan.input_snapshot.data_kind, 'synthetic');
      assert.equal(plan.candidate_snapshot.candidate_id, candidate.candidate_id);
    }
    pass('save and reopen baseline and scenario plans');
    const question = { farm_id: farm.id, analysis_id: analysis.analysis_id,
      scenario_id: scenario.scenario_id, candidate_id: candidate.candidate_id,
      language: 'en', message: 'Show full analysis' };
    const answer = await api.sendAssistantMessage(question);
    assert.equal(answer.role, 'assistant');
    assert.ok(answer.content.toLowerCase().includes('synthetic'));
    assert.ok(answer.content.toLowerCase().includes('hypothetical'));
    assert.ok(Array.isArray(answer.source_ids));
    for (const language of ['si', 'ta']) {
      await assert.rejects(api.sendAssistantMessage({ ...question, language }),
        e => e.status === 422 && e.code === 'UNSUPPORTED_LANGUAGE');
    }
    const english = await api.sendAssistantMessage(question);
    assert.equal(english.language, 'en');
    pass('assistant context, disclosures, si/ta rejection and English retry');
    const other = await api.createDemoFarm();
    await assert.rejects(api.sendAssistantMessage({ ...question, farm_id: other.id }), e => e.status === 409);
    pass('cross-farm context conflict');
  } else if (obs) {
    const analysis = await api.createRotation(farm.id, body);
    assert.deepEqual(analysis.candidates, []);
    results.live_nasa = { outcome: 'retrieved actual provider data; modeled provenance retained' };
    pass('production catalog empty analysis');
  }
  console.log(JSON.stringify(results, null, 2));
} finally { await server.close(); }
