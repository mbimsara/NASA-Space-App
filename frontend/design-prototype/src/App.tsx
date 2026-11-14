import { useEffect, useRef, useState } from "react";

type IconName =
  | "leaf"
  | "grid"
  | "rotation"
  | "climate"
  | "water"
  | "soil"
  | "scan"
  | "globe"
  | "chat"
  | "calendar"
  | "wallet"
  | "report"
  | "community"
  | "settings"
  | "bell"
  | "search"
  | "menu"
  | "arrow"
  | "spark"
  | "sun"
  | "moon"
  | "rain"
  | "wind"
  | "trend"
  | "check"
  | "info"
  | "chevron"
  | "close"
  | "upload"
  | "download"
  | "play"
  | "location"
  | "satellite"
  | "clock"
  | "shield"
  | "plus"
  | "mic"
  | "external";

const paths: Record<IconName, React.ReactNode> = {
  leaf: (
    <>
      <path d="M20 4c-7 0-13 3-14 10 3-2 6-3 10-3-5 2-8 5-9 9" />
      <path d="M6 14c0 3 2 5 5 5 6 0 9-7 9-15" />
    </>
  ),
  grid: (
    <>
      <rect x="4" y="4" width="6" height="6" rx="2" />
      <rect x="14" y="4" width="6" height="6" rx="2" />
      <rect x="4" y="14" width="6" height="6" rx="2" />
      <rect x="14" y="14" width="6" height="6" rx="2" />
    </>
  ),
  rotation: (
    <>
      <path d="M20 7h-5V2" />
      <path d="M20 7a9 9 0 1 0 1 9" />
      <path d="m4 17 4-1 1 4" />
    </>
  ),
  climate: (
    <>
      <path d="M12 9V3" />
      <path d="M8 5h8" />
      <path d="M7 15a5 5 0 1 0 10 0c0-2-1-3-2-4V5a3 3 0 0 0-6 0v6c-1 1-2 2-2 4Z" />
    </>
  ),
  water: <path d="M12 3S5 11 5 16a7 7 0 0 0 14 0c0-5-7-13-7-13Z" />,
  soil: (
    <>
      <path d="M3 16c3-2 5 2 8 0s5 2 10 0" />
      <path d="M3 20c3-2 5 2 8 0s5 2 10 0" />
      <path d="M12 14V6" />
      <path d="M12 10c-4 0-6-2-6-5 4 0 6 2 6 5Zm0-2c3 0 5-2 5-5-3 0-5 2-5 5Z" />
    </>
  ),
  scan: (
    <>
      <path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" />
      <path d="M8 15c5 0 8-3 8-8-5 0-8 3-8 8Z" />
    </>
  ),
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
    </>
  ),
  chat: (
    <>
      <path d="M21 14a4 4 0 0 1-4 4H9l-5 3v-5a6 6 0 0 1-1-3V8a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z" />
      <path d="M8 10h.01M12 10h.01M16 10h.01" />
    </>
  ),
  calendar: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="3" />
      <path d="M8 3v4M16 3v4M3 10h18" />
      <path d="M8 14h2M14 14h2M8 18h2" />
    </>
  ),
  wallet: (
    <>
      <path d="M4 6h14a2 2 0 0 1 2 2v11H5a2 2 0 0 1-2-2V6a3 3 0 0 1 3-3h11" />
      <path d="M16 12h5v4h-5a2 2 0 0 1 0-4Z" />
    </>
  ),
  report: (
    <>
      <path d="M6 3h9l4 4v14H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
      <path d="M14 3v5h5M8 13h8M8 17h6" />
    </>
  ),
  community: (
    <>
      <circle cx="9" cy="8" r="3" />
      <circle cx="17" cy="9" r="2" />
      <path d="M3 20c0-4 2-7 6-7s6 3 6 7M15 14c4 0 6 2 6 6" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path
        d="M19 13.5v-3l-2-.6-.7-1.7 1-1.8-2.1-2.1-1.8 1-1.7-.7L11 3H8l-.6 2-1.7.7-1.8-1-2.1 2.1 1 1.8-.7 1.7-2 .6v3l2 .6.7 1.7-1 1.8 2.1 2.1 1.8-1 1.7.7.6 2h3l.6-2 1.7-.7 1.8 1 2.1-2.1-1-1.8.7-1.7Z"
        transform="scale(.8) translate(3 3)"
      />
    </>
  ),
  bell: (
    <>
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
  spark: (
    <>
      <path d="m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5Z" />
      <path d="m19 15 .7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7Z" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  moon: <path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z" />,
  rain: (
    <>
      <path d="M7 16h10a4 4 0 0 0 0-8 6 6 0 0 0-11-1 4.5 4.5 0 0 0 1 9Z" />
      <path d="m8 19-1 2m5-2-1 2m5-2-1 2" />
    </>
  ),
  wind: (
    <>
      <path d="M3 8h12c4 0 4-5 1-5-2 0-2 2-2 2M3 12h16c3 0 3 5 0 5h-2M3 16h8c3 0 3 5 0 5" />
    </>
  ),
  trend: <path d="m3 17 6-6 4 4 8-9m-5 0h5v5" />,
  check: <path d="m5 12 4 4L19 6" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6M12 7h.01" />
    </>
  ),
  chevron: <path d="m9 18 6-6-6-6" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  upload: (
    <>
      <path d="M12 16V4m-5 5 5-5 5 5" />
      <path d="M5 20h14" />
    </>
  ),
  download: (
    <>
      <path d="M12 4v12m-5-5 5 5 5-5" />
      <path d="M5 20h14" />
    </>
  ),
  play: <path d="m9 7 8 5-8 5Z" />,
  location: (
    <>
      <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
      <circle cx="12" cy="10" r="2" />
    </>
  ),
  satellite: (
    <>
      <path d="m5 5 14 14M8 2l4 4-4 4-4-4Zm8 12 4 4-4 4-4-4Z" />
      <path d="M14 5c3 1 4 2 5 5M5 14c1 3 2 4 5 5" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6l4 2" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3 4 6v5c0 5 3 8 8 10 5-2 8-5 8-10V6Z" />
      <path d="m8 12 3 3 5-6" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  mic: (
    <>
      <rect x="9" y="3" width="6" height="12" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </>
  ),
  external: (
    <>
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </>
  ),
};

function Icon({
  name,
  size = 20,
  className = "",
}: {
  name: IconName;
  size?: number;
  className?: string;
}) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}

const nav = [
  ["setup", "Farm setup", "location"],
  ["dashboard", "Farm overview", "grid"],
  ["rotation", "Crop planner", "rotation"],
  ["climate", "Climate lab", "climate"],
  ["assistant", "AI assistant", "chat"],
  ["saved", "Saved plans & export", "download"],
  ["water", "Water budget", "water"],
  ["soil", "Soil health", "soil"],
  ["weeds", "WeedShield AI", "scan"],
  ["twin", "Climate twin", "globe"],
  ["calendar", "Farm calendar", "calendar"],
  ["finance", "Financial planner", "wallet"],
  ["reports", "Reports & history", "report"],
  ["community", "Community water", "community"],
  ["settings", "Settings", "settings"],
] as [string, string, IconName][];

const pageMeta: Record<string, [string, string]> = {
  setup: ["Set up your farm", "Create the farm profile used across every AgroSphere plan."],
  dashboard: ["Good morning, Nimal", "Here’s what’s happening across Green Valley Farm."],
  rotation: ["Crop Rotation Planner", "Build a resilient, profitable multi-season crop plan."],
  climate: ["Climate Simulation Lab", "Stress-test your plan against future weather scenarios."],
  water: ["Water Budget Planner", "Balance expected supply against crop demand."],
  soil: ["Soil Health & Recovery", "Restore fertility and build long-term soil resilience."],
  weeds: ["WeedShield AI", "Estimate weed pressure from a field image."],
  twin: ["Global Climate Twin Finder", "Learn from farms facing conditions like yours."],
  assistant: ["AI Farming Assistant", "Guidance in English, සිංහල, and தமிழ்."],
  saved: ["Saved Plan & Export", "Review, document, and share your selected farm strategy."],
  calendar: ["Farm Calendar", "Keep every field task on time."],
  finance: ["Financial Planner", "Compare costs, returns, and risk across plans."],
  reports: ["Reports & History", "Review decisions, outcomes, and agronomist notes."],
  community: ["Community Water Planning", "Coordinate shared irrigation resources fairly."],
  settings: ["Settings", "Personalize AgroSphere for your farm and team."],
};

const coreJourney = [
  ["setup", "Farm setup", "location"],
  ["dashboard", "Dashboard", "grid"],
  ["rotation", "Crop plan", "rotation"],
  ["climate", "Climate test", "climate"],
  ["assistant", "AI review", "chat"],
  ["saved", "Save & export", "download"],
] as [string, string, IconName][];

const sampleBadge = <span className="sample-badge">SAMPLE DATA</span>;

function Button({
  children,
  variant = "primary",
  onClick,
  icon,
}: {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  onClick?: () => void;
  icon?: IconName;
}) {
  return (
    <button onClick={onClick} className={`btn btn-${variant}`}>
      {children}
      {icon && <Icon name={icon} size={17} />}
    </button>
  );
}

function Card({ children, className = "", ...props }: React.ComponentPropsWithoutRef<"section">) {
  return (
    <section className={`card ${className}`} {...props}>
      {children}
    </section>
  );
}

function SectionHead({
  title,
  sub,
  action,
}: {
  title: string;
  sub?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="section-head">
      <div>
        <h2>{title}</h2>
        {sub && <p>{sub}</p>}
      </div>
      {action}
    </div>
  );
}

function MiniChart({ color = "#10B981", bars = false }: { color?: string; bars?: boolean }) {
  if (bars)
    return (
      <div className="mini-bars">
        {[34, 55, 43, 72, 64, 88, 77].map((v, i) => (
          <i key={i} style={{ height: `${v}%`, background: i === 5 ? color : "#dce8df" }} />
        ))}
      </div>
    );
  return (
    <svg className="mini-chart" viewBox="0 0 160 52" preserveAspectRatio="none">
      <defs>
        <linearGradient id={`g${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop stopColor={color} stopOpacity=".25" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d="M0 44 C20 40,20 29,40 32 S64 42,80 22 S105 34,120 16 S145 20,160 5 V52 H0Z"
        fill={`url(#g${color.replace("#", "")})`}
      />
      <path
        d="M0 44 C20 40,20 29,40 32 S64 42,80 22 S105 34,120 16 S145 20,160 5"
        fill="none"
        stroke={color}
        strokeWidth="3"
      />
    </svg>
  );
}

function CoreJourney({ page, setPage }: { page: string; setPage: (page: string) => void }) {
  const current = coreJourney.findIndex(([id]) => id === page);
  const next = coreJourney[current + 1];
  return (
    <Card className="core-journey" aria-label="Core planning journey">
      <div className="journey-label">
        <span>CORE WORKFLOW</span>
        <b>Step {current + 1} of 6</b>
      </div>
      <div className="journey-steps">
        {coreJourney.map(([id, label, icon], index) => (
          <button
            key={id}
            className={`${id === page ? "active" : ""} ${index < current ? "complete" : ""}`}
            onClick={() => setPage(id)}
            aria-current={id === page ? "step" : undefined}
          >
            <i>
              <Icon name={index < current ? "check" : icon} size={14} />
            </i>
            <span>{label}</span>
          </button>
        ))}
      </div>
      {next ? (
        <button className="journey-next" onClick={() => setPage(next[0])}>
          Next: {next[1]} <Icon name="arrow" size={15} />
        </button>
      ) : (
        <span className="journey-done">
          <Icon name="check" size={14} /> Journey complete
        </span>
      )}
    </Card>
  );
}

const nasaSources = [
  {
    name: "NASA SMAP L3",
    metric: "Surface soil moisture",
    unit: "m³/m³",
    observed: "24 May 2026",
    resolution: "9 km",
    uncertainty: "±0.04 m³/m³",
  },
  {
    name: "NASA GPM IMERG",
    metric: "Precipitation estimate",
    unit: "mm/day",
    observed: "23 May 2026",
    resolution: "10 km",
    uncertainty: "±20% sample range",
  },
  {
    name: "NASA MODIS MOD13",
    metric: "Vegetation index",
    unit: "NDVI index",
    observed: "17 May 2026",
    resolution: "250 m",
    uncertainty: "Quality flag: good",
  },
];

function DataProvenance({ compact = false }: { compact?: boolean }) {
  const [open, setOpen] = useState(!compact);
  return (
    <Card className={`data-provenance ${compact ? "compact" : ""}`}>
      <button className="provenance-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="nasa-icon">
          <Icon name="satellite" />
        </span>
        <span>
          <b>Earth observation data context</b>
          <small>Illustrative NASA-source metadata · Not a live connection</small>
        </span>
        <span className="quality-pill">
          <i /> Sample quality 92%
        </span>
        <Icon name="chevron" className={open ? "turn" : ""} size={16} />
      </button>
      {open && (
        <div className="source-table">
          <div className="source-row source-labels">
            <span>Source & indicator</span>
            <span>Unit</span>
            <span>Observation date</span>
            <span>Spatial resolution</span>
            <span>Uncertainty</span>
          </div>
          {nasaSources.map((source) => (
            <div className="source-row" key={source.name}>
              <span>
                <b>{source.name}</b>
                <small>{source.metric}</small>
              </span>
              <span>{source.unit}</span>
              <span>{source.observed}</span>
              <span>{source.resolution}</span>
              <span>{source.uncertainty}</span>
            </div>
          ))}
          <div className="source-provenance-footer">
            <a
              href="https://www.spaceappschallenge.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="provenance-spaceapps-badge"
              title="Built for NASA Space Apps 2026 - Official Challenge Site"
            >
              <img
                src="/images/nasa-space-apps-logo.png"
                alt="NASA Space Apps Challenge"
                className="provenance-spaceapps-img"
              />
              <div className="provenance-spaceapps-text">
                <strong>Built for NASA Space Apps 2026</strong>
                <span>Open Science Challenge Prototype · Visit spaceappschallenge.org</span>
              </div>
              <Icon name="external" size={14} />
            </a>
            <p className="source-note">
              <Icon name="info" size={14} />
              Dates and values are realistic sample metadata for interface demonstration only. Local
              field measurements should be used for operational decisions.
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}

function ThemeToggle({ theme, toggleTheme }: { theme: "light" | "dark"; toggleTheme: () => void }) {
  return (
    <button
      className="icon-btn theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
    >
      <Icon name={theme === "light" ? "moon" : "sun"} size={18} />
    </button>
  );
}

function Landing({
  enter,
  theme,
  toggleTheme,
}: {
  enter: () => void;
  theme: "light" | "dark";
  toggleTheme: () => void;
}) {
  const [menu, setMenu] = useState(false);
  const [heroSlide, setHeroSlide] = useState(0);
  const heroSlides = [
    {
      src: "/images/agrosphere-hero.webp",
      alt: "Cinematic aerial view of golden and green agricultural fields with distant mountains under a blue sky",
    },
    {
      src: "/images/agrosphere-hero-aerial.webp",
      alt: "Top-down aerial view of varied green agricultural fields divided by trees",
    },
    {
      src: "/images/agrosphere-hero-precision.webp",
      alt: "Wide aerial view of precision agriculture fields with a tractor and distant mountains",
    },
    {
      src: "/images/agrosphere-hero-water.webp",
      alt: "Aerial view of climate-resilient green and golden fields surrounding an irrigation canal and reservoir",
    },
    {
      src: "/images/agrosphere-hero-global.webp",
      alt: "Top-down aerial view of diverse green, golden, and cultivated fields surrounding a farm and narrow waterways",
    },
  ];
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const timer = window.setInterval(
      () => setHeroSlide((current) => (current + 1) % heroSlides.length),
      6500,
    );
    return () => window.clearInterval(timer);
  }, [heroSlides.length]);
  return (
    <div className="landing" data-theme={theme}>
      <header className="land-nav">
        <button className="brand" onClick={() => scrollTo(0, 0)}>
          <span className="brand-mark">
            <Icon name="leaf" size={23} />
          </span>
          <span>
            AgroSphere <b>AI</b>
          </span>
        </button>
        <nav className={menu ? "open" : ""}>
          <a href="#platform">Platform</a>
          <a href="#data">NASA data</a>
          <a href="#impact">Impact</a>
          <a href="#team">Team</a>
        </nav>
        <div className="land-actions">
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
          <button className="icon-btn mobile-menu" onClick={() => setMenu(!menu)}>
            <Icon name={menu ? "close" : "menu"} />
          </button>
          <Button variant="secondary" onClick={enter}>
            View demo
          </Button>
          <Button onClick={enter}>
            Open platform <Icon name="arrow" size={17} />
          </Button>
        </div>
      </header>
      <main>
        <section className="hero">
          <div className="hero-images">
            {heroSlides.map((slide, index) => (
              <img
                key={slide.src}
                className={heroSlide === index ? "active" : ""}
                src={slide.src}
                alt={slide.alt}
                aria-hidden={heroSlide !== index}
              />
            ))}
          </div>
          <div className="hero-shade" />
          <div className="hero-content">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              <Icon name="satellite" size={15} />
              <span>Earth intelligence for every field</span>
            </div>
            <h1>
              Grow with the planet,
              <br />
              <em>not against it.</em>
            </h1>
            <p>
              AgroSphere turns Earth observation signals and farm knowledge into clear,
              climate-resilient decisions for growers everywhere.
            </p>
            <div className="hero-buttons">
              <Button onClick={enter}>
                Explore your farm <Icon name="arrow" size={17} />
              </Button>
              <button className="video-btn">
                <span>
                  <Icon name="play" size={18} />
                </span>{" "}
                See how it works
              </button>
            </div>
            <a
              href="https://www.spaceappschallenge.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="hero-spaceapps-badge"
              title="Built for NASA Space Apps 2026 - Official Challenge Site"
            >
              <img
                src="/images/nasa-space-apps-logo-transparent.png"
                alt="NASA Space Apps Challenge"
                className="hero-spaceapps-logo"
              />
              <span className="hero-spaceapps-divider" />
              <div className="hero-spaceapps-text">
                <strong>Built for NASA Space Apps 2026</strong>
                <small>
                  Official Global Challenge · spaceappschallenge.org <Icon name="external" size={11} />
                </small>
              </div>
            </a>
          </div>
          <div className="hero-float card">
            <div className="float-top">
              <span className="status-dot" /> Field outlook <span>Today</span>
            </div>
            <div className="float-score">
              <strong>87</strong>
              <span>
                /100
                <br />
                <b>Strong</b>
              </span>
            </div>
            <div className="float-line">
              <MiniChart />
            </div>
            <p>
              <Icon name="spark" size={16} /> A legume rotation may support soil diversity; verify
              with local evidence
            </p>
          </div>
        </section>
        <section className="stats">
          <div>
            <strong>32%</strong>
            <span>less water risk</span>
          </div>
          <div>
            <strong>2.4×</strong>
            <span>faster planning</span>
          </div>
          <div>
            <strong>14</strong>
            <span>decision modules</span>
          </div>
          <div>
            <strong>3</strong>
            <span>local languages</span>
          </div>
        </section>
        <section id="platform" className="land-section intro">
          <div className="section-kicker">ONE CONNECTED PLATFORM</div>
          <h2>From uncertainty to confident action.</h2>
          <p className="lead">
            Plan across seasons, test against climate extremes, and understand every
            recommendation—with one calm, intelligent workspace.
          </p>
          <div className="feature-grid">
            {[
              [
                "rotation",
                "Plan beyond one harvest",
                "Multi-season crop rotations balance income, soil health, water, and farmer constraints.",
                "Explore rotation planning",
              ],
              [
                "climate",
                "Prepare for what’s next",
                "Simulate heat, rainfall, and drought scenarios before committing resources.",
                "Open climate lab",
              ],
              [
                "spark",
                "Understand every recommendation",
                "See the evidence, uncertainty, and tradeoffs behind each AI-assisted insight.",
                "See explainable AI",
              ],
            ].map(([i, t, d, a], n) => (
              <article className={`feature-card feature-${n}`} key={t} onClick={enter}>
                <div className="feature-icon">
                  <Icon name={i as IconName} />
                </div>
                <h3>{t}</h3>
                <p>{d}</p>
                <button>
                  {a} <Icon name="arrow" size={16} />
                </button>
                <div className="feature-viz">
                  {n === 0 ? (
                    <>
                      <span className="crop corn">M</span>
                      <i />
                      <span className="crop">P</span>
                      <i />
                      <span className="crop gold">R</span>
                    </>
                  ) : n === 1 ? (
                    <MiniChart />
                  ) : (
                    <div className="explain">
                      <b>Why this plan?</b>
                      <span>
                        <i style={{ width: "84%" }} />
                      </span>
                      <small>Water fit · 91% confidence</small>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
        <section id="data" className="data-section">
          <div className="data-copy">
            <div className="section-kicker light">EARTH OBSERVATION, MADE USEFUL</div>
            <h2>
              Global perspective.
              <br />
              Field-level clarity.
            </h2>
            <p>
              AgroSphere’s prototype demonstrates how open Earth science datasets can complement
              local farm records—without pretending sample data is live.
            </p>
            <ul>
              <li>
                <Icon name="check" /> Vegetation and land surface indicators
              </li>
              <li>
                <Icon name="check" /> Precipitation and soil moisture context
              </li>
              <li>
                <Icon name="check" /> Provenance, quality, and uncertainty on every insight
              </li>
            </ul>
            <div className="prototype-note">
              <Icon name="info" />
              <span>
                <b>Transparency by design</b>All values in this prototype are illustrative sample
                data, not live NASA feeds or outputs from trained models.
              </span>
            </div>
          </div>
          <div className="earth-card">
            <img
              className="earth-image"
              src="/images/earth-observation.webp"
              alt="Earth observation view centered on South Asia and Sri Lanka"
            />
            <div className="signal s1">
              <i />
              <span>
                <b>Soil moisture</b>
                <small>Moderate · sample value</small>
              </span>
            </div>
            <div className="signal s2">
              <i />
              <span>
                <b>Data quality</b>
                <small>92% illustrative score</small>
              </span>
            </div>
            <div className="signal s3">
              <i />
              <span>
                <b>Observation region</b>
                <small>Matale, Sri Lanka</small>
              </span>
            </div>
            <div className="signal s4">
              <i />
              <span>
                <b>Prototype context</b>
                <small>NASA open-data concept · not live</small>
              </span>
            </div>
          </div>
        </section>
        <section id="impact" className="land-section impact">
          <div className="section-kicker">DESIGNED FOR REAL-WORLD RESILIENCE</div>
          <h2>Better seasons start with better choices.</h2>
          <div className="impact-grid">
            {[
              [
                "water",
                "Water security",
                "Match crop demand to realistic rainfall and irrigation supply.",
              ],
              [
                "soil",
                "Living soils",
                "Build diversity, organic matter, and recovery into every plan.",
              ],
              [
                "trend",
                "Stronger livelihoods",
                "Compare financial upside against climate and market risk.",
              ],
              [
                "community",
                "Shared resilience",
                "Coordinate scarce resources across farming communities.",
              ],
            ].map(([i, t, d]) => (
              <div key={t}>
                <Icon name={i as IconName} />
                <h3>{t}</h3>
                <p>{d}</p>
              </div>
            ))}
          </div>
        </section>
        <section className="steps">
          <div className="section-kicker light">HOW IT WORKS</div>
          <h2>Complex science. Three simple steps.</h2>
          <div className="step-grid">
            {[
              [
                "01",
                "Describe your farm",
                "Add location, soil, crops, water access, and what matters most to you.",
              ],
              [
                "02",
                "Explore your options",
                "Compare rotations and stress-test them against climate scenarios.",
              ],
              [
                "03",
                "Act with confidence",
                "Follow a seasonal plan with reminders and transparent reasoning.",
              ],
            ].map(([n, t, d]) => (
              <div key={n}>
                <span>{n}</span>
                <h3>{t}</h3>
                <p>{d}</p>
              </div>
            ))}
          </div>
          <Button onClick={enter}>
            Start exploring <Icon name="arrow" />
          </Button>
        </section>
        <section id="team" className="land-section team">
          <div>
            <div className="section-kicker">OUR MISSION</div>
            <h2>Technology that listens to the land—and the people who know it best.</h2>
          </div>
          <div>
            <p>
              Created as a NASA Space Apps Challenge 2026 prototype, AgroSphere explores a future
              where advanced climate intelligence is understandable, responsible, and accessible to
              every farmer.
            </p>
            <div className="team-tags">
              <span>Farmer-centered</span>
              <span>Open science</span>
              <span>Explainable by default</span>
            </div>
          </div>
        </section>
        <section className="cta">
          <div>
            <div className="section-kicker light">YOUR NEXT SEASON STARTS HERE</div>
            <h2>Plan with the whole planet in view.</h2>
            <p>Explore the interactive AgroSphere prototype with realistic sample farm data.</p>
            <Button onClick={enter}>
              Open the farm workspace <Icon name="arrow" />
            </Button>
          </div>
        </section>
      </main>
      <footer>
        <div className="brand">
          <span className="brand-mark">
            <Icon name="leaf" />
          </span>
          <span>
            AgroSphere <b>AI</b>
          </span>
        </div>
        <p>NASA Space Apps Challenge 2026 · Interactive prototype</p>
        <span>Sample data only · No live NASA connection</span>
      </footer>
    </div>
  );
}

function Shell({
  page,
  setPage,
  goHome,
  theme,
  toggleTheme,
}: {
  page: string;
  setPage: (p: string) => void;
  goHome: () => void;
  theme: "light" | "dark";
  toggleTheme: () => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [notice, setNotice] = useState(false);
  return (
    <div className="app-shell" data-theme={theme}>
      {mobile && <div className="scrim" onClick={() => setMobile(false)} />}
      <aside className={`${collapsed ? "collapsed" : ""} ${mobile ? "mobile-open" : ""}`}>
        <button className="brand side-brand" onClick={goHome}>
          <span className="brand-mark">
            <Icon name="leaf" size={21} />
          </span>
          {!collapsed && (
            <span>
              AgroSphere <b>AI</b>
            </span>
          )}
        </button>
        <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
          <Icon name="chevron" className={collapsed ? "flip" : ""} size={17} />
        </button>
        <div className="farm-switch">
          <div>GV</div>
          {!collapsed && (
            <span>
              <b>Green Valley</b>
              <small>Matale, Sri Lanka</small>
            </span>
          )}
          {!collapsed && <Icon name="chevron" size={14} />}
        </div>
        <nav className="side-nav">
          <small>{!collapsed ? "CORE JOURNEY" : "•"}</small>
          {nav.slice(0, 6).map(([id, label, icon]) => (
            <button
              key={id}
              title={label}
              className={page === id ? "active" : ""}
              onClick={() => {
                setPage(id);
                setMobile(false);
              }}
            >
              <Icon name={icon} />
              {!collapsed && <span>{label}</span>}
              {id === "assistant" && !collapsed && <i>AI</i>}
            </button>
          ))}
          <small>{!collapsed ? "ADVANCED TOOLS" : "•"}</small>
          {nav.slice(6).map(([id, label, icon]) => (
            <button
              key={id}
              title={label}
              className={page === id ? "active" : ""}
              onClick={() => {
                setPage(id);
                setMobile(false);
              }}
            >
              <Icon name={icon} />
              {!collapsed && <span>{label}</span>}
            </button>
          ))}
        </nav>
        <div className="side-bottom">
          <a
            href="https://www.spaceappschallenge.org/"
            target="_blank"
            rel="noopener noreferrer"
            className={`spaceapps-side-card ${collapsed ? "collapsed" : ""}`}
            title="Built for NASA Space Apps 2026 - Visit official challenge site"
          >
            <div className="spaceapps-side-logo-wrap">
              <img
                src="/images/nasa-space-apps-logo.png"
                alt="NASA Space Apps Challenge"
                className="spaceapps-side-logo"
              />
            </div>
            {!collapsed && (
              <div className="spaceapps-side-info">
                <span className="spaceapps-side-tag">HACKATHON 2026</span>
                <strong className="spaceapps-side-title">NASA Space Apps</strong>
                <span className="spaceapps-side-link">
                  spaceappschallenge.org <Icon name="external" size={11} />
                </span>
              </div>
            )}
          </a>
          {!collapsed && (
            <div>
              <Icon name="satellite" />
              <span>
                <b>NASA data context</b>
                <small>Sample · Last synced 2h ago</small>
              </span>
            </div>
          )}
          <button className="user">
            <span>NP</span>
            {!collapsed && (
              <>
                <b>
                  Nimal Perera<small>Farm manager</small>
                </b>
                <Icon name="chevron" size={14} />
              </>
            )}
          </button>
        </div>
      </aside>
      <div className="app-main">
        <header className="topbar">
          <button className="icon-btn mobile-menu show" onClick={() => setMobile(true)}>
            <Icon name="menu" />
          </button>
          <div className="search">
            <Icon name="search" size={18} />
            <input placeholder="Search fields, plans, or insights..." />
            <kbd>⌘ K</kbd>
          </div>
          <div className="top-actions">
            <a
              href="https://www.spaceappschallenge.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="spaceapps-topbar-badge"
              title="Built for NASA Space Apps Challenge 2026 (spaceappschallenge.org)"
            >
              <img
                src="/images/nasa-space-apps-logo.png"
                alt="NASA Space Apps Challenge"
                className="spaceapps-topbar-logo"
              />
              <span className="spaceapps-topbar-text">
                Built for <strong>NASA Space Apps 2026</strong>
              </span>
              <Icon name="external" size={12} className="spaceapps-topbar-ext" />
            </a>
            <span className="data-state">
              <i /> Sample data
            </span>
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <button className="icon-btn" onClick={() => setNotice(!notice)}>
              <Icon name="bell" />
              <i />
            </button>
            <button className="help">?</button>
          </div>
          {notice && (
            <div className="notice-pop">
              <b>Notifications</b>
              <p>
                <span className="status-dot" /> Irrigation window opens tomorrow at 6:00 AM.
              </p>
              <p>
                <Icon name="rain" size={17} /> Rain likelihood increased for Friday.
              </p>
            </div>
          )}
        </header>
        <main className="workspace">
          <div className="page-title">
            <div>
              {page === "dashboard" && (
                <span className="greeting-icon">
                  <Icon name="sun" size={18} />
                </span>
              )}
              <h1>{pageMeta[page][0]}</h1>
              <p>{pageMeta[page][1]}</p>
            </div>
            <div>
              {sampleBadge}
              {page !== "setup" && (
                <Button variant="secondary" icon="download">
                  Export
                </Button>
              )}
              {!["dashboard", "setup", "saved"].includes(page) && (
                <Button icon="plus">New plan</Button>
              )}
            </div>
          </div>
          {coreJourney.some(([id]) => id === page) && <CoreJourney page={page} setPage={setPage} />}
          <Page page={page} setPage={setPage} />
        </main>
      </div>
    </div>
  );
}

function MapVisual({ world = false }: { world?: boolean }) {
  return (
    <div className={`map-visual ${world ? "world" : ""}`}>
      {!world && (
        <img
          src="https://images.unsplash.com/photo-1775762951322-d382fcb43fef?auto=format&fit=crop&w=1200&q=75"
          alt="Aerial fields used as sample farm map"
        />
      )}
      {world ? (
        <>
          <div className="world-shape">◖</div>
          <div className="world-shape two">◗</div>
          {[
            ["Sri Lanka", "63%", "47%"],
            ["Ghana", "25%", "43%"],
            ["Brazil", "39%", "70%"],
            ["Vietnam", "72%", "39%"],
          ].map(([n, x, y], i) => (
            <button className={`map-pin p${i}`} style={{ left: x, top: y }} key={n}>
              <span />
              <b>{n}</b>
            </button>
          ))}
        </>
      ) : (
        <>
          <svg viewBox="0 0 600 320" preserveAspectRatio="none">
            <path
              d="M80 55 275 40 320 145 260 280 65 245Z"
              fill="rgba(16,185,129,.28)"
              stroke="#fff"
              strokeWidth="3"
            />
            <path
              d="m325 60 190 30 22 150-210 35-45-120Z"
              fill="rgba(245,178,66,.25)"
              stroke="#fff"
              strokeWidth="3"
            />
          </svg>
          <div className="field-label a">Field A · Rice</div>
          <div className="field-label b">Field B · Maize</div>
        </>
      )}
      <div className="map-controls">
        <button>+</button>
        <button>−</button>
      </div>
      <span className="map-source">
        <Icon name="satellite" size={13} /> Simulated map layer
      </span>
    </div>
  );
}

function FarmSetup({ setPage }: { setPage: (page: string) => void }) {
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "Green Valley Farm",
    location: "Matale, Sri Lanka",
    size: "32.4",
    unit: "hectares",
    soil: "Clay loam",
    irrigation: "Canal + farm pond",
  });
  const update = (key: keyof typeof form, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));
  const continueSetup = () => {
    if (!form.name.trim() || !form.location.trim() || !form.size.trim()) {
      setError("Add a farm name, location, and farm size before continuing.");
      return;
    }
    setError("");
    if (step < 3) {
      setStep(step + 1);
      return;
    }
    setSaving(true);
    window.setTimeout(() => {
      setSaving(false);
      setPage("dashboard");
    }, 900);
  };
  return (
    <div className="farm-setup">
      <div className="setup-intro">
        <div>
          <span className="section-kicker">FARM PROFILE</span>
          <h2>Tell AgroSphere about your farm.</h2>
          <p>
            These details shape the sample recommendations, water budgets, and climate scenarios
            shown throughout the prototype.
          </p>
        </div>
        <div className="setup-progress" aria-label={`Farm setup step ${step} of 3`}>
          {["Farm details", "Fields & water", "Review"].map((label, index) => (
            <button
              key={label}
              className={`${index + 1 === step ? "active" : ""} ${index + 1 < step ? "complete" : ""}`}
              onClick={() => index + 1 <= step && setStep(index + 1)}
            >
              <i>{index + 1 < step ? <Icon name="check" size={13} /> : index + 1}</i>
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>
      {error && (
        <div className="form-alert error" role="alert">
          <Icon name="info" size={18} />
          <div>
            <b>Complete the required details</b>
            <p>{error}</p>
          </div>
          <button onClick={() => setError("")} aria-label="Dismiss error">
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
      <div className="setup-grid">
        <Card className="setup-form-card">
          {step === 1 && (
            <>
              <SectionHead
                title="Farm details"
                sub="Required fields are marked with an asterisk."
              />
              <div className="field-grid">
                <label className="field span-two">
                  <span>Farm name *</span>
                  <input
                    value={form.name}
                    onChange={(e) => update("name", e.target.value)}
                    aria-invalid={!!error && !form.name}
                    placeholder="e.g. Green Valley Farm"
                  />
                  <small>Used in saved plans and exported reports.</small>
                </label>
                <label className="field span-two">
                  <span>Primary location *</span>
                  <div className="input-icon">
                    <Icon name="location" size={16} />
                    <input
                      value={form.location}
                      onChange={(e) => update("location", e.target.value)}
                      aria-invalid={!!error && !form.location}
                      placeholder="Town, district, country"
                    />
                  </div>
                  <small>Sample coordinates: 7.4675° N, 80.6234° E</small>
                </label>
                <label className="field">
                  <span>Total farm size *</span>
                  <input
                    type="number"
                    min="0"
                    value={form.size}
                    onChange={(e) => update("size", e.target.value)}
                    aria-invalid={!!error && !form.size}
                  />
                </label>
                <label className="field">
                  <span>Measurement unit</span>
                  <select value={form.unit} onChange={(e) => update("unit", e.target.value)}>
                    <option>hectares</option>
                    <option>acres</option>
                  </select>
                </label>
                <label className="field">
                  <span>Primary soil type</span>
                  <select value={form.soil} onChange={(e) => update("soil", e.target.value)}>
                    <option>Clay loam</option>
                    <option>Sandy loam</option>
                    <option>Silt loam</option>
                    <option>Not sure</option>
                  </select>
                </label>
                <label className="field">
                  <span>Primary language</span>
                  <select>
                    <option>English</option>
                    <option>සිංහල</option>
                    <option>தமிழ்</option>
                  </select>
                </label>
              </div>
            </>
          )}
          {step === 2 && (
            <>
              <SectionHead
                title="Fields and water access"
                sub="Review the sample field boundary and available water sources."
              />
              <div className="field-list">
                {[
                  ["Field A", "12.6 ha", "Rice", "Healthy"],
                  ["Field B", "8.2 ha", "Maize", "Monitor"],
                  ["Field C", "7.4 ha", "Vegetables", "Healthy"],
                  ["Field D", "4.2 ha", "Cover crop", "Healthy"],
                ].map((field) => (
                  <div key={field[0]}>
                    <span className="field-color" />
                    <span>
                      <b>{field[0]}</b>
                      <small>
                        {field[1]} · {field[2]}
                      </small>
                    </span>
                    <em>{field[3]}</em>
                    <button aria-label={`Edit ${field[0]}`}>Edit</button>
                  </div>
                ))}
              </div>
              <button className="add-field">
                <Icon name="plus" size={17} /> Add another field
              </button>
              <label className="field setup-select">
                <span>Primary irrigation source</span>
                <select
                  value={form.irrigation}
                  onChange={(e) => update("irrigation", e.target.value)}
                >
                  <option>Canal + farm pond</option>
                  <option>Rain-fed only</option>
                  <option>Groundwater well</option>
                  <option>Community irrigation</option>
                </select>
              </label>
            </>
          )}
          {step === 3 && (
            <>
              <SectionHead
                title="Review your farm profile"
                sub="You can change these details later in Settings."
              />
              <div className="review-list">
                {[
                  ["Farm", form.name],
                  ["Location", form.location],
                  ["Total area", `${form.size} ${form.unit}`],
                  ["Fields", "4 mapped fields"],
                  ["Soil", form.soil],
                  ["Water", form.irrigation],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span>{label}</span>
                    <b>{value}</b>
                    <button
                      onClick={() => setStep(label === "Farm" || label === "Location" ? 1 : 2)}
                    >
                      Edit
                    </button>
                  </div>
                ))}
              </div>
              <div className="consent-note">
                <Icon name="shield" size={19} />
                <span>
                  <b>Prototype privacy</b>
                  Farm details remain in this browser demonstration and are not sent to a backend.
                </span>
              </div>
            </>
          )}
          <div className="setup-actions">
            <button
              className="btn btn-secondary"
              onClick={() => (step > 1 ? setStep(step - 1) : setPage("dashboard"))}
            >
              {step > 1 ? "Back" : "Use sample farm"}
            </button>
            <button className="btn btn-primary" onClick={continueSetup} disabled={saving}>
              {saving ? (
                <>
                  <i className="spinner" /> Preparing dashboard…
                </>
              ) : step === 3 ? (
                <>
                  Save farm & continue <Icon name="arrow" size={17} />
                </>
              ) : (
                <>
                  Continue <Icon name="arrow" size={17} />
                </>
              )}
            </button>
          </div>
        </Card>
        <div className="setup-aside">
          <Card className="setup-map">
            <SectionHead
              title="Sample farm boundary"
              sub="Illustrative boundary · Not a cadastral map"
            />
            <MapVisual />
            <button>
              <Icon name="upload" size={16} /> Upload GeoJSON or draw boundary
            </button>
          </Card>
          <Card className="setup-help">
            <Icon name="info" />
            <div>
              <b>Why AgroSphere asks</b>
              <p>
                Location and field area help express rainfall, soil moisture, and water requirements
                with the correct units and spatial context.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Dashboard({ setPage }: { setPage: (p: string) => void }) {
  return (
    <div className="dashboard">
      <div className="alert-banner">
        <div className="alert-icon">
          <Icon name="spark" />
        </div>
        <div>
          <b>One opportunity needs your attention</b>
          <p>
            Switching Field B to mung bean next season may lower water demand by 18% and improve
            soil nitrogen.
          </p>
        </div>
        <button onClick={() => setPage("rotation")}>
          Review recommendation <Icon name="arrow" size={16} />
        </button>
        <Icon name="info" size={17} />
      </div>
      <div className="metric-grid">
        {[
          ["Farm health", "87", "/ 100", "+4 this month", "trend"],
          ["Soil moisture", "64", "%", "Good range", "water"],
          ["Water outlook", "28", "days", "Moderate risk", "rain"],
          ["Active fields", "4", "/ 5", "32.4 hectares", "leaf"],
        ].map(([l, v, u, n, i], x) => (
          <Card className="metric" key={l}>
            <div>
              <span>{l}</span>
              <i className={`metric-icon m${x}`}>
                <Icon name={i as IconName} />
              </i>
            </div>
            <strong>
              {v}
              <small>{u}</small>
            </strong>
            <p className={x === 2 ? "warn" : ""}>
              <Icon name={x === 2 ? "info" : "trend"} size={14} />
              {n}
            </p>
          </Card>
        ))}
      </div>
      <div className="dash-grid">
        <Card className="map-card">
          <SectionHead
            title="Farm overview"
            sub="Green Valley · 32.4 ha"
            action={
              <button className="text-btn">
                Manage fields <Icon name="arrow" size={15} />
              </button>
            }
          />
          <MapVisual />
          <div className="map-legend">
            <span>
              <i className="green" />
              Healthy
            </span>
            <span>
              <i className="amber" />
              Monitor
            </span>
            <span>
              <i className="white" />
              Field boundary
            </span>
            <b>Imagery is illustrative</b>
          </div>
        </Card>
        <Card className="weather-card">
          <SectionHead title="Today’s conditions" sub="Matale, Sri Lanka" />
          <div className="today">
            <Icon name="sun" size={52} />
            <strong>
              29°<small>Feels like 31°</small>
            </strong>
            <span>
              Partly cloudy<small>High 31° · Low 23°</small>
            </span>
          </div>
          <div className="weather-metrics">
            <div>
              <Icon name="rain" />
              <span>
                Rainfall<b>2.4 mm</b>
              </span>
            </div>
            <div>
              <Icon name="wind" />
              <span>
                Wind<b>11 km/h</b>
              </span>
            </div>
            <div>
              <Icon name="water" />
              <span>
                Humidity<b>72%</b>
              </span>
            </div>
          </div>
          <div className="forecast">
            {["Today", "Tue", "Wed", "Thu", "Fri"].map((d, i) => (
              <div key={d}>
                <span>{d}</span>
                <Icon name={i === 3 ? "rain" : i === 2 ? "climate" : "sun"} />
                <b>{[29, 30, 31, 27, 28][i]}°</b>
              </div>
            ))}
          </div>
          <button className="full-link">
            View weather history <Icon name="arrow" size={15} />
          </button>
        </Card>
        <Card className="trend-card">
          <SectionHead
            title="Farm performance"
            sub="Last 6 months"
            action={
              <select>
                <option>All fields</option>
              </select>
            }
          />
          <div className="chart-legend">
            <span>
              <i />
              Vegetation health
            </span>
            <span>
              <i />
              Soil moisture
            </span>
          </div>
          <div className="large-chart">
            <div className="ylabels">
              <span>100</span>
              <span>75</span>
              <span>50</span>
              <span>25</span>
            </div>
            <svg viewBox="0 0 600 170" preserveAspectRatio="none">
              <path className="gridline" d="M0 15h600M0 55h600M0 95h600M0 135h600" />
              <path
                d="M0 125 C70 110 90 90 145 92 S220 120 285 68 S390 92 460 42 S540 48 600 20"
                className="line green"
              />
              <path
                d="M0 105 C70 95 100 120 160 100 S250 70 315 85 S420 65 470 78 S550 48 600 60"
                className="line blue"
              />
            </svg>
            <div className="xlabels">
              <span>Jan</span>
              <span>Feb</span>
              <span>Mar</span>
              <span>Apr</span>
              <span>May</span>
              <span>Jun</span>
            </div>
          </div>
        </Card>
        <Card className="tasks-card">
          <SectionHead
            title="Upcoming tasks"
            action={
              <button className="icon-btn">
                <Icon name="plus" size={18} />
              </button>
            }
          />
          {[
            ["Tomorrow", "Inspect drip lines", "Field C · 7:30 AM", "water"],
            ["May 28", "Apply compost", "Field A · 6:00 AM", "soil"],
            ["Jun 02", "Scout for leaf curl", "Field B · Morning", "scan"],
          ].map(([d, t, s, i]) => (
            <div className="task" key={t}>
              <span>{d}</span>
              <i>
                <Icon name={i as IconName} />
              </i>
              <div>
                <b>{t}</b>
                <small>{s}</small>
              </div>
              <button>
                <Icon name="chevron" size={16} />
              </button>
            </div>
          ))}
          <button className="full-link" onClick={() => setPage("calendar")}>
            Open farm calendar <Icon name="arrow" size={15} />
          </button>
        </Card>
      </div>
      <DataProvenance compact />
    </div>
  );
}

function Rotation() {
  const [goal, setGoal] = useState("Balanced");
  const [season, setSeason] = useState(4);
  const crops = [
    ["Rice", "R", "rice"],
    ["Mung bean", "M", "mung"],
    ["Maize", "M", "maize"],
    ["Groundnut", "G", "ground"],
    ["Cowpea", "C", "cow"],
    ["Vegetables", "V", "veg"],
  ];
  return (
    <div className="rotation-page">
      <div className="planner-steps">
        <span className="active">
          <b>1</b>Goals & crops
        </span>
        <i />
        <span className="active">
          <b>2</b>Build rotation
        </span>
        <i />
        <span>
          <b>3</b>Compare plans
        </span>
      </div>
      <div className="planner-grid">
        <div className="planner-left">
          <Card>
            <SectionHead title="1. What matters most?" sub="Set your optimization priorities" />
            <div className="goal-grid">
              {["Balanced", "Maximize income", "Save water", "Restore soil"].map((g, i) => (
                <button className={goal === g ? "selected" : ""} onClick={() => setGoal(g)} key={g}>
                  <Icon name={(["grid", "wallet", "water", "soil"] as IconName[])[i]} />
                  <b>{g}</b>
                  <small>
                    {
                      [
                        "Recommended mix of goals",
                        "Higher return potential",
                        "Prioritize low demand",
                        "Build soil organic matter",
                      ][i]
                    }
                  </small>
                  {goal === g && (
                    <span>
                      <Icon name="check" size={13} />
                    </span>
                  )}
                </button>
              ))}
            </div>
            <div className="priority">
              <div>
                <span>Income priority</span>
                <b>65%</b>
              </div>
              <input type="range" defaultValue="65" />
              <div>
                <span>Resilience priority</span>
                <b>80%</b>
              </div>
              <input type="range" defaultValue="80" />
            </div>
          </Card>
          <Card>
            <SectionHead title="2. Select available crops" sub="Choose at least three crops" />
            <div className="crop-grid">
              {crops.map(([c, l, k], i) => (
                <button className={i < 4 ? "selected" : ""} key={c}>
                  <span className={k}>{l}</span>
                  <b>{c}</b>
                  {i < 4 && (
                    <i>
                      <Icon name="check" size={12} />
                    </i>
                  )}
                </button>
              ))}
            </div>
            <button className="add-crop">
              <Icon name="plus" size={17} /> Add custom crop
            </button>
          </Card>
        </div>
        <Card className="rotation-build">
          <SectionHead
            title="3. Build your rotation"
            sub={`${season} seasons · Field B (8.2 ha)`}
            action={
              <select value={season} onChange={(e) => setSeason(+e.target.value)}>
                <option value="3">3 seasons</option>
                <option value="4">4 seasons</option>
                <option value="5">5 seasons</option>
              </select>
            }
          />
          <div className="timeline">
            {Array.from({ length: season }).map((_, i) => {
              const vals = [
                ["Yala 2026", "Rice", "R", "rice"],
                ["Maha 2026", "Mung bean", "M", "mung"],
                ["Yala 2027", "Maize", "M", "maize"],
                ["Maha 2027", "Groundnut", "G", "ground"],
                ["Yala 2028", "Rice", "R", "rice"],
              ][i];
              return (
                <div className="season" key={i}>
                  <div>
                    <span>{vals[0]}</span>
                    <small>{i % 2 ? "Oct – Feb" : "May – Sep"}</small>
                  </div>
                  <button>
                    <i className={vals[3]}>{vals[2]}</i>
                    <span>
                      <b>{vals[1]}</b>
                      <small>
                        {i === 1
                          ? "+ Nitrogen fixing"
                          : i === 3
                            ? "Low water need"
                            : "Moderate water"}
                      </small>
                    </span>
                    <Icon name="chevron" size={16} />
                  </button>
                  {i < season - 1 && (
                    <em>
                      <Icon name="arrow" size={15} />
                    </em>
                  )}
                </div>
              );
            })}
          </div>
          <div className="constraint-box">
            <Icon name="shield" />
            <div>
              <b>Constraints checked</b>
              <p>No crop repeats · Water budget respected · Market window aligned</p>
            </div>
            <span>3/3 passed</span>
          </div>
          <Button>
            Optimize rotation <Icon name="spark" size={17} />
          </Button>
          <p className="model-note">
            <Icon name="info" size={14} /> Prototype optimization uses illustrative rules, not a
            trained AI model.
          </p>
        </Card>
      </div>
      <SectionHead
        title="Recommended plans"
        sub={`Optimized for: ${goal}`}
        action={
          <button className="text-btn">
            How ranking works <Icon name="info" size={15} />
          </button>
        }
      />
      <div className="plans">
        {[
          ["A", "Resilient balance", "92", "Recommended", "+18%", "−22%", "+14%"],
          ["B", "Income first", "86", "High return", "+26%", "−8%", "+6%"],
          ["C", "Water saver", "81", "Lowest demand", "+11%", "−34%", "+17%"],
        ].map((p, i) => (
          <Card className={i === 0 ? "recommended" : ""} key={p[0]}>
            {i === 0 && (
              <span className="recommend-label">
                <Icon name="spark" size={13} /> BEST MATCH
              </span>
            )}
            <div className="plan-head">
              <span>{p[0]}</span>
              <div>
                <b>{p[1]}</b>
                <small>{p[3]}</small>
              </div>
              <strong>
                {p[2]}
                <small>/100</small>
              </strong>
            </div>
            <div className="plan-crops">
              {["R", "M", "M", "G"].map((c, x) => (
                <span key={x} className={["rice", "mung", "maize", "ground"][x]}>
                  {c}
                </span>
              ))}
            </div>
            <div className="plan-metrics">
              <span>
                Net income <b>{p[4]}</b>
              </span>
              <span>
                Water use <b>{p[5]}</b>
              </span>
              <span>
                Soil score <b>{p[6]}</b>
              </span>
            </div>
            <div className="confidence">
              <span>Confidence: {i === 0 ? "High" : "Medium"}</span>
              <span>
                <i style={{ width: `${92 - i * 11}%` }} />
              </span>
            </div>
            <Button variant={i === 0 ? "primary" : "secondary"}>
              View full plan <Icon name="arrow" size={16} />
            </Button>
          </Card>
        ))}
      </div>
      <Card className="comparison">
        <SectionHead title="Before & after" sub="Current practice compared with Plan A" />
        <div className="compare-grid">
          {[
            ["Estimated income", "$12.8k", "$15.1k", "+18%"],
            ["Water demand", "4,820 m³", "3,760 m³", "−22%"],
            ["Soil health", "58 / 100", "72 / 100", "+14 pts"],
            ["Climate risk", "High", "Moderate", "Improved"],
          ].map((r) => (
            <div key={r[0]}>
              <span>{r[0]}</span>
              <del>{r[1]}</del>
              <Icon name="arrow" size={15} />
              <b>{r[2]}</b>
              <em>{r[3]}</em>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Climate() {
  const [rain, setRain] = useState(-15),
    [temp, setTemp] = useState(2),
    [scenario, setScenario] = useState("Moderate drought");
  const score = Math.max(35, 86 - Math.abs(rain) / 3 - temp * 5);
  return (
    <div className="climate-page">
      <div className="scenario-strip">
        <span>Scenario</span>
        {["Normal season", "Moderate drought", "Severe drought", "Extreme heat"].map((s) => (
          <button
            className={scenario === s ? "active" : ""}
            onClick={() => {
              setScenario(s);
              if (s === "Normal season") {
                setRain(0);
                setTemp(0);
              } else if (s === "Moderate drought") {
                setRain(-15);
                setTemp(2);
              } else if (s === "Severe drought") {
                setRain(-35);
                setTemp(3);
              } else {
                setRain(-10);
                setTemp(5);
              }
            }}
            key={s}
          >
            {s}
          </button>
        ))}
        <button className="save">Save scenario</button>
      </div>
      <div className="sim-grid">
        <Card className="controls">
          <SectionHead title="Climate assumptions" sub="Adjust conditions for Maha 2026" />
          <label>
            <span>
              Seasonal rainfall{" "}
              <b>
                {rain > 0 ? "+" : ""}
                {rain}%
              </b>
            </span>
            <input
              type="range"
              min="-50"
              max="30"
              value={rain}
              onChange={(e) => setRain(+e.target.value)}
            />
            <small>
              <i>−50%</i>
              <i>Historical average</i>
              <i>+30%</i>
            </small>
          </label>
          <label>
            <span>
              Temperature change <b>+{temp}°C</b>
            </span>
            <input
              className="temp-range"
              type="range"
              min="0"
              max="6"
              step=".5"
              value={temp}
              onChange={(e) => setTemp(+e.target.value)}
            />
            <small>
              <i>0°C</i>
              <i>+3°C</i>
              <i>+6°C</i>
            </small>
          </label>
          <label>
            <span>
              Water availability <b>70%</b>
            </span>
            <input type="range" defaultValue="70" />
            <small>
              <i>Limited</i>
              <i>Normal</i>
              <i>Abundant</i>
            </small>
          </label>
          <div className="toggle-row">
            <div>
              <b>Include pest pressure</b>
              <small>Adjust risk using climate response</small>
            </div>
            <button className="toggle on">
              <i />
            </button>
          </div>
          <Button>
            Run simulation <Icon name="play" size={16} />
          </Button>
          <p className="model-note">
            <Icon name="info" size={14} /> Scenario outputs are illustrative estimates.
          </p>
        </Card>
        <Card className="outcome">
          <SectionHead
            title="Scenario outcome"
            sub={`${scenario} · Plan A`}
            action={
              <span className={`risk ${score < 65 ? "high" : ""}`}>
                {score < 65 ? "High" : "Moderate"} risk
              </span>
            }
          />
          <div
            className="score-ring"
            style={{ "--score": `${score * 3.6}deg` } as React.CSSProperties}
          >
            <div>
              <strong>{Math.round(score)}</strong>
              <span>Resilience score</span>
            </div>
          </div>
          <p className="outcome-copy">
            Your rotation remains{" "}
            <b>{score > 65 ? "viable with adaptation" : "at risk under this scenario"}</b>. Mung
            bean helps buffer lower rainfall, but maize needs supplemental irrigation.
          </p>
          <div className="outcome-metrics">
            <div>
              <Icon name="trend" />
              <span>
                Yield change<b>{Math.round(rain / 2 - temp * 2)}%</b>
                <small>vs. normal season</small>
              </span>
            </div>
            <div>
              <Icon name="water" />
              <span>
                Water gap<b>{Math.abs(Math.round(rain * 18))} m³</b>
                <small>during peak demand</small>
              </span>
            </div>
            <div>
              <Icon name="wallet" />
              <span>
                Income impact<b>−${Math.abs(Math.round(rain * 48 + temp * 60))}</b>
                <small>illustrative estimate</small>
              </span>
            </div>
          </div>
          <div className="recommend-box">
            <Icon name="spark" />
            <div>
              <b>Adaptation opportunity</b>
              <p>
                Shift maize planting 2 weeks earlier and reserve 340 m³ irrigation for flowering.
              </p>
            </div>
            <button>Apply to plan</button>
          </div>
        </Card>
      </div>
      <Card className="scenario-chart">
        <SectionHead
          title="Plan comparison under this scenario"
          sub="Projected yield index across the season"
          action={
            <div className="chart-tabs">
              <button className="active">Yield</button>
              <button>Water</button>
              <button>Income</button>
            </div>
          }
        />
        <div className="chart-legend">
          <span>
            <i />
            Plan A · Resilient
          </span>
          <span>
            <i />
            Current practice
          </span>
          <span>
            <i />
            Normal baseline
          </span>
        </div>
        <div className="scenario-graph">
          <div className="ylabels">
            <span>100</span>
            <span>80</span>
            <span>60</span>
            <span>40</span>
            <span>20</span>
          </div>
          <svg viewBox="0 0 900 220" preserveAspectRatio="none">
            <path className="gridline" d="M0 15h900M0 60h900M0 105h900M0 150h900M0 195h900" />
            <path
              d="M0 160 C130 140 140 95 260 90 S400 115 490 70 S680 45 900 35"
              className="line green"
            />
            <path
              d="M0 170 C140 155 180 130 280 145 S400 160 500 125 S650 118 730 100 S830 105 900 90"
              className="line amber"
            />
            <path d="M0 120 C180 100 320 98 450 90 S700 75 900 60" className="line dashed" />
          </svg>
          <div className="xlabels">
            <span>Planting</span>
            <span>Establishment</span>
            <span>Vegetative</span>
            <span>Flowering</span>
            <span>Harvest</span>
          </div>
        </div>
        <div className="uncertainty">
          <Icon name="info" />
          <span>
            <b>Uncertainty range: ±12%</b>Based on variability in rainfall timing and soil moisture
            assumptions.
          </span>
          <button>View methodology</button>
        </div>
      </Card>
      <div className="risk-grid">
        {[
          ["water", "Water stress", "High", "Maize flowering stage is most exposed."],
          ["scan", "Pest & disease", "Moderate", "Warmer nights may increase leaf curl risk."],
          ["soil", "Soil resilience", "Strong", "Legume sequence supports moisture retention."],
        ].map(([i, t, r, d], x) => (
          <Card key={t}>
            <i className={`risk-icon r${x}`}>
              <Icon name={i as IconName} />
            </i>
            <div>
              <span>{t}</span>
              <b>{r}</b>
              <p>{d}</p>
            </div>
            <button>
              <Icon name="chevron" size={16} />
            </button>
          </Card>
        ))}
      </div>
      <DataProvenance compact />
    </div>
  );
}

function Water() {
  const [irrigation, setIrrigation] = useState(68);
  return (
    <div>
      <div className="metric-grid">
        {[
          ["Expected rainfall", "620", "mm", "12% below average", "rain"],
          ["Irrigation supply", `${irrigation}`, "%", "2,140 m³ available", "water"],
          ["Crop requirement", "3,420", "m³", "Across 4 fields", "leaf"],
          ["Projected balance", "−380", "m³", "Gap in late August", "info"],
        ].map(([l, v, u, n, i], x) => (
          <Card className="metric" key={l}>
            <div>
              <span>{l}</span>
              <i className={`metric-icon m${x}`}>
                <Icon name={i as IconName} />
              </i>
            </div>
            <strong>
              {v}
              <small>{u}</small>
            </strong>
            <p className={x === 3 ? "warn" : ""}>{n}</p>
          </Card>
        ))}
      </div>
      <div className="two-col">
        <Card>
          <SectionHead title="Supply assumptions" sub="Maha 2026" />
          <div className="form-row">
            <label>
              Rainfall reliability <b>75%</b>
              <input type="range" defaultValue="75" />
            </label>
            <label>
              Irrigation availability <b>{irrigation}%</b>
              <input
                type="range"
                value={irrigation}
                onChange={(e) => setIrrigation(+e.target.value)}
              />
            </label>
          </div>
          <div className="water-sources">
            {[
              ["rain", "Rainfall", "1,930 m³", "56%"],
              ["water", "Canal allocation", "1,480 m³", "38%"],
              ["water", "Farm pond", "210 m³", "6%"],
            ].map((r) => (
              <div key={r[1]}>
                <Icon name={r[0] as IconName} />
                <span>
                  {r[1]}
                  <small>{r[2]}</small>
                </span>
                <b>{r[3]}</b>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <SectionHead title="Water balance" sub="Supply versus crop demand" />
          <div className="donut-wrap">
            <div className="donut">
              <span>
                <b>{Math.round(82 + irrigation / 10)}%</b>covered
              </span>
            </div>
            <div>
              <p>
                <i className="green" />
                Available <b>3,620 m³</b>
              </p>
              <p>
                <i className="amber" />
                Required <b>4,000 m³</b>
              </p>
              <p>
                <i className="red" />
                Gap <b>380 m³</b>
              </p>
            </div>
          </div>
          <div className="recommend-box">
            <Icon name="spark" />
            <div>
              <b>Close 76% of the gap</b>
              <p>Move Field C planting by 12 days and use mulch during establishment.</p>
            </div>
          </div>
        </Card>
      </div>
      <Card className="budget-chart">
        <SectionHead title="Monthly water budget" sub="All values are illustrative estimates" />
        <div className="mini-bars big">
          {[58, 70, 88, 64, 45, 32].map((v, i) => (
            <i key={i} style={{ height: `${v}%` }}>
              <span>{["May", "Jun", "Jul", "Aug", "Sep", "Oct"][i]}</span>
            </i>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Soil() {
  return (
    <div>
      <div className="health-hero card">
        <div>
          <span>SOIL HEALTH SCORE</span>
          <strong>
            72<small>/100</small>
          </strong>
          <p>
            <Icon name="trend" /> 8 points since last season
          </p>
        </div>
        <div className="soil-rings">
          {[
            ["Organic matter", "2.8%", "Good"],
            ["pH", "6.4", "Optimal"],
            ["Nitrogen", "42 ppm", "Monitor"],
            ["Compaction", "Low", "Good"],
          ].map((r, i) => (
            <div key={r[0]}>
              <span className={`ring r${i}`}>{r[1]}</span>
              <b>{r[0]}</b>
              <small>{r[2]}</small>
            </div>
          ))}
        </div>
      </div>
      <div className="two-col">
        <Card>
          <SectionHead
            title="Latest soil test"
            sub="Field B · May 12, 2026"
            action={<Button variant="secondary">Add test</Button>}
          />
          {[
            ["Soil organic carbon", "1.62%", "Healthy", "82"],
            ["Available nitrogen", "42 ppm", "Monitor", "58"],
            ["Phosphorus", "18 ppm", "Healthy", "76"],
            ["Potassium", "148 ppm", "Healthy", "88"],
          ].map((r) => (
            <div className="test-row" key={r[0]}>
              <span>{r[0]}</span>
              <div>
                <i>
                  <em style={{ width: `${r[3]}%` }} />
                </i>
                <small>{r[1]}</small>
              </div>
              <b>{r[2]}</b>
            </div>
          ))}
        </Card>
        <Card>
          <SectionHead title="Recovery plan" sub="After seasonal drought" />
          {[
            ["1", "Plant sunn hemp cover crop", "Jun 08 – Jul 20", "In progress"],
            ["2", "Apply compost at 2 t/ha", "Jul 22", "Upcoming"],
            ["3", "Minimum-till bed preparation", "Aug 14", "Planned"],
          ].map((r) => (
            <div className="recovery-step" key={r[0]}>
              <span>{r[0]}</span>
              <div>
                <b>{r[1]}</b>
                <small>{r[2]}</small>
              </div>
              <em>{r[3]}</em>
            </div>
          ))}
          <Button>
            View full recovery plan <Icon name="arrow" />
          </Button>
        </Card>
      </div>
      <Card>
        <SectionHead
          title="Diversity & resilience"
          sub="How your rotation supports soil recovery"
        />
        <div className="indicator-grid">
          {[
            ["leaf", "Crop diversity", "4 families", "Strong"],
            ["soil", "Living roots", "9 months/year", "Good"],
            ["water", "Ground cover", "78%", "Good"],
            ["rotation", "Rotation quality", "No repeats", "Strong"],
          ].map((r) => (
            <div key={r[1]}>
              <Icon name={r[0] as IconName} />
              <span>
                {r[1]}
                <b>{r[2]}</b>
              </span>
              <em>{r[3]}</em>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Weeds() {
  const input = useRef<HTMLInputElement>(null),
    [uploaded, setUploaded] = useState(false);
  return (
    <div className="weed-grid">
      <Card className="upload-card">
        <SectionHead title="Field image" sub="Upload a clear overhead crop image" />
        {uploaded ? (
          <div className="uploaded">
            <img
              src="https://images.unsplash.com/photo-1613482390018-6cb1e20c39d0?auto=format&fit=crop&w=900&q=80"
              alt="Sample green field for weed analysis"
            />
            <div className="scan-overlay">
              <i />
              <i />
              <i />
            </div>
            <button onClick={() => setUploaded(false)}>
              <Icon name="close" />
            </button>
            <span>Sample field image</span>
          </div>
        ) : (
          <button className="dropzone" onClick={() => input.current?.click()}>
            <span>
              <Icon name="upload" size={25} />
            </span>
            <b>Drop a field image here</b>
            <p>or click to browse · JPG, PNG up to 10 MB</p>
            <small>
              <Icon name="info" size={13} /> For this prototype, upload triggers sample analysis.
            </small>
          </button>
        )}
        <input ref={input} hidden type="file" onChange={() => setUploaded(true)} />
        <Button onClick={() => setUploaded(true)}>
          {uploaded ? "Run sample analysis" : "Use sample image"} <Icon name="scan" />
        </Button>
      </Card>
      <Card className="analysis-card">
        <SectionHead
          title="Analysis results"
          sub={uploaded ? "Illustrative visual estimate" : "Waiting for an image"}
          action={uploaded ? <span className="risk">Sample result</span> : null}
        />
        {uploaded ? (
          <>
            <div className="coverage">
              <div className="donut weed">
                <span>
                  <b>18%</b>coverage
                </span>
              </div>
              <div>
                <span>Estimated weed pressure</span>
                <strong>Moderate</strong>
                <p>Likely concentrated along the north field edge.</p>
              </div>
            </div>
            <div className="species">
              <b>Possible visual matches</b>
              <div>
                <span>
                  Nutgrass <em>44% visual similarity</em>
                </span>
                <i style={{ width: "44%" }} />
              </div>
              <div>
                <span>
                  Crowfoot grass <em>31% visual similarity</em>
                </span>
                <i style={{ width: "31%" }} />
              </div>
            </div>
            <div className="prototype-note">
              <Icon name="info" />
              <span>
                <b>Not a diagnosis</b>This is a simulated interface—not a trained image recognition
                model. Confirm with an agronomist.
              </span>
            </div>
          </>
        ) : (
          <div className="empty">
            <span>
              <Icon name="scan" size={34} />
            </span>
            <b>Your results will appear here</b>
            <p>Upload an image to see weed coverage and sample visual matches.</p>
          </div>
        )}
      </Card>
    </div>
  );
}

function Twin() {
  const [region, setRegion] = useState("Ghana");
  return (
    <div>
      <Card className="twin-map">
        <SectionHead
          title="Climate similarity map"
          sub="Regions with comparable rainfall, temperature, and seasonality"
          action={
            <div className="search mini">
              <Icon name="search" />
              <input placeholder="Find a region" />
            </div>
          }
        />
        <MapVisual world />
      </Card>
      <div className="twin-grid">
        {[
          ["Ghana", "Upper East", "89", "Sorghum · Cowpea", "Dry-season water harvesting"],
          ["Brazil", "Cerrado", "84", "Maize · Soy", "No-till soil cover"],
          ["Vietnam", "Central Highlands", "79", "Rice · Legumes", "Contour water management"],
        ].map((r, i) => (
          <Card
            className={region === r[0] ? "selected" : ""}
            key={r[0]}
            onClick={() => setRegion(r[0])}
          >
            <div className="match">
              <span>{r[2]}%</span>
              <div>
                <b>{r[0]}</b>
                <small>{r[1]}</small>
              </div>
              <em>Climate match</em>
            </div>
            <p>
              <Icon name="leaf" />
              {r[3]}
            </p>
            <p>
              <Icon name="spark" />
              {r[4]}
            </p>
            <Button variant={i === 0 ? "primary" : "secondary"}>
              Explore lessons <Icon name="arrow" />
            </Button>
          </Card>
        ))}
      </div>
      <Card className="provenance">
        <Icon name="globe" />
        <div>
          <b>How similarity is estimated</b>
          <p>
            Prototype scores compare sample monthly rainfall, temperature, elevation, and
            seasonality—not live data.
          </p>
        </div>
        <button>View methodology</button>
      </Card>
    </div>
  );
}

function Assistant() {
  const [messages, setMessages] = useState<string[]>([
    "How can I reduce water risk for Field B this season?",
  ]);
  const [text, setText] = useState(""),
    [lang, setLang] = useState("English");
  const send = () => {
    if (text.trim()) {
      setMessages([...messages, text]);
      setText("");
    }
  };
  return (
    <div className="assistant-layout">
      <Card className="chat-panel">
        <div className="chat-head">
          <span>
            <Icon name="spark" />
          </span>
          <div>
            <b>Agro Assistant</b>
            <small>
              <i /> Prototype · Sample responses
            </small>
          </div>
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            <option>English</option>
            <option>සිංහල</option>
            <option>தமிழ்</option>
          </select>
        </div>
        <div className="messages">
          <div className="bot-message">
            <span>
              <Icon name="leaf" />
            </span>
            <div>
              <p>
                Hello Nimal. I can help you explore farm plans and understand sample
                recommendations. What would you like to work on?
              </p>
              <small>AgroSphere · now</small>
            </div>
          </div>
          {messages.map((m, i) => (
            <div key={i}>
              <div className="user-message">
                <p>{m}</p>
              </div>
              <div className="bot-message">
                <span>
                  <Icon name="spark" />
                </span>
                <div>
                  <p>
                    Based on your sample plan, the largest water gap appears during maize flowering
                    in late August. Three options could help:
                  </p>
                  <ol>
                    <li>
                      <b>Shift planting 12 days earlier</b> to align peak demand with expected rain.
                    </li>
                    <li>
                      Reserve <b>340 m³</b> of canal allocation for flowering.
                    </li>
                    <li>Add mulch to reduce modeled soil evaporation.</li>
                  </ol>
                  <button>
                    Why these suggestions? <Icon name="info" size={14} />
                  </button>
                  <small>Illustrative response · not agronomic advice</small>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="quick-prompts">
          <button onClick={() => setText("Explain my rotation score")}>
            Explain my rotation score
          </button>
          <button onClick={() => setText("What should I do this week?")}>
            What should I do this week?
          </button>
        </div>
        <div className="chat-input">
          <button>
            <Icon name="plus" />
          </button>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder={`Ask in ${lang}...`}
          />
          <button>
            <Icon name="mic" />
          </button>
          <button onClick={send}>
            <Icon name="arrow" />
          </button>
        </div>
      </Card>
      <aside>
        <Card>
          <SectionHead title="Farm context" />
          {[
            ["location", "Green Valley", "Matale, Sri Lanka"],
            ["leaf", "4 active fields", "32.4 hectares"],
            ["rotation", "Plan A", "Maha 2026"],
          ].map((r) => (
            <div className="context-row" key={r[1]}>
              <Icon name={r[0] as IconName} />
              <span>
                <b>{r[1]}</b>
                <small>{r[2]}</small>
              </span>
            </div>
          ))}
        </Card>
        <Card className="guardrail">
          <Icon name="shield" />
          <b>Responsible assistance</b>
          <p>
            Recommendations show data sources, confidence, and uncertainty. Always confirm
            high-impact decisions locally.
          </p>
        </Card>
      </aside>
    </div>
  );
}

function CalendarPage() {
  const [month, setMonth] = useState(5);
  const days = Array.from({ length: 35 }, (_, i) => i - 1);
  return (
    <div>
      <div className="calendar-tools">
        <div>
          <button onClick={() => setMonth(month - 1)}>
            <Icon name="chevron" className="back" />
          </button>
          <h2>
            {["", "January", "February", "March", "April", "May", "June", "July"][month]} 2026
          </h2>
          <button onClick={() => setMonth(month + 1)}>
            <Icon name="chevron" />
          </button>
          <button>Today</button>
        </div>
        <Button icon="plus">Add task</Button>
      </div>
      <div className="calendar-layout">
        <Card className="month-grid">
          <div className="week">
            {["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"].map((d) => (
              <b key={d}>{d}</b>
            ))}
          </div>
          <div className="days">
            {days.map((d, i) => (
              <div className={d === 26 ? "today" : ""} key={i}>
                <span>{d > 0 && d <= 30 ? d : ""}</span>
                {d === 4 && <em className="plant">Plant rice</em>}
                {d === 12 && <em className="water">Irrigate C</em>}
                {d === 18 && <em className="soil-event">Soil test</em>}
                {d === 26 && <em className="alert">Scout pests</em>}
              </div>
            ))}
          </div>
        </Card>
        <aside>
          <Card>
            <SectionHead title="Upcoming" />
            {[
              ["Tomorrow", "Inspect drip lines", "Field C"],
              ["May 28", "Apply compost", "Field A"],
              ["Jun 02", "Scout leaf curl", "Field B"],
              ["Jun 08", "Plant sunn hemp", "Field D"],
            ].map((r) => (
              <div className="agenda" key={r[1]}>
                <span>{r[0]}</span>
                <div>
                  <b>{r[1]}</b>
                  <small>{r[2]}</small>
                </div>
                <i />
              </div>
            ))}
          </Card>
          <Card className="weather-note">
            <Icon name="rain" />
            <div>
              <b>Rain expected Friday</b>
              <p>Consider moving compost application to Saturday.</p>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function Finance() {
  return (
    <div>
      <div className="metric-grid">
        {[
          ["Projected income", "$15.1k", "", "+18% vs current", "trend"],
          ["Estimated costs", "$6.4k", "", "Seed, labor, inputs", "wallet"],
          ["Net margin", "$8.7k", "", "58% margin", "trend"],
          ["Risk buffer", "$1.2k", "", "Recommended reserve", "shield"],
        ].map(([l, v, u, n, i], x) => (
          <Card className="metric" key={l}>
            <div>
              <span>{l}</span>
              <i className={`metric-icon m${x}`}>
                <Icon name={i as IconName} />
              </i>
            </div>
            <strong>
              {v}
              <small>{u}</small>
            </strong>
            <p>{n}</p>
          </Card>
        ))}
      </div>
      <div className="two-col">
        <Card>
          <SectionHead title="Season cost breakdown" sub="Plan A · Illustrative estimates" />
          <div className="cost-donut">
            <div className="donut finance">
              <span>
                <b>$6,400</b>total costs
              </span>
            </div>
            <div>
              {[
                ["Seeds", "28%"],
                ["Labor", "34%"],
                ["Water & energy", "22%"],
                ["Other inputs", "16%"],
              ].map((r, i) => (
                <p key={r[0]}>
                  <i className={`c${i}`} />
                  {r[0]}
                  <b>{r[1]}</b>
                </p>
              ))}
            </div>
          </div>
        </Card>
        <Card>
          <SectionHead title="Income range" sub="Reflects yield and price uncertainty" />
          <div className="range-chart">
            <span>
              Low<b>$12.2k</b>
            </span>
            <i>
              <em />
            </i>
            <span>
              Expected<b>$15.1k</b>
            </span>
            <span>
              High<b>$18.4k</b>
            </span>
          </div>
          <div className="uncertainty">
            <Icon name="info" />
            <span>
              <b>Confidence: medium</b>Market prices contribute most to the ±18% range.
            </span>
          </div>
        </Card>
      </div>
      <Card>
        <SectionHead title="Rotation comparison" sub="Financial and resilience tradeoffs" />
        <div className="finance-table">
          <div>
            <b>Plan</b>
            <b>Revenue</b>
            <b>Costs</b>
            <b>Net margin</b>
            <b>Water risk</b>
            <b></b>
          </div>
          {[
            ["Plan A · Resilient", "$15.1k", "$6.4k", "$8.7k", "Moderate"],
            ["Plan B · Income", "$16.3k", "$7.1k", "$9.2k", "High"],
            ["Plan C · Water saver", "$13.9k", "$5.8k", "$8.1k", "Low"],
          ].map((r) => (
            <div key={r[0]}>
              {r.map((v, i) => (
                <span key={v} className={i === 4 ? v.toLowerCase() : ""}>
                  {v}
                </span>
              ))}
              <button>View</button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function SavedPlans({ setPage }: { setPage: (page: string) => void }) {
  const [tab, setTab] = useState<"current" | "archived">("current");
  const [format, setFormat] = useState("PDF report");
  const [exportState, setExportState] = useState<"idle" | "loading" | "ready">("idle");
  const generateExport = () => {
    setExportState("loading");
    window.setTimeout(() => setExportState("ready"), 950);
  };
  return (
    <div className="saved-plans">
      <div className="saved-summary">
        <div>
          <span className="section-kicker">SELECTED STRATEGY</span>
          <h2>Plan A · Resilient balance</h2>
          <p>
            Four-season rotation for Field B, tested against a hypothetical moderate drought
            scenario.
          </p>
          <div className="saved-tags">
            <span>
              <Icon name="check" size={13} /> Farm profile complete
            </span>
            <span>
              <Icon name="check" size={13} /> Climate tested
            </span>
            <span>
              <Icon name="check" size={13} /> AI explanation reviewed
            </span>
          </div>
        </div>
        <div className="plan-score">
          <span>PLAN SCORE</span>
          <strong>
            92<small>/100</small>
          </strong>
          <em>High confidence</em>
        </div>
      </div>
      <div className="saved-layout">
        <div>
          <div className="saved-tabs" role="tablist" aria-label="Saved plans">
            <button
              role="tab"
              aria-selected={tab === "current"}
              className={tab === "current" ? "active" : ""}
              onClick={() => setTab("current")}
            >
              Current plans <span>2</span>
            </button>
            <button
              role="tab"
              aria-selected={tab === "archived"}
              className={tab === "archived" ? "active" : ""}
              onClick={() => setTab("archived")}
            >
              Archived <span>0</span>
            </button>
          </div>
          {tab === "current" ? (
            <div className="saved-list">
              <Card className="saved-plan-card selected">
                <div className="saved-plan-head">
                  <span className="report-icon">
                    <Icon name="rotation" />
                  </span>
                  <div>
                    <b>Plan A · Resilient balance</b>
                    <small>Field B · Maha 2026 to Yala 2028</small>
                  </div>
                  <span className="selected-pill">SELECTED</span>
                </div>
                <div className="plan-crops">
                  {["R", "M", "M", "G"].map((crop, index) => (
                    <span key={index} className={["rice", "mung", "maize", "ground"][index]}>
                      {crop}
                    </span>
                  ))}
                </div>
                <div className="saved-plan-metrics">
                  <span>
                    Net income <b>$15.1k</b>
                  </span>
                  <span>
                    Water demand <b>3,760 m³</b>
                  </span>
                  <span>
                    Climate risk <b>Moderate</b>
                  </span>
                  <span>
                    Uncertainty <b>±12%</b>
                  </span>
                </div>
                <div className="saved-plan-actions">
                  <button onClick={() => setPage("rotation")}>Edit plan</button>
                  <button onClick={() => setPage("climate")}>View simulation</button>
                  <button>
                    <Icon name="community" size={15} /> Share for review
                  </button>
                </div>
              </Card>
              <Card className="saved-plan-card">
                <div className="saved-plan-head">
                  <span className="report-icon x1">
                    <Icon name="water" />
                  </span>
                  <div>
                    <b>Plan C · Water saver</b>
                    <small>Draft · Last edited 18 May 2026</small>
                  </div>
                  <span className="draft-pill">DRAFT</span>
                </div>
                <div className="saved-plan-metrics compact">
                  <span>
                    Net income <b>$13.9k</b>
                  </span>
                  <span>
                    Water demand <b>3,180 m³</b>
                  </span>
                  <span>
                    Climate risk <b>Low</b>
                  </span>
                </div>
                <div className="saved-plan-actions">
                  <button onClick={() => setPage("rotation")}>Continue editing</button>
                </div>
              </Card>
            </div>
          ) : (
            <Card className="empty-state" role="tabpanel">
              <span>
                <Icon name="report" size={28} />
              </span>
              <b>No archived plans yet</b>
              <p>Plans you archive will stay available here for seasonal comparison.</p>
              <Button variant="secondary" onClick={() => setTab("current")}>
                View current plans
              </Button>
            </Card>
          )}
        </div>
        <Card className="export-builder">
          <SectionHead
            title="Export selected plan"
            sub="Create an implementation-ready document for your team."
          />
          <fieldset>
            <legend>Export format</legend>
            {[
              ["PDF report", "Complete visual plan", "report"],
              ["CSV data", "Tables and scenario values", "grid"],
              ["Print summary", "Two-page field guide", "leaf"],
            ].map(([name, description, icon]) => (
              <label className={format === name ? "selected" : ""} key={name}>
                <input
                  type="radio"
                  name="export-format"
                  value={name}
                  checked={format === name}
                  onChange={() => {
                    setFormat(name);
                    setExportState("idle");
                  }}
                />
                <Icon name={icon as IconName} />
                <span>
                  <b>{name}</b>
                  <small>{description}</small>
                </span>
                <i>{format === name && <Icon name="check" size={12} />}</i>
              </label>
            ))}
          </fieldset>
          <div className="export-options">
            <label>
              <input type="checkbox" defaultChecked /> Include NASA data provenance
            </label>
            <label>
              <input type="checkbox" defaultChecked /> Include uncertainty notes
            </label>
            <label>
              <input type="checkbox" defaultChecked /> Include cost assumptions
            </label>
          </div>
          {exportState === "ready" && (
            <div className="form-alert success" role="status">
              <Icon name="check" size={18} />
              <div>
                <b>Your sample export is ready</b>
                <p>AgroSphere_Plan_A_Maha_2026.pdf · 2.4 MB</p>
              </div>
            </div>
          )}
          <button
            className="btn btn-primary export-button"
            onClick={generateExport}
            disabled={exportState === "loading"}
          >
            {exportState === "loading" ? (
              <>
                <i className="spinner" /> Generating export…
              </>
            ) : exportState === "ready" ? (
              <>
                Download {format} <Icon name="download" size={17} />
              </>
            ) : (
              <>
                Generate {format} <Icon name="download" size={17} />
              </>
            )}
          </button>
          <p className="export-note">
            <Icon name="info" size={13} /> Prototype export uses sample values and does not create a
            real file.
          </p>
        </Card>
      </div>
      <DataProvenance />
    </div>
  );
}

function Reports() {
  return (
    <div>
      <div className="report-filters">
        <button className="active">
          All reports <span>8</span>
        </button>
        <button>
          Rotation plans <span>3</span>
        </button>
        <button>
          Soil & water <span>3</span>
        </button>
        <button>
          Season reviews <span>2</span>
        </button>
      </div>
      <div className="reports-grid">
        {[
          [
            "rotation",
            "Maha 2026 Rotation Plan",
            "Updated 2 days ago",
            "Plan A · 4 seasons",
            "Ready",
          ],
          [
            "water",
            "Water Budget & Drought Scenario",
            "Updated May 20",
            "Moderate drought",
            "Ready",
          ],
          ["soil", "Field B Soil Recovery Plan", "Updated May 12", "6-month program", "In review"],
          [
            "report",
            "Yala 2025 Season Review",
            "Completed Oct 2025",
            "Actual vs planned",
            "Reviewed",
          ],
        ].map((r, i) => (
          <Card key={r[1]}>
            <div className={`report-icon x${i}`}>
              <Icon name={r[0] as IconName} />
            </div>
            <span className="report-status">{r[4]}</span>
            <h3>{r[1]}</h3>
            <p>{r[3]}</p>
            <small>
              <Icon name="clock" size={14} />
              {r[2]}
            </small>
            <div>
              <Button variant="secondary">Open report</Button>
              <button className="icon-btn">
                <Icon name="download" />
              </button>
            </div>
          </Card>
        ))}
      </div>
      <Card className="agronomist">
        <div className="avatar">AD</div>
        <div>
          <b>Agronomist review</b>
          <p>Dr. A. Dissanayake left feedback on your Soil Recovery Plan.</p>
        </div>
        <blockquote>
          “Good cover crop choice. Consider splitting the compost application before heavy
          rainfall.”
        </blockquote>
        <button>
          View feedback <Icon name="arrow" />
        </button>
      </Card>
    </div>
  );
}

function Community() {
  return (
    <div>
      <div className="community-hero">
        <div>
          <div className="section-kicker light">MATALE NORTH WATER GROUP</div>
          <h2>Shared water, coordinated fairly.</h2>
          <p>8 farms · 214 hectares · Maha 2026 allocation</p>
        </div>
        <div className="allocation">
          <span>
            <b>68%</b> allocated
          </span>
          <p>18,240 of 26,800 m³</p>
          <i>
            <em />
          </i>
        </div>
      </div>
      <div className="metric-grid">
        {[
          ["Your allocation", "2,140", "m³", "8% of shared supply", "water"],
          ["Group demand", "24,620", "m³", "2,180 m³ buffer", "community"],
          ["Fairness score", "91", "/100", "Balanced distribution", "shield"],
          ["Next release", "6", "days", "June 2 · 6:00 AM", "clock"],
        ].map(([l, v, u, n, i], x) => (
          <Card className="metric" key={l}>
            <div>
              <span>{l}</span>
              <i className={`metric-icon m${x}`}>
                <Icon name={i as IconName} />
              </i>
            </div>
            <strong>
              {v}
              <small>{u}</small>
            </strong>
            <p>{n}</p>
          </Card>
        ))}
      </div>
      <Card>
        <SectionHead
          title="Farm allocation comparison"
          sub="Illustrative shared irrigation budget"
          action={<Button variant="secondary">Propose adjustment</Button>}
        />
        <div className="farm-bars">
          {[
            ["Green Valley", "2,140", "80"],
            ["Hillview Farm", "3,280", "92"],
            ["Lakpura Growers", "2,760", "74"],
            ["Sunrise Fields", "1,840", "58"],
            ["Dambulla Co-op", "4,120", "88"],
          ].map((r) => (
            <div key={r[0]}>
              <span>{r[0]}</span>
              <i>
                <em style={{ width: `${r[2]}%` }} />
              </i>
              <b>{r[1]} m³</b>
            </div>
          ))}
        </div>
      </Card>
      <div className="two-col">
        <Card>
          <SectionHead title="Shared timeline" />
          {[
            ["Jun 02", "Canal release · Zone A", "6:00 AM – 4:00 PM"],
            ["Jun 05", "Community check-in", "Online · 7:00 PM"],
            ["Jun 12", "Canal release · Zone B", "5:00 AM – 2:00 PM"],
          ].map((r) => (
            <div className="agenda" key={r[1]}>
              <span>{r[0]}</span>
              <div>
                <b>{r[1]}</b>
                <small>{r[2]}</small>
              </div>
            </div>
          ))}
        </Card>
        <Card>
          <SectionHead title="Community insight" />
          <div className="recommend-box">
            <Icon name="spark" />
            <div>
              <b>Collective savings opportunity</b>
              <p>
                Staggering maize planting by 10 days across three farms could reduce peak canal
                demand by an estimated 12%.
              </p>
            </div>
          </div>
          <Button>
            Explore coordinated plan <Icon name="arrow" />
          </Button>
        </Card>
      </div>
    </div>
  );
}

function SettingsPage() {
  const [voice, setVoice] = useState(false),
    [offline, setOffline] = useState(true),
    [contrast, setContrast] = useState(false);
  return (
    <div className="settings-layout">
      <aside>
        <button className="active">Farm profile</button>
        <button>Preferences</button>
        <button>Accessibility</button>
        <button>Data & privacy</button>
        <button>Notifications</button>
      </aside>
      <div>
        <Card>
          <SectionHead title="Farm profile" sub="Information used to personalize sample plans" />
          <div className="settings-form">
            <label>
              Farm name
              <input defaultValue="Green Valley Farm" />
            </label>
            <label>
              Primary location
              <input defaultValue="Matale, Sri Lanka" />
            </label>
            <label>
              Farm size
              <input defaultValue="32.4 hectares" />
            </label>
            <label>
              Primary language
              <select>
                <option>English</option>
                <option>සිංහල</option>
                <option>தமிழ்</option>
              </select>
            </label>
          </div>
          <Button>Save changes</Button>
        </Card>
        <Card>
          <SectionHead
            title="Accessibility & interaction"
            sub="Choose how AgroSphere works for you"
          />
          {[
            ["Voice interaction", "Use speech for assistant and navigation", voice, setVoice],
            ["Offline notebook", "Keep recent plans available offline", offline, setOffline],
            [
              "High contrast",
              "Increase contrast across charts and controls",
              contrast,
              setContrast,
            ],
          ].map(([t, d, v, s]) => (
            <div className="setting-row" key={t as string}>
              <div>
                <b>{t as string}</b>
                <small>{d as string}</small>
              </div>
              <button
                onClick={() => (s as (v: boolean) => void)(!(v as boolean))}
                className={`toggle ${v ? "on" : ""}`}
              >
                <i />
              </button>
            </div>
          ))}
        </Card>
        <Card>
          <SectionHead title="Farmer goals & constraints" />
          <div className="tag-editor">
            {[
              "Protect water supply",
              "Stable household income",
              "Restore soil",
              "Avoid chemical herbicides",
              "Max. 2 crop changes/year",
            ].map((t) => (
              <span key={t}>
                {t}
                <button>
                  <Icon name="close" size={13} />
                </button>
              </span>
            ))}
            <button>
              <Icon name="plus" size={14} /> Add goal
            </button>
          </div>
        </Card>
        <Card className="danger-zone">
          <SectionHead title="Data transparency" />
          <p>Download or clear locally stored prototype preferences and sample plan history.</p>
          <Button variant="secondary" icon="download">
            Download my data
          </Button>
        </Card>
      </div>
    </div>
  );
}

function Page({ page, setPage }: { page: string; setPage: (p: string) => void }) {
  const pages: Record<string, React.ReactNode> = {
    setup: <FarmSetup setPage={setPage} />,
    dashboard: <Dashboard setPage={setPage} />,
    rotation: <Rotation />,
    climate: <Climate />,
    water: <Water />,
    soil: <Soil />,
    weeds: <Weeds />,
    twin: <Twin />,
    assistant: <Assistant />,
    saved: <SavedPlans setPage={setPage} />,
    calendar: <CalendarPage />,
    finance: <Finance />,
    reports: <Reports />,
    community: <Community />,
    settings: <SettingsPage />,
  };
  return pages[page];
}

export default function App() {
  const [entered, setEntered] = useState(false);
  const [page, setPage] = useState("setup");
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const saved = localStorage.getItem("agrosphere-theme");
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    localStorage.setItem("agrosphere-theme", theme);
  }, [theme]);
  const toggleTheme = () => setTheme((current) => (current === "light" ? "dark" : "light"));
  const enter = () => {
    setPage("setup");
    setEntered(true);
    window.scrollTo(0, 0);
  };
  return entered ? (
    <Shell
      page={page}
      setPage={(p) => {
        setPage(p);
        window.scrollTo(0, 0);
      }}
      goHome={() => setEntered(false)}
      theme={theme}
      toggleTheme={toggleTheme}
    />
  ) : (
    <Landing enter={enter} theme={theme} toggleTheme={toggleTheme} />
  );
}
