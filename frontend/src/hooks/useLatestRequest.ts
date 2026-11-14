import { useEffect, useState } from "react";
import { createLatestRequest, type LatestRequest } from "../api/requestGuard";

/** One stale-response guard per component; cancels on unmount. */
export function useLatestRequest(): LatestRequest {
  const [guard] = useState(createLatestRequest);
  useEffect(() => () => guard.cancel(), [guard]);
  return guard;
}
