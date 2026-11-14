/**
 * FinancePage — illustrative cost / revenue / net ranges from explicit, dated local inputs.
 * Owner: Shehani (implementation). Formulas pending Bhagya's approval; inputs researched by Tharuka.
 */
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../hooks/useAppStore";
import {
  calculateFinance,
  roundMoney,
  type CostCategory,
  type DatedSource,
  type NullableRange,
  type Range,
} from "../finance/calculator";
import { todayIso } from "../utils/validation";

const toNum = (s: string) => (s.trim() === "" ? null : Number(s));

function RangeInputs({
  id,
  label,
  value,
  onChange,
  error,
}: {
  id: string;
  label: string;
  value: NullableRange;
  onChange: (r: NullableRange) => void;
  error?: string;
}) {
  const { t } = useTranslation();
  return (
    <fieldset style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>
      <legend style={{ fontWeight: 600, fontSize: "0.9rem" }}>{label}</legend>
      <div className="row" style={{ flexWrap: "nowrap" }}>
        <div className="field">
          <label htmlFor={`${id}-low`} className="muted" style={{ fontWeight: 400 }}>
            {t("financial.low")}
          </label>
          <input
            id={`${id}-low`}
            type="number"
            min="0"
            step="any"
            value={value.low ?? ""}
            placeholder={t("common.unknown")}
            onChange={(e) => onChange({ ...value, low: toNum(e.target.value) })}
            aria-invalid={!!error}
          />
        </div>
        <div className="field">
          <label htmlFor={`${id}-high`} className="muted" style={{ fontWeight: 400 }}>
            {t("financial.high")}
          </label>
          <input
            id={`${id}-high`}
            type="number"
            min="0"
            step="any"
            value={value.high ?? ""}
            placeholder={t("common.unknown")}
            onChange={(e) => onChange({ ...value, high: toNum(e.target.value) })}
            aria-invalid={!!error}
          />
        </div>
      </div>
      {error && (
        <span className="field-error" role="alert">
          {error}
        </span>
      )}
    </fieldset>
  );
}

export function FinancePage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;

  const [currency, setCurrency] = useState("LKR");
  const [cropLabel, setCropLabel] = useState("");
  const [costs, setCosts] = useState<CostCategory[]>([
    { name: "Seed", per_ha: { low: null, high: null } },
    { name: "Fertilizer", per_ha: { low: null, high: null } },
    { name: "Labour", per_ha: { low: null, high: null } },
  ]);
  const [yieldRange, setYieldRange] = useState<NullableRange>({ low: null, high: null });
  const [price, setPrice] = useState<NullableRange>({ low: null, high: null });
  const [sources, setSources] = useState<DatedSource[]>([{ label: "", date: todayIso() }]);

  const outcome = useMemo(
    () =>
      calculateFinance({
        currency,
        area: { value: farm.profile.area_ha, unit: "ha" },
        crop_label: cropLabel,
        costs,
        yield_kg_per_ha: yieldRange,
        price_per_kg: price,
        sources,
      }),
    [currency, farm.profile.area_ha, cropLabel, costs, yieldRange, price, sources],
  );
  const e = outcome.errors;
  const r = outcome.result;
  const money = (x: Range | null) =>
    x === null
      ? t("common.unknown")
      : `${currency} ${roundMoney(x.low).toLocaleString()} – ${roundMoney(x.high).toLocaleString()}`;

  return (
    <div className="page">
      <h1>{t("financial.title")}</h1>
      <div className="notice notice-warn" role="note">
        {t("financial.awaitsApproval")}
      </div>

      <div className="card grid-2">
        <div className="field">
          <label htmlFor="fin-crop">{t("financial.crop")}</label>
          <input id="fin-crop" value={cropLabel} onChange={(ev) => setCropLabel(ev.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="fin-currency">{t("financial.currency")}</label>
          <input
            id="fin-currency"
            value={currency}
            maxLength={3}
            onChange={(ev) => setCurrency(ev.target.value.toUpperCase())}
            aria-invalid={!!e.currency}
          />
          {e.currency && <span className="field-error">{e.currency}</span>}
        </div>
        <div className="field">
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{t("farm.area")}</span>
          <span>
            {farm.profile.area_ha} ha <span className="muted">({t("financial.areaFromFarm")})</span>
          </span>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>{t("financial.costs")}</h2>
        <p className="muted">{t("financial.costsHelp", { currency })}</p>
        {costs.map((c, i) => (
          <div key={i} className="grid-2" style={{ marginBottom: 12, alignItems: "end" }}>
            <div className="field">
              <label htmlFor={`cost-name-${i}`}>{t("financial.category")}</label>
              <input
                id={`cost-name-${i}`}
                value={c.name}
                onChange={(ev) => setCosts((cs) => cs.map((x, j) => (j === i ? { ...x, name: ev.target.value } : x)))}
                aria-invalid={!!e[`costs.${i}.name`]}
              />
            </div>
            <RangeInputs
              id={`cost-${i}`}
              label={`${c.name || t("financial.category")} (${currency}/ha)`}
              value={c.per_ha}
              onChange={(per_ha) => setCosts((cs) => cs.map((x, j) => (j === i ? { ...x, per_ha } : x)))}
              error={e[`costs.${i}`] ?? e[`costs.${i}.low`] ?? e[`costs.${i}.high`] ?? e[`costs.${i}.name`]}
            />
            <button type="button" className="btn btn-danger" onClick={() => setCosts((cs) => cs.filter((_, j) => j !== i))}>
              {t("common.remove")}
            </button>
          </div>
        ))}
        <button
          type="button"
          className="btn"
          onClick={() => setCosts((cs) => [...cs, { name: "", per_ha: { low: null, high: null } }])}
        >
          + {t("financial.addCost")}
        </button>
      </div>

      <div className="card grid-2">
        <RangeInputs
          id="yield"
          label={t("financial.yield")}
          value={yieldRange}
          onChange={setYieldRange}
          error={e.yield_kg_per_ha ?? e["yield_kg_per_ha.low"] ?? e["yield_kg_per_ha.high"]}
        />
        <RangeInputs
          id="price"
          label={t("financial.price", { currency })}
          value={price}
          onChange={setPrice}
          error={e.price_per_kg ?? e["price_per_kg.low"] ?? e["price_per_kg.high"]}
        />
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>{t("financial.sources")}</h2>
        <p className="muted">{t("financial.sourcesHelp")}</p>
        {e.sources && <p className="field-error">{e.sources}</p>}
        {sources.map((s, i) => (
          <div key={i} className="grid-2" style={{ marginBottom: 8, alignItems: "end" }}>
            <div className="field">
              <label htmlFor={`src-label-${i}`}>{t("financial.sourceLabel")}</label>
              <input
                id={`src-label-${i}`}
                value={s.label}
                onChange={(ev) => setSources((ss) => ss.map((x, j) => (j === i ? { ...x, label: ev.target.value } : x)))}
                aria-invalid={!!e[`sources.${i}.label`]}
              />
              {e[`sources.${i}.label`] && <span className="field-error">{e[`sources.${i}.label`]}</span>}
            </div>
            <div className="field">
              <label htmlFor={`src-date-${i}`}>{t("financial.sourceDate")}</label>
              <input
                id={`src-date-${i}`}
                type="date"
                value={s.date}
                max={todayIso()}
                onChange={(ev) => setSources((ss) => ss.map((x, j) => (j === i ? { ...x, date: ev.target.value } : x)))}
                aria-invalid={!!e[`sources.${i}.date`]}
              />
            </div>
            <button type="button" className="btn btn-danger" onClick={() => setSources((ss) => ss.filter((_, j) => j !== i))}>
              {t("common.remove")}
            </button>
          </div>
        ))}
        <button type="button" className="btn" onClick={() => setSources((ss) => [...ss, { label: "", date: todayIso() }])}>
          + {t("financial.addSource")}
        </button>
      </div>

      <section className="card" aria-live="polite" aria-labelledby="fin-results">
        <h2 id="fin-results" style={{ marginTop: 0 }}>
          {t("financial.results")}
        </h2>
        {!outcome.ok && <p className="muted">{t("financial.fixInputs")}</p>}
        {r && (
          <>
            <table className="data">
              <tbody>
                <tr>
                  <th scope="row">{t("financial.costRange")}</th>
                  <td>{money(r.cost)}</td>
                </tr>
                <tr>
                  <th scope="row">{t("financial.revenueRange")}</th>
                  <td>{money(r.revenue)}</td>
                </tr>
                <tr>
                  <th scope="row">{t("financial.netRange")}</th>
                  <td>
                    <strong>{money(r.net)}</strong>
                  </td>
                </tr>
                <tr>
                  <th scope="row">{t("financial.breakEven")}</th>
                  <td>
                    {r.break_even_price_per_kg === null
                      ? t("common.unknown")
                      : `${currency} ${r.break_even_price_per_kg.low.toFixed(2)} – ${r.break_even_price_per_kg.high.toFixed(2)} / kg`}
                  </td>
                </tr>
              </tbody>
            </table>
            {r.unknowns.length > 0 && (
              <ul className="muted">
                {r.unknowns.map((u, i) => (
                  <li key={i}>{u}</li>
                ))}
              </ul>
            )}
            <details className="muted">
              <summary style={{ cursor: "pointer" }}>{t("common.assumptions")}</summary>
              <ul>
                {r.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
                {sources.map((s, i) => (
                  <li key={`s${i}`}>
                    {t("common.source")}: {s.label} ({s.date})
                  </li>
                ))}
              </ul>
            </details>
          </>
        )}
        <p className="muted">{t("financial.disclaimer")}</p>
      </section>
    </div>
  );
}
