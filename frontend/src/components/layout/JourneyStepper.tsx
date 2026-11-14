/**
 * JourneyStepper — Tharuka's "core journey" step tracker:
 * Farm setup → Overview → Crop plan → Climate test → AI review → Save & export.
 * A step is complete only when this farm actually has that result (farm saved,
 * observation loaded, analysis, scenario, saved plan). The current page is active.
 * Owner: Shehani. Design: Tharuka.
 */
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Icon } from "../ui/Icon";
import { selectCurrentAnalysis, selectCurrentScenario, useAppStore } from "../../hooks/useAppStore";
import { activeStepIndex, journeySteps } from "../../utils/journey";

export function JourneyStepper({ farmId }: { farmId: string }) {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const hasObservation = useAppStore((s) => s.latestObservation?.farmId === farmId);
  const hasAnalysis = useAppStore((s) => !!selectCurrentAnalysis(s));
  const hasScenario = useAppStore((s) => !!selectCurrentScenario(s));
  const planId = useAppStore((s) => s.recentPlans.find((p) => p.farmId === farmId)?.id ?? null);

  const steps = journeySteps({ farmId, hasObservation, hasAnalysis, hasScenario, planId });
  const active = activeStepIndex(steps, pathname);
  const next = active >= 0 && active < steps.length - 1 ? steps[active + 1] : null;

  return (
    <nav className="journey no-print" aria-label={t("journey.label")}>
      <ol>
        {steps.map((s, i) => {
          const state = i === active ? "active" : s.complete ? "complete" : "";
          return (
            <li key={s.key} className={state}>
              <Link to={s.to} aria-current={i === active ? "step" : undefined}>
                <span className="step-dot" aria-hidden="true">
                  {s.complete && i !== active ? <Icon name="check" /> : i + 1}
                </span>
                <span className="step-label">{t(`journey.${s.key}`)}</span>
                {s.complete && i !== active && <span className="sr-only"> ({t("journey.done")})</span>}
              </Link>
            </li>
          );
        })}
      </ol>
      {next && (
        <Link className="journey-next" to={next.to}>
          {t("journey.next", { step: t(`journey.${next.key}`) })} <Icon name="arrow" />
        </Link>
      )}
    </nav>
  );
}
