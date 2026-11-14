// Actual unmodified frontend API facade + Axios over real HTTP; not browser E2E.
import assert from 'node:assert/strict';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [frontend] = process.argv.slice(2);
process.env.VITE_USE_FIXTURES = 'false';
process.env.VITE_API_BASE_URL = 'http://localhost:8000/api/v1';
const { createServer } = await import(pathToFileURL(path.join(frontend, 'node_modules/vite/dist/node/index.js')));
const server = await createServer({ root: frontend, envFile: false,
  server: { host: 'localhost', port: 5173, strictPort: true } });
const checks = [];
try {
  await server.listen();
  const { api, USE_FIXTURES } = await server.ssrLoadModule('/src/api/index.ts');
  const { CATALOG_VERSION } = await server.ssrLoadModule('/src/catalog/index.ts');
  assert.equal(USE_FIXTURES, false);
  assert.equal((await fetch('http://localhost:5173/')).status, 200);
  const cors = await fetch('http://localhost:8000/api/v1/farms', { method: 'OPTIONS', headers: {
    Origin: 'http://localhost:5173', 'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'content-type' } });
  assert.equal(cors.headers.get('access-control-allow-origin'), 'http://localhost:5173');
  checks.push('unmodified frontend live facade and CORS');
  let farm = await api.createDemoFarm();
  assert.equal(farm.profile.data_kind, 'synthetic');
  assert.deepEqual(await api.getFarm(farm.id), farm);
  farm = await api.updateFarm(farm.id, 1, farm.profile);
  await assert.rejects(api.updateFarm(farm.id, 1, farm.profile), e => e.status === 409);
  checks.push('farm create/read/PATCH and stale-version 409');
  const obs = await api.getObservations(farm.id, '2024-02-28', '2024-03-01');
  assert.equal(obs.data_kind, 'synthetic');
  assert.equal(obs.input_version, farm.input_version);
  const body = { input_version: farm.input_version, observation_id: obs.observation_id,
    seasons: 3, season_labels: ['maha', 'yala', 'maha'], catalog_version: CATALOG_VERSION,
    priority_weights: farm.profile.priority_weights };
  await assert.rejects(api.createRotation(farm.id, { ...body, observation_id: null }), e => e.status === 422);
  const { season_labels: omitted, ...countOnly } = body;
  assert.equal(omitted.length, 3);
  await assert.rejects(api.createRotation(farm.id, countOnly), e => e.status === 422);
  const analysis = await api.createRotation(farm.id, body);
  const candidate = analysis.candidates[0];
  assert.equal(candidate.water_budget.deficit_mm, null);
  assert.ok(candidate.water_budget_range.every(row => row.baseline_rainfall_mm === null));
  const scenario = await api.createScenario(analysis.analysis_id, -20);
  assert.equal(scenario.kind, 'hypothetical_rotation_scenario');
  assert.equal(scenario.baseline_analysis_id, analysis.analysis_id);
  assert.equal(scenario.candidates[0].candidate_id, candidate.candidate_id);
  assert.ok('score_change' in scenario.baseline_differences[candidate.candidate_id]);
  checks.push('canonical rotations/scenarios, required season identity and unknown water');
  const question = { farm_id: farm.id, analysis_id: analysis.analysis_id,
    scenario_id: scenario.scenario_id, candidate_id: candidate.candidate_id, language: 'en', message: 'Show full analysis' };
  const answer = await api.sendAssistantMessage(question);
  assert.equal(answer.role, 'assistant');
  assert.ok(answer.content.toLowerCase().includes('synthetic'));
  assert.ok(answer.content.toLowerCase().includes('hypothetical'));
  for (const language of ['si', 'ta']) {
    await assert.rejects(api.sendAssistantMessage({ ...question, language }),
      e => e.status === 422 && e.code === 'UNSUPPORTED_LANGUAGE');
  }
  checks.push('canonical assistant and English-only errors');
  for (const scenario_id of [undefined, scenario.scenario_id]) {
    const { plan_id } = await api.savePlan(farm.id, { analysis_id: analysis.analysis_id,
      scenario_id, candidate_id: candidate.candidate_id, expected_input_version: farm.input_version });
    const plan = await api.getPlan(plan_id);
    assert.equal(plan.scenario_id, scenario_id ?? null);
    assert.equal(plan.analysis_result_snapshot.analysis_id, analysis.analysis_id);
    assert.equal(plan.candidate_snapshot.candidate_id, candidate.candidate_id);
    assert.equal(plan.observation_snapshot.observation_id, obs.observation_id);
  }
  const excluded = await api.createFarm({ ...farm.profile, excluded_crop_ids: ['probe-crop'] });
  const excludedObs = await api.getObservations(excluded.id, '2024-02-28', '2024-03-01');
  const empty = await api.createRotation(excluded.id, { ...body, input_version: excluded.input_version,
    observation_id: excludedObs.observation_id });
  assert.deepEqual(empty.candidates, []);
  checks.push('baseline/scenario plans and legitimate zero-candidate analysis');
  console.log(JSON.stringify({ synthetic_only: true, browser_e2e: false, checks }, null, 2));
} finally { await server.close(); }
