/**
 * API facade: switches between the live client and synthetic fixtures.
 * Owner: Shehani.
 *
 * Fixtures are the default until the backend is deployed. Set
 * VITE_USE_FIXTURES=false in frontend/.env.local to call VITE_API_BASE_URL.
 */
import * as live from "./client";
import * as fix from "./fixtures";

export const USE_FIXTURES = import.meta.env.VITE_USE_FIXTURES !== "false";

export const api = {
  createFarm: USE_FIXTURES ? fix.createFarmFixture : live.createFarm,
  createDemoFarm: USE_FIXTURES ? fix.createDemoFarmFixture : live.createDemoFarm,
  getFarm: USE_FIXTURES ? fix.getFarmFixture : live.getFarm,
  updateFarm: USE_FIXTURES ? fix.updateFarmFixture : live.updateFarm,
  getObservations: USE_FIXTURES ? fix.getObservationsFixture : live.getObservations,
  createRotation: USE_FIXTURES ? fix.createRotationFixture : live.createRotation,
  createScenario: USE_FIXTURES ? fix.createScenarioFixture : live.createScenario,
  sendAssistantMessage: USE_FIXTURES ? fix.sendAssistantMessageFixture : live.sendAssistantMessage,
  savePlan: USE_FIXTURES ? fix.savePlanFixture : live.savePlan,
  getPlan: USE_FIXTURES ? fix.getPlanFixture : live.getPlan,
} as const;

export { ApiClientError } from "./client";
