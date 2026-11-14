/**
 * FarmLayout — loads the farm named in the URL, makes it the selected farm,
 * and renders farm-scoped navigation. Child pages read the farm from the store,
 * so every screen under /farms/:farmId always shows that farm's data only.
 * Owner: Shehani.
 */
import { useCallback, useEffect, useState } from "react";
import { Outlet, useParams } from "react-router-dom";
import { api } from "../../api";
import { isAbortError } from "../../api/requestGuard";
import { useAppStore } from "../../hooks/useAppStore";
import { useLatestRequest } from "../../hooks/useLatestRequest";
import { ErrorMessage } from "../ui/ErrorMessage";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { JourneyStepper } from "./JourneyStepper";

export function FarmLayout() {
  const { farmId } = useParams<{ farmId: string }>();
  const farm = useAppStore((s) => s.farm);
  const setFarm = useAppStore((s) => s.setFarm);
  const guard = useLatestRequest();
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(() => {
    if (!farmId) return;
    const ticket = guard.next();
    setError(null);
    api
      .getFarm(farmId, ticket.signal)
      .then((env) => {
        if (ticket.isCurrent()) setFarm(env);
      })
      .catch((err) => {
        if (ticket.isCurrent() && !isAbortError(err)) setError(err);
      });
  }, [farmId, guard, setFarm]);

  useEffect(() => {
    // Loading the URL-scoped farm is the intended synchronization boundary.
    // oxlint-disable-next-line react/set-state-in-effect
    load();
  }, [load]);

  const ready = farm && farm.id === farmId;

  if (error) {
    return (
      <div className="page">
        <ErrorMessage error={error} onRetry={load} />
      </div>
    );
  }
  if (!ready) return <LoadingSpinner />;

  return (
    <>
      <JourneyStepper farmId={farm.id} />
      <Outlet />
    </>
  );
}
