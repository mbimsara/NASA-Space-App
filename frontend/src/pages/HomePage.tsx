/** Tharuka's landing design connected to Shehani's real navigation and fixture flow. */
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAppStore } from "../hooks/useAppStore";
import { useTheme } from "../hooks/useTheme";
import { Icon } from "../components/ui/Icon";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { listCachedPlanIds } from "../utils/offlineCache";

const slides = ["agrosphere-hero.webp", "agrosphere-hero-aerial.webp", "agrosphere-hero-precision.webp", "agrosphere-hero-water.webp", "agrosphere-hero-global.webp"];

export function HomePage() {
  const navigate = useNavigate();
  const [theme, toggleTheme] = useTheme();
  const recentFarms = useAppStore((s) => s.recentFarms);
  const recentPlans = useAppStore((s) => s.recentPlans);
  const setFarm = useAppStore((s) => s.setFarm);
  const [menu, setMenu] = useState(false);
  const [slide, setSlide] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [offlineIds] = useState(() => new Set(listCachedPlanIds()));

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = window.setInterval(() => setSlide((value) => (value + 1) % slides.length), 6500);
    return () => window.clearInterval(timer);
  }, []);

  const loadDemo = async () => {
    setBusy(true);
    setError(null);
    try {
      const farm = await api.createDemoFarm();
      setFarm(farm);
      navigate(`/farms/${farm.id}`);
    } catch (cause) {
      setError(cause);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="landing" data-theme={theme}>
      <header className="land-nav">
        <button className="brand" type="button" onClick={() => window.scrollTo(0, 0)}><span className="brand-mark"><Icon name="leaf" /></span><span>AgroSphere <b>AI</b></span></button>
        <nav className={menu ? "open" : ""} aria-label="Landing navigation"><a href="#platform">Platform</a><a href="#data">NASA data</a><a href="#impact">Impact</a><a href="#workspace">Workspace</a></nav>
        <div className="land-actions">
          <button className="icon-btn theme-toggle" type="button" onClick={toggleTheme} aria-label="Toggle theme"><Icon name={theme === "dark" ? "sun" : "moon"} /></button>
          <button className="icon-btn mobile-menu" type="button" onClick={() => setMenu(!menu)} aria-label="Open menu"><Icon name={menu ? "close" : "menu"} /></button>
          <button className="btn btn-secondary" type="button" onClick={loadDemo} disabled={busy}>{busy ? "Loading…" : "View demo"}</button>
          <Link className="btn btn-primary" to="/farms/new">Open platform <Icon name="arrow" /></Link>
        </div>
      </header>
      <main>
        <section className="hero">
          <div className="hero-images">{slides.map((name, index) => <img key={name} className={slide === index ? "active" : ""} src={`/images/${name}`} alt="" aria-hidden={slide !== index} />)}</div>
          <div className="hero-shade" />
          <div className="hero-content">
            <div className="eyebrow"><span /> Earth intelligence for every field</div>
            <h1>Grow with the planet,<br /><em>not against it.</em></h1>
            <p>AgroSphere turns Earth observation signals and farm knowledge into clear, climate-resilient decisions for growers everywhere.</p>
            <div className="hero-buttons"><Link className="btn btn-primary" to="/farms/new">Explore your farm <Icon name="arrow" /></Link><a className="video-btn" href="#platform"><span>▶</span> See how it works</a></div>
            <a href="https://www.spaceappschallenge.org/" target="_blank" rel="noopener noreferrer" className="hero-spaceapps-badge" title="Built for NASA Space Apps 2026 - Official Challenge Site">
              <img src="/images/nasa-space-apps-logo-transparent.png" alt="NASA Space Apps Challenge" className="hero-spaceapps-logo" />
              <span className="hero-spaceapps-divider" />
              <div className="hero-spaceapps-text"><strong>Built for NASA Space Apps 2026</strong><small>Official Global Challenge ? spaceappschallenge.org <Icon name="external" /></small></div>
            </a>
          </div>
          <div className="hero-float card"><div className="float-top"><span className="status-dot" /> Decision workspace <span>Ready</span></div><div className="float-score"><strong>3–5</strong><span>seasons<br /><b>compared</b></span></div><p>Compare crop, water, climate, soil, and financial trade-offs in one farm context.</p></div>
        </section>
        <section className="stats"><div><strong>4</strong><span>NASA data contexts</span></div><div><strong>3–5</strong><span>seasons planned</span></div><div><strong>1</strong><span>connected farm record</span></div><div><strong>3</strong><span>interface languages</span></div></section>
        <section id="platform" className="land-section intro">
          <div className="section-kicker">ONE CONNECTED PLATFORM</div><h2>From uncertainty to informed action.</h2><p className="lead">Plan across seasons, test climate stress, and inspect the evidence and limitations behind every result.</p>
          <div className="feature-grid">{[
            ["rotate", "Plan beyond one harvest", "Compare multi-season rotations, water demand, soil benefits, constraints, and uncertainty."],
            ["climate", "Prepare for what’s next", "Test hypothetical rainfall changes without rewriting the historical NASA baseline."],
            ["chat", "Understand every result", "Ask the assistant to explain the selected farm, analysis, scenario, and candidate."],
          ].map(([icon, title, copy], index) => <article className={`feature-card feature-${index}`} key={title}><div className="feature-icon"><Icon name={icon} /></div><h3>{title}</h3><p>{copy}</p><Link className="feature-action" to="/farms/new">Open workspace <Icon name="arrow" /></Link></article>)}</div>
        </section>
        <section id="data" className="data-section">
          <div className="data-copy"><div className="section-kicker light">EARTH OBSERVATION, MADE USEFUL</div><h2>Global perspective.<br />Visible limitations.</h2><p>NASA POWER climate observations and regional SMAP surface-moisture context are kept separate from measured field soil properties.</p><ul><li><Icon name="check" /> Source, dates, units, and coverage</li><li><Icon name="check" /> Missing days remain visible</li><li><Icon name="check" /> Historical baselines stay distinct from scenarios</li></ul><div className="prototype-note"><Icon name="book" /><span><b>Transparency by design</b>Fixture results are labelled synthetic. Modeled NASA values are not presented as on-farm measurements.</span></div></div>
          <div className="earth-card"><img className="earth-image" src="/images/earth-observation.webp" alt="Earth observation view centred on South Asia" /></div>
        </section>
        <section id="impact" className="land-section impact"><div className="section-kicker">DESIGNED FOR REAL-WORLD RESILIENCE</div><h2>Every tool supports the rotation decision.</h2><div className="impact-grid"><div><Icon name="climate" /><h3>Water security</h3><p>Compare rainfall, known field-applied irrigation, and crop demand.</p></div><div><Icon name="farm" /><h3>Soil and recovery</h3><p>Keep measured soil inputs distinct from modeled screening indicators.</p></div><div><Icon name="coin" /><h3>Financial scenarios</h3><p>Inspect ranges, sources, dates, and omitted cost categories.</p></div><div><Icon name="overview" /><h3>Climate context</h3><p>Explore observations, scenarios, and future climate-twin methods.</p></div></div></section>
        <section id="workspace" className="land-section intro"><div className="section-kicker">YOUR WORKSPACE</div><h2>Pick up where you left off.</h2><ErrorMessage error={error} onRetry={loadDemo} /><div className="feature-grid"><article className="feature-card"><h3>Recent farms</h3>{recentFarms.length ? recentFarms.map((farm) => <Link key={farm.id} to={`/farms/${farm.id}`}>{farm.name}</Link>) : <p>No farms yet on this device.</p>}</article><article className="feature-card"><h3>Saved plans</h3>{recentPlans.length ? recentPlans.map((plan) => <Link key={plan.id} to={`/plans/${plan.id}`}>{plan.name}{offlineIds.has(plan.id) ? " · Offline" : ""}</Link>) : <p>No saved plans yet on this device.</p>}</article><article className="feature-card"><h3>Start planning</h3><p>Create a farm or load the clearly labelled synthetic demonstration.</p><Link to="/farms/new">Create farm →</Link></article></div></section>
      </main>
      <footer><div className="brand"><span className="brand-mark"><Icon name="leaf" /></span><span>AgroSphere <b>AI</b></span></div><p>NASA Space Apps Challenge 2026</p><span>Sources and uncertainty shown with results</span></footer>
    </div>
  );
}
