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
import { useOnlineStatus } from "../../hooks/useOnlineStatus";
import { clearPendingFarmEdit, pendingFarmEdit } from "../../utils/offlineFarmQueue";
import { ErrorMessage } from "../ui/ErrorMessage";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { JourneyStepper } from "./JourneyStepper";

export function FarmLayout() {
  const { farmId } = useParams<{ farmId: string }>();
  const farm = useAppStore((s) => s.farm);
  const setFarm = useAppStore((s) => s.setFarm);
  const guard = useLatestRequest();
  const online = useOnlineStatus();
  const [error, setError] = useState<unknown>(null);
  const [syncError, setSyncError] = useState<unknown>(null);
  const [hasPending, setHasPending] = useState(false);

  const load = useCallback(() => {
    if (!farmId) return;
    const ticket = guard.next();
    setError(null); setSyncError(null);
    const pending = pendingFarmEdit(farmId);
    setHasPending(!!pending);
    if (!online && pending) {
      setFarm({ id: farmId, input_version: pending.expectedInputVersion, profile: pending.profile });
      return;
    }
    const synchronize = pending && online
      ? api.updateFarm(farmId, pending.expectedInputVersion, pending.profile, ticket.signal)
          .then((env) => { clearPendingFarmEdit(farmId); setHasPending(false); return env; })
          .catch((err) => { setSyncError(err); return api.getFarm(farmId, ticket.signal); })
      : api.getFarm(farmId, ticket.signal);
    synchronize
      .then((env) => {
        if (ticket.isCurrent()) setFarm(env);
      })
      .catch((err) => {
        if (ticket.isCurrent() && !isAbortError(err)) setError(err);
      });
  }, [farmId, guard, online, setFarm]);

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
      {hasPending && <div className="notice notice-warn" role="status" style={{ margin: "12px 24px" }}>
        {online ? "This device has a queued farm edit that has not synced." : "Showing a farm edit saved on this device. It will sync when the API is reachable."}
        {syncError != null && <div className="row" style={{ marginTop: 8 }}>
          <span>Automatic sync failed, usually because the server farm changed.</span>
          <button type="button" className="btn" onClick={load}>Retry sync</button>
          <button type="button" className="btn btn-danger" onClick={() => { clearPendingFarmEdit(farm.id); setHasPending(false); load(); }}>Discard queued edit</button>
        </div>}
      </div>}
      <JourneyStepper farmId={farm.id} />
      <Outlet />
    </>
  );
}
