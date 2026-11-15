/**
 * API facade: switches between the live client and synthetic fixtures.
 * Owner: Shehani.
 *
 * Live is the default. Only VITE_USE_FIXTURES=true enables synthetic demos.
 */
import * as live from "./client";
import * as fix from "./fixtures";
import { configuration } from "./config";

export const USE_FIXTURES = configuration.useFixtures;

export const api = {
  createFarm: USE_FIXTURES ? fix.createFarmFixture : live.createFarm,
  createDemoFarm: USE_FIXTURES ? fix.createDemoFarmFixture : live.createDemoFarm,
  getFarm: USE_FIXTURES ? fix.getFarmFixture : live.getFarm,
  updateFarm: USE_FIXTURES ? fix.updateFarmFixture : live.updateFarm,
  getObservations: USE_FIXTURES ? fix.getObservationsFixture : live.getObservations,
  getSoilMoisture: USE_FIXTURES ? fix.getSoilMoistureFixture : live.getSoilMoisture,
  getGpmPrecipitation: USE_FIXTURES ? fix.getGpmPrecipitationFixture : live.getGpmPrecipitation,
  getHlsVegetation: USE_FIXTURES ? fix.getHlsVegetationFixture : live.getHlsVegetation,
  createRotation: USE_FIXTURES ? fix.createRotationFixture : live.createRotation,
  createScenario: USE_FIXTURES ? fix.createScenarioFixture : live.createScenario,
  sendAssistantMessage: USE_FIXTURES ? fix.sendAssistantMessageFixture : live.sendAssistantMessage,
  savePlan: USE_FIXTURES ? fix.savePlanFixture : live.savePlan,
  getPlan: USE_FIXTURES ? fix.getPlanFixture : live.getPlan,
} as const;

export { ApiClientError } from "./client";
