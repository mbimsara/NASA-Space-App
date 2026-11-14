import { defineConfig } from "@playwright/test";
import path from "node:path";

const python = process.env.AGROSPHERE_PYTHON ?? path.resolve("../backend/.venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  use: { baseURL: "http://localhost:5173", browserName: "chromium",
    channel: process.env.PLAYWRIGHT_CHANNEL ?? (process.platform === "win32" ? "msedge" : undefined),
    trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: [
    { command: `"${python}" e2e/serve_backend.py`, url: "http://127.0.0.1:8000/api/v1/health",
      env: { AGROSPHERE_E2E: "1" }, reuseExistingServer: false, timeout: 30_000 },
    { command: "npm run dev -- --host localhost --port 5173 --strictPort", url: "http://localhost:5173",
      env: { VITE_USE_FIXTURES: process.env.E2E_FRONTEND_FIXTURES === "1" ? "true" : "false", VITE_API_BASE_URL: "http://localhost:8000/api/v1" },
      reuseExistingServer: false, timeout: 30_000 },
  ],
});
