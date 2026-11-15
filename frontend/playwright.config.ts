import { defineConfig } from "@playwright/test";
import path from "node:path";

const python = process.env.AGROSPHERE_PYTHON ?? path.resolve("../backend/.venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const backendPort = process.env.E2E_BACKEND_PORT ?? "8000";
const frontendPort = process.env.E2E_FRONTEND_PORT ?? "5173";
const backendBaseURL = `http://localhost:${backendPort}/api/v1`;
const frontendBaseURL = `http://localhost:${frontendPort}`;

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  use: { baseURL: frontendBaseURL, browserName: "chromium",
    channel: process.env.PLAYWRIGHT_CHANNEL ?? (process.platform === "win32" ? "msedge" : undefined),
    trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: [
    { command: `"${python}" e2e/serve_backend.py`, url: `http://127.0.0.1:${backendPort}/api/v1/health`,
      env: { AGROSPHERE_E2E: "1", E2E_BACKEND_PORT: backendPort, E2E_FRONTEND_PORT: frontendPort }, reuseExistingServer: false, timeout: 30_000 },
    { command: `npm run dev -- --host localhost --port ${frontendPort} --strictPort`, url: frontendBaseURL,
      env: { VITE_USE_FIXTURES: process.env.E2E_FRONTEND_FIXTURES === "1" ? "true" : "false", VITE_API_BASE_URL: backendBaseURL },
      reuseExistingServer: false, timeout: 30_000 },
  ],
});
