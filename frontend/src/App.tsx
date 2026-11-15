/**
 * Routes for the core farmer journey.
 * farm setup → observations → rotations → scenario → assistant → saved plan
 * Owner: Shehani.
 *
 * Pages are lazy-loaded so the map (Leaflet) and charts (Recharts) download only
 * on the pages that use them, keeping the first load small on phones.
 */
import { lazy, Suspense, type ReactNode } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { FarmLayout } from "./components/layout/FarmLayout";
import { LoadingSpinner } from "./components/ui/LoadingSpinner";

const HomePage = lazy(() => import("./pages/HomePage").then((m) => ({ default: m.HomePage })));
const FarmFormPage = lazy(() => import("./pages/FarmFormPage").then((m) => ({ default: m.FarmFormPage })));
const ObservationsPage = lazy(() => import("./pages/ObservationsPage").then((m) => ({ default: m.ObservationsPage })));
const RotationPage = lazy(() => import("./pages/RotationPage").then((m) => ({ default: m.RotationPage })));
const ScenarioPage = lazy(() => import("./pages/ScenarioPage").then((m) => ({ default: m.ScenarioPage })));
const AssistantPage = lazy(() => import("./pages/AssistantPage").then((m) => ({ default: m.AssistantPage })));
const FinancePage = lazy(() => import("./pages/FinancePage").then((m) => ({ default: m.FinancePage })));
const SoilHealthPage = lazy(() => import("./pages/SoilHealthPage").then((m) => ({ default: m.SoilHealthPage })));
const ClimateTwinPage = lazy(() => import("./pages/ClimateTwinPage").then((m) => ({ default: m.ClimateTwinPage })));
const PlanPage = lazy(() => import("./pages/PlanPage").then((m) => ({ default: m.PlanPage })));
const CatalogPage = lazy(() => import("./pages/CatalogPage").then((m) => ({ default: m.CatalogPage })));
const RoadmapPage = lazy(() => import("./pages/RoadmapPage").then((m) => ({ default: m.RoadmapPage })));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })));

const page = (el: ReactNode) => <Suspense fallback={<LoadingSpinner />}>{el}</Suspense>;

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={page(<HomePage />)} />
          <Route path="farms/new" element={page(<FarmFormPage mode="new" />)} />
          <Route path="farms/:farmId" element={<FarmLayout />}>
            <Route index element={page(<ObservationsPage />)} />
            <Route path="edit" element={page(<FarmFormPage mode="edit" />)} />
            <Route path="rotations" element={page(<RotationPage />)} />
            <Route path="scenario" element={page(<ScenarioPage />)} />
            <Route path="assistant" element={page(<AssistantPage />)} />
            <Route path="finance" element={page(<FinancePage />)} />
            <Route path="soil-health" element={page(<SoilHealthPage />)} />
            <Route path="climate-twins" element={page(<ClimateTwinPage />)} />
          </Route>
          <Route path="plans/:planId" element={page(<PlanPage />)} />
          <Route path="catalog" element={page(<CatalogPage />)} />
          <Route path="roadmap" element={page(<RoadmapPage />)} />
          <Route path="*" element={page(<NotFoundPage />)} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
