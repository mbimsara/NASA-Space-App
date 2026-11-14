/**
 * Routes for the core farmer journey.
 * farm setup → observations → rotations → scenario → assistant → saved plan
 * Owner: Shehani.
 */
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { FarmLayout } from "./components/layout/FarmLayout";
import { HomePage } from "./pages/HomePage";
import { FarmFormPage } from "./pages/FarmFormPage";
import { ObservationsPage } from "./pages/ObservationsPage";
import { RotationPage } from "./pages/RotationPage";
import { ScenarioPage } from "./pages/ScenarioPage";
import { AssistantPage } from "./pages/AssistantPage";
import { FinancePage } from "./pages/FinancePage";
import { PlanPage } from "./pages/PlanPage";
import { CatalogPage } from "./pages/CatalogPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="farms/new" element={<FarmFormPage mode="new" />} />
          <Route path="farms/:farmId" element={<FarmLayout />}>
            <Route index element={<ObservationsPage />} />
            <Route path="edit" element={<FarmFormPage mode="edit" />} />
            <Route path="rotations" element={<RotationPage />} />
            <Route path="scenario" element={<ScenarioPage />} />
            <Route path="assistant" element={<AssistantPage />} />
            <Route path="finance" element={<FinancePage />} />
          </Route>
          <Route path="plans/:planId" element={<PlanPage />} />
          <Route path="catalog" element={<CatalogPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
