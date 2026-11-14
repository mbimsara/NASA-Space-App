/**
 * FinancePage — illustrative cost / revenue / net ranges from explicit inputs,
 * each linked to its own source record (URL or document reference).
 * Owner: Shehani. Specification v0.1: docs/FINANCIAL_SPECIFICATION.md (Bhagya).
 */
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../hooks/useAppStore";
import {
  FINANCE_SPEC_REFERENCE,
  FINANCE_SPEC_VERSION,
  STANDARD_COST_CATEGORIES,
  calculateFinance,
  roundMoney,
  type CostCategory,
  type NullableRange,
  type Range,
  type SourceKind,
  type SourceRecord,
} from "../finance/calculator";
import { todayIso } from "../utils/validation";

const toNum = (s: string) => (s.trim() === "" ? null : Number(s));
const KINDS: SourceKind[] = ["farmer_entered", "observed", "researched", "synthetic"];

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
        {(["low", "high"] as const).map((k) => (
          <div className="field" key={k}>
            <label htmlFor={`${id}-${k}`} className="muted" style={{ fontWeight: 400 }}>
              {t(`financial.${k}`)}
            </label>
            <input
              id={`${id}-${k}`}
              type="number"
              min="0"
              step="any"
              value={value[k] ?? ""}
              placeholder={t("common.unknown")}
              onChange={(e) => onChange({ ...value, [k]: toNum(e.target.value) })}
              aria-invalid={!!error}
            />
          </div>
        ))}
      </div>
      {error && (
        <span className="field-error" role="alert">
          {error}
        </span>
      )}
    </fieldset>
  );
}

/** Checkbox group linking an input to the source records that support it. */
function SourcePicker({
  id,
  sources,
  selected,
  onChange,
  error,
}: {
  id: string;
  sources: SourceRecord[];
  selected: string[];
  onChange: (ids: string[]) => void;
  error?: string;
}) {
  const { t } = useTranslation();
  return (
    <fieldset style={{ border: 0, padding: 0, margin: "6px 0 0", minWidth: 0 }}>
      <legend className="muted" style={{ fontSize: "0.8rem" }}>
        {t("financial.supportedBy")}
      </legend>
      {sources.length === 0 ? (
        <span className="muted" style={{ fontSize: "0.8rem" }}>
          {t("financial.noSourcesYet")}
        </span>
      ) : (
        <div className="row" style={{ gap: 8 }}>
          {sources.map((s) => (
            <label key={s.id} style={{ fontSize: "0.8rem", fontWeight: 400 }}>
              <input
                type="checkbox"
                id={`${id}-src-${s.id}`}
                checked={selected.includes(s.id)}
                onChange={(e) =>
                  onChange(e.target.checked ? [...selected, s.id] : selected.filter((x) => x !== s.id))
                }
                style={{ width: "auto", marginRight: 4 }}
              />
              {s.id}
              {s.label ? `: ${s.label}` : ""}
            </label>
          ))}
        </div>
      )}
      {error && (
        <span className="field-error" role="alert" style={{ display: "block" }}>
          {error}
        </span>
      )}
    </fieldset>
  );
}

const emptyRange = (): NullableRange => ({ low: null, high: null });

export function FinancePage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;

  const [currency, setCurrency] = useState("LKR");
  const [cropLabel, setCropLabel] = useState("");
  const [costs, setCosts] = useState<CostCategory[]>(() =>
    STANDARD_COST_CATEGORIES.map((c) => ({ key: c.key, name: c.name, per_ha: emptyRange(), source_ids: [] })),
  );
  const [yieldRange, setYieldRange] = useState<NullableRange>(emptyRange);
  const [yieldSources, setYieldSources] = useState<string[]>([]);
  const [price, setPrice] = useState<NullableRange>(emptyRange);
  const [priceSources, setPriceSources] = useState<string[]>([]);
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [nextSourceNo, setNextSourceNo] = useState(1);

  const outcome = useMemo(
    () =>
      calculateFinance({
        currency,
        area: { value: farm.profile.area_ha, unit: "ha" },
        crop_label: cropLabel,
        costs,
        yield_kg_per_ha: yieldRange,
        yield_source_ids: yieldSources,
        price_per_kg: price,
        price_source_ids: priceSources,
        sources,
      }),
    [currency, farm.profile.area_ha, cropLabel, costs, yieldRange, yieldSources, price, priceSources, sources],
  );
  const e = outcome.errors;
  const r = outcome.result;
  const money = (x: Range | null) =>
    x === null
      ? t("common.unknown")
      : `${currency} ${roundMoney(x.low).toLocaleString()} – ${roundMoney(x.high).toLocaleString()}`;

  const addSource = () => {
    const id = `S${nextSourceNo}`;
    setNextSourceNo((n) => n + 1);
    const today = todayIso();
    setSources((ss) => [
      ...ss,
      {
        id,
        label: "",
        reference: "",
        quoted_on: today,
        accessed_on: today,
        area: "",
        crop_variety_grade: cropLabel,
        unit_period: "",
        kind: "researched",
      },
    ]);
  };

  const removeSource = (id: string) => {
    setSources((ss) => ss.filter((s) => s.id !== id));
    setCosts((cs) => cs.map((c) => ({ ...c, source_ids: c.source_ids.filter((x) => x !== id) })));
    setYieldSources((ids) => ids.filter((x) => x !== id));
    setPriceSources((ids) => ids.filter((x) => x !== id));
  };

  const updateSource = (i: number, patch: Partial<SourceRecord>) =>
    setSources((ss) => ss.map((s, j) => (j === i ? { ...s, ...patch } : s)));

  const sourceFields: { k: keyof SourceRecord; type: string }[] = [
    { k: "label", type: "text" },
    { k: "reference", type: "text" },
    { k: "quoted_on", type: "date" },
    { k: "accessed_on", type: "date" },
    { k: "area", type: "text" },
    { k: "crop_variety_grade", type: "text" },
    { k: "unit_period", type: "text" },
  ];

  return (
    <div className="page">
      <h1>{t("financial.title")}</h1>
      <div className="notice notice-info" role="note">
        <strong>{t("financial.specStatus", { version: FINANCE_SPEC_VERSION })}</strong>{" "}
        {t("financial.specReference", { ref: FINANCE_SPEC_REFERENCE })}
        <div>{t("financial.dataPending")}</div>
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
        <h2 style={{ marginTop: 0 }}>{t("financial.sources")}</h2>
        <p className="muted">{t("financial.sourcesHelp")}</p>
        {sources.map((s, i) => (
          <fieldset key={s.id} className="card" style={{ margin: "0 0 12px", background: "var(--surface-alt)" }}>
            <legend style={{ fontWeight: 600 }}>
              {t("financial.sourceId", { id: s.id })}
            </legend>
            <div className="grid-2">
              {sourceFields.map(({ k, type }) => {
                const errKey = `sources.${i}.${k}`;
                return (
                  <div className="field" key={k}>
                    <label htmlFor={`src-${s.id}-${k}`}>{t(`financial.src_${k}`)}</label>
                    <input
                      id={`src-${s.id}-${k}`}
                      type={type}
                      value={s[k] as string}
                      max={type === "date" ? todayIso() : undefined}
                      onChange={(ev) => updateSource(i, { [k]: ev.target.value })}
                      aria-invalid={!!e[errKey]}
                      aria-describedby={e[errKey] ? `${errKey}-error` : undefined}
                    />
                    {e[errKey] && (
                      <span id={`${errKey}-error`} className="field-error">
                        {e[errKey]}
                      </span>
                    )}
                  </div>
                );
              })}
              <div className="field">
                <label htmlFor={`src-${s.id}-kind`}>{t("financial.src_kind")}</label>
                <select
                  id={`src-${s.id}-kind`}
                  value={s.kind}
                  onChange={(ev) => updateSource(i, { kind: ev.target.value as SourceKind })}
                >
                  {KINDS.map((k) => (
                    <option key={k} value={k}>
                      {t(`financial.kind_${k}`)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button type="button" className="btn btn-danger" style={{ marginTop: 8 }} onClick={() => removeSource(s.id)}>
              {t("common.remove")} {s.id}
            </button>
          </fieldset>
        ))}
        <button type="button" className="btn" onClick={addSource}>
          + {t("financial.addSource")}
        </button>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>{t("financial.costs")}</h2>
        <p className="muted">{t("financial.costsHelp", { currency })}</p>
        {costs.map((c, i) => (
          <div key={c.key ?? `custom-${i}`} style={{ borderTop: "1px solid var(--border)", padding: "10px 0" }}>
            <div className="grid-2" style={{ alignItems: "end" }}>
              {c.key === null ? (
                <div className="field">
                  <label htmlFor={`cost-name-${i}`}>{t("financial.category")}</label>
                  <input
                    id={`cost-name-${i}`}
                    value={c.name}
                    onChange={(ev) => setCosts((cs) => cs.map((x, j) => (j === i ? { ...x, name: ev.target.value } : x)))}
                    aria-invalid={!!e[`costs.${i}.name`]}
                  />
                </div>
              ) : null}
              <RangeInputs
                id={`cost-${i}`}
                label={`${c.name || t("financial.category")} (${currency}/ha)`}
                value={c.per_ha}
                onChange={(per_ha) => setCosts((cs) => cs.map((x, j) => (j === i ? { ...x, per_ha } : x)))}
                error={e[`costs.${i}`] ?? e[`costs.${i}.low`] ?? e[`costs.${i}.high`] ?? e[`costs.${i}.name`]}
              />
              <button type="button" className="btn btn-danger" onClick={() => setCosts((cs) => cs.filter((_, j) => j !== i))}>
                {t("financial.notApplicable")}
              </button>
            </div>
            <SourcePicker
              id={`cost-${i}`}
              sources={sources}
              selected={c.source_ids}
              onChange={(ids) => setCosts((cs) => cs.map((x, j) => (j === i ? { ...x, source_ids: ids } : x)))}
              error={e[`costs.${i}.sources`]}
            />
          </div>
        ))}
        <div className="row" style={{ marginTop: 8 }}>
          <button
            type="button"
            className="btn"
            onClick={() => setCosts((cs) => [...cs, { key: null, name: "", per_ha: emptyRange(), source_ids: [] }])}
          >
            + {t("financial.addCost")}
          </button>
          {STANDARD_COST_CATEGORIES.filter((s) => !costs.some((c) => c.key === s.key)).map((s) => (
            <button
              key={s.key}
              type="button"
              className="btn"
              style={{ fontWeight: 400 }}
              onClick={() => setCosts((cs) => [...cs, { key: s.key, name: s.name, per_ha: emptyRange(), source_ids: [] }])}
            >
              + {s.name}
            </button>
          ))}
        </div>
      </div>

      <div className="card grid-2">
        <div>
          <RangeInputs
            id="yield"
            label={t("financial.yield")}
            value={yieldRange}
            onChange={setYieldRange}
            error={e.yield_kg_per_ha ?? e["yield_kg_per_ha.low"] ?? e["yield_kg_per_ha.high"]}
          />
          <SourcePicker
            id="yield"
            sources={sources}
            selected={yieldSources}
            onChange={setYieldSources}
            error={e["yield_kg_per_ha.sources"]}
          />
        </div>
        <div>
          <RangeInputs
            id="price"
            label={t("financial.price", { currency })}
            value={price}
            onChange={setPrice}
            error={e.price_per_kg ?? e["price_per_kg.low"] ?? e["price_per_kg.high"]}
          />
          <SourcePicker
            id="price"
            sources={sources}
            selected={priceSources}
            onChange={setPriceSources}
            error={e["price_per_kg.sources"]}
          />
        </div>
      </div>

      <section className="card" aria-live="polite" aria-labelledby="fin-results">
        <h2 id="fin-results" style={{ marginTop: 0 }}>
          {t("financial.results")}
        </h2>
        {!outcome.ok && <p className="muted">{t("financial.fixInputs")}</p>}
        {r && (
          <>
            {r.uses_synthetic && (
              <div className="notice notice-warn" role="status">
                {t("financial.syntheticInputs")}
              </div>
            )}
            <div className="table-scroll">
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
            </div>
            {(r.unknowns.length > 0 || r.limitations.length > 0) && (
              <div className="notice notice-warn" style={{ marginTop: 12 }}>
                <strong>{t("financial.limitationsTitle")}</strong>
                <ul style={{ margin: "4px 0 0" }}>
                  {[...r.unknowns, ...r.limitations].map((u, i) => (
                    <li key={i}>{u}</li>
                  ))}
                </ul>
              </div>
            )}
            <details className="muted">
              <summary style={{ cursor: "pointer" }}>{t("common.assumptions")}</summary>
              <ul>
                {r.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
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
