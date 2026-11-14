/** Live is the default. Demo data requires an explicit build-time opt-in. */
export function apiConfiguration(fixtureFlag?: string, baseUrl?: string) {
  if (fixtureFlag !== undefined && fixtureFlag !== "true" && fixtureFlag !== "false") {
    throw new Error("VITE_USE_FIXTURES must be true (synthetic demo) or false (live API).");
  }
  const useFixtures = fixtureFlag === "true";
  const apiBaseUrl = (baseUrl ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
  if (!apiBaseUrl.trim()) throw new Error("VITE_API_BASE_URL must not be empty.");
  // Never hydrate demo results, plans or drafts into a live backend session.
  const namespace = useFixtures ? "fixture" : `live_${encodeURIComponent(apiBaseUrl)}`;
  return { useFixtures, apiBaseUrl, namespace };
}

export const configuration = apiConfiguration(import.meta.env.VITE_USE_FIXTURES, import.meta.env.VITE_API_BASE_URL);
export const APP_STORAGE_KEY = `agrosphere_app_${configuration.namespace}`;
export const PLAN_CACHE_KEY = `agrosphere_offline_plans_${configuration.namespace}`;
