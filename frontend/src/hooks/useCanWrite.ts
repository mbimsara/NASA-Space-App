import { USE_FIXTURES } from "../api";
import { useOnlineStatus } from "./useOnlineStatus";

/**
 * Whether server writes/computations may be attempted. Offline writes are not
 * queued until a sync/conflict policy is agreed with Dulanjaya, so live mode
 * blocks them while offline. Fixture mode is local and unaffected.
 */
export function useCanWrite(): boolean {
  const online = useOnlineStatus();
  return online || USE_FIXTURES;
}
