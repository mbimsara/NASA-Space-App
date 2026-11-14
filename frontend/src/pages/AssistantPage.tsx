/**
 * AssistantPage — explanations grounded in the currently selected farm/analysis/
 * scenario/candidate. Conversation resets whenever that context changes.
 * Owner: Shehani (UI). Answers: Akash's assistant service.
 */
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { isAbortError } from "../api/requestGuard";
import { isAnalysisOutdated, selectCurrentAnalysis, selectCurrentScenario, useAppStore } from "../hooks/useAppStore";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { useCanWrite } from "../hooks/useCanWrite";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { ApiClientError } from "../api/client";
import type { Language } from "../types/api";
import type { AssistantMessage } from "../types/api";

export function AssistantPage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;
  const analysis = useAppStore(selectCurrentAnalysis);
  const scenario = useAppStore(selectCurrentScenario);
  const candidateId = useAppStore((s) => s.selectedCandidateId);
  const language = useAppStore((s) => s.language);
  const allScenarios = useAppStore((s) => s.scenarios);
  const selectScenario = useAppStore((s) => s.selectScenario);
  const clearScenario = useAppStore((s) => s.clearScenario);
  const selectCandidate = useAppStore((s) => s.selectCandidate);
  const clearCandidate = useAppStore((s) => s.clearCandidate);
  const guard = useLatestRequest();
  const canWrite = useCanWrite();

  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const contextKey = `${farm.id}|${farm.input_version}|${analysis?.analysis_id}|${scenario?.scenario_id}|${candidateId}`;
  useEffect(() => {
    guard.cancel();
    // A conversation cannot cross farm/analysis/scenario context boundaries.
    // oxlint-disable-next-line react/set-state-in-effect
    setMessages([]);
    setError(null);
    setLoading(false);
  }, [contextKey, guard]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [messages]);

  if (!analysis) {
    return (
      <div className="page">
        <h1>{t("assistant.title")}</h1>
        <div className="card muted">
          {t("assistant.noAnalysis")} <Link to={`/farms/${farm.id}/rotations`}>{t("rotation.run")}</Link>
        </div>
      </div>
    );
  }

  const candidateRank = analysis.candidates.findIndex((c) => c.candidate_id === candidateId);
  const outdated = isAnalysisOutdated(analysis, farm.input_version);
  // Scenarios already computed from this exact baseline (context selection).
  const scenarioOptions = Object.values(allScenarios)
    .filter((sc) => sc.baseline_analysis_id === analysis.analysis_id)
    .sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));
  const planLink = (id: string) => `/farms/${farm.id}/rotations#candidate-${id}`;

  const sendMessage = async (text: string, lang: Language = language) => {
    if (!text.trim() || outdated || !canWrite) return;
    const ticket = guard.next();
    setLoading(true);
    setError(null);
    setMessages((m) => [...m, { role: "user", content: text, source_ids: [], limitations: [] }]);
    setInput("");
    try {
      const response = await api.sendAssistantMessage(
        {
          farm_id: farm.id,
          analysis_id: analysis.analysis_id,
          scenario_id: scenario?.scenario_id,
          candidate_id: candidateId ?? undefined,
          language: lang,
          message: text,
        },
        ticket.signal,
      );
      if (ticket.isCurrent()) setMessages((m) => [...m, response]);
    } catch (err) {
      if (ticket.isCurrent() && !isAbortError(err)) {
        setError(err);
        setMessages((m) => m.slice(0, -1));
        setInput(text);
      }
    } finally {
      if (ticket.isCurrent()) setLoading(false);
    }
  };

  const sourceLink = (id: string) => {
    if (id === analysis.analysis_id) return <Link to={`/farms/${farm.id}/rotations`}>{id}</Link>;
    if (scenario && id === scenario.scenario_id) return <Link to={`/farms/${farm.id}/scenario`}>{id}</Link>;
    if (analysis.observation_id && id === analysis.observation_id) return <Link to={`/farms/${farm.id}`}>{id}</Link>;
    if (analysis.candidates.some((c) => c.candidate_id === id)) return <Link to={planLink(id)}>{id}</Link>;
    // Akash's service may return the producer's real source URL as a reference.
    if (/^https?:\/\//i.test(id)) {
      let host = id;
      try {
        host = new URL(id).host;
      } catch {
        /* keep the raw text */
      }
      return (
        <a href={id} target="_blank" rel="noreferrer">
          {host}
        </a>
      );
    }
    return <span>{id}</span>;
  };

  const suggestions = [t("assistant.q1"), t("assistant.q2"), t("assistant.q3")];

  return (
    <div className="page">
      <h1>{t("assistant.title")}</h1>

      {outdated && (
        <div className="notice notice-warn" role="alert">
          {t("assistant.outdated")} <Link to={`/farms/${farm.id}/rotations`}>{t("rotation.rerun")}</Link>
        </div>
      )}

      <fieldset className="card" style={{ margin: "0 0 16px" }}>
        <legend style={{ fontWeight: 700 }}>{t("assistant.chooseContext")}</legend>
        <div className="grid-2">
          <div className="field">
            <label htmlFor="ctx-plan">{t("assistant.ctxPlan")}</label>
            <select
              id="ctx-plan"
              value={candidateId ?? ""}
              onChange={(e) => (e.target.value ? selectCandidate(e.target.value) : clearCandidate())}
            >
              <option value="">{t("assistant.ctxNoPlan")}</option>
              {analysis.candidates.map((c, i) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  {t("rotation.candidate", { index: i + 1 })}: {c.sequence.map((q) => q.crop_name ?? q.crop_id).join(" → ")}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="ctx-scenario">{t("assistant.ctxScenario")}</label>
            <select
              id="ctx-scenario"
              value={scenario?.scenario_id ?? ""}
              onChange={(e) => (e.target.value ? selectScenario(e.target.value) : clearScenario())}
            >
              <option value="">{t("scenario.baseline")}</option>
              {scenarioOptions.map((sc) => (
                <option key={sc.scenario_id} value={sc.scenario_id}>
                  {t("assistant.scenarioOption", { pct: `${sc.parameters.rainfall_change_pct > 0 ? "+" : ""}${sc.parameters.rainfall_change_pct}` })}
                </option>
              ))}
            </select>
            {scenarioOptions.length === 0 && (
              <span className="muted" style={{ fontSize: 12 }}>
                {t("assistant.noScenarios")} <Link to={`/farms/${farm.id}/scenario`}>{t("scenario.run")}</Link>
              </span>
            )}
          </div>
        </div>
        <p className="muted" style={{ margin: "8px 0 0", fontSize: 12 }}>
          {t("assistant.contextResets")}
        </p>
      </fieldset>

      <div className="notice notice-info" role="note">
        <strong>{t("assistant.contextNote")}</strong>
        <ul style={{ margin: "4px 0 0" }}>
          <li>
            {t("assistant.ctxAnalysis")}: <Link to={`/farms/${farm.id}/rotations`}>{analysis.analysis_id}</Link>
          </li>
          <li>
            {t("assistant.ctxPlan")}:{" "}
            {candidateRank >= 0 && candidateId ? (
              <Link to={planLink(candidateId)}>{t("rotation.candidate", { index: candidateRank + 1 })}</Link>
            ) : (
              t("assistant.ctxNoPlan")
            )}
          </li>
          <li>
            {t("assistant.ctxScenario")}:{" "}
            {scenario ? (
              <Link to={`/farms/${farm.id}/scenario`}>
                {scenario.parameters.rainfall_change_pct}% ({t("scenario.hypothetical")})
              </Link>
            ) : (
              t("scenario.baseline")
            )}
          </li>
          <li>
            {t("nav.language")}: {language}
          </li>
        </ul>
      </div>

      <div
        ref={logRef}
        role="log"
        aria-live="polite"
        aria-label={t("assistant.conversation")}
        className="card"
        style={{ minHeight: 240, maxHeight: 420, overflowY: "auto" }}
      >
        {messages.length === 0 && !loading && <p className="muted">{t("assistant.empty")}</p>}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: 14,
              display: "flex",
              flexDirection: "column",
              alignItems: msg.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            <div
              style={{
                maxWidth: "85%",
                background: msg.role === "user" ? "var(--blue-700)" : "var(--surface-alt)",
                color: msg.role === "user" ? "var(--on-primary)" : "var(--text)",
                borderRadius: 10,
                padding: "10px 14px",
                fontSize: 14,
              }}
            >
              {msg.content}
            </div>
            {msg.role === "assistant" && msg.source_ids.length > 0 && (
              <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                {t("assistant.sources")}:{" "}
                {msg.source_ids.map((id, j) => (
                  <span key={id}>
                    {j > 0 && ", "}
                    {sourceLink(id)}
                  </span>
                ))}
              </div>
            )}
            {msg.role === "assistant" && msg.status && msg.status !== "answered" && (
              <div className="notice notice-warn" role="note" style={{ fontSize: 12, margin: "6px 0 0", padding: "4px 8px" }}>
                {t(`assistant.status.${msg.status}`, { defaultValue: msg.status })}
              </div>
            )}
            {msg.role === "assistant" && (msg.assumptions?.length ?? 0) > 0 && (
              <details style={{ fontSize: 12, marginTop: 4 }}>
                <summary style={{ cursor: "pointer" }}>{t("common.assumptions")}</summary>
                <ul style={{ margin: "4px 0 0 16px" }}>
                  {msg.assumptions!.map((a, j) => (
                    <li key={j}>{a}</li>
                  ))}
                </ul>
              </details>
            )}
            {msg.role === "assistant" && msg.limitations.length > 0 && (
              <ul style={{ fontSize: 12, color: "var(--red-700)", margin: "4px 0 0 16px" }}>
                {msg.limitations.map((l, j) => (
                  <li key={j}>{l}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
        {loading && <LoadingSpinner />}
      </div>

      <div className="row" style={{ marginBottom: 12 }} aria-label={t("assistant.suggestedQuestions")}>
        {suggestions.map((q) => (
          <button key={q} type="button" className="btn" style={{ fontWeight: 400 }} onClick={() => sendMessage(q)} disabled={loading || outdated || !canWrite}>
            {q}
          </button>
        ))}
      </div>

      {!canWrite && <p className="muted" role="note">{t("offline.writeBlocked")}</p>}
      <ErrorMessage error={error} />
      {error instanceof ApiClientError && error.code === "UNSUPPORTED_LANGUAGE" && language !== "en" && (
        <div className="row" style={{ marginBottom: 12 }}>
          <button data-testid="assistant-english-retry" type="button" className="btn btn-secondary" onClick={() => sendMessage(input, "en")} disabled={loading || !input.trim() || !canWrite || outdated}>
            {t("assistant.askInEnglish")}
          </button>
          <span className="muted">{t("assistant.languagePending")}</span>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="row"
        style={{ flexWrap: "nowrap" }}
      >
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="assistant-input" className="muted" style={{ fontWeight: 400 }}>
            {t("assistant.placeholder")}
          </label>
          <input id="assistant-input" type="text" maxLength={2000} value={input} onChange={(e) => setInput(e.target.value)} disabled={loading} />
        </div>
        <button type="submit" className="btn btn-secondary" disabled={loading || !input.trim() || !canWrite || outdated}>
          {t("assistant.send")}
        </button>
      </form>
    </div>
  );
}
