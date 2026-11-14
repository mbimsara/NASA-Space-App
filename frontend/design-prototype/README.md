# AgroSphere design prototype

This is Tharuka's Figma Make handoff, imported from
`Build AgroSphere AI MVP.zip` as a clean local-only React/Vite prototype.
Generated `.next` output and platform caches were intentionally excluded.

## Purpose

Use this application to review the intended visual journey, layout, labels, and
responsive design. It uses illustrative sample values and local UI state. It is
not connected to the AgroSphere APIs, NASA providers, the rotation engine, or
the reviewed financial calculator.

Shehani's `frontend/src` remains the production frontend implementation. Move
approved visual patterns from this prototype into that application rather than
adding backend integration here.

## Setup and checks

Requires Node.js 22. The retained lockfile uses pnpm 10.20.0.

```powershell
npx.cmd --yes pnpm@10.20.0 install --frozen-lockfile
.\node_modules\.bin\tsc.cmd --noEmit
.\node_modules\.bin\oxfmt.cmd --check src index.html vite.config.ts
.\node_modules\.bin\vite.cmd build
```

Run locally when an interactive visual review is needed:

```powershell
.\node_modules\.bin\vite.cmd --host 127.0.0.1
```

## Integration rules

- Preserve labels that identify sample, synthetic, modeled, and hypothetical
  information.
- Do not copy hard-coded crop scores, financial values, or NASA values into the
  connected frontend.
- Use shared API types and fixtures when wiring production screens.
- Render unknown measurements as unknown, never zero.
- Use the reviewed crop-water ranges and show their basis, model version,
  assumptions, and limitations.
- Keep assistant explanations tied to the selected farm and analysis IDs.
