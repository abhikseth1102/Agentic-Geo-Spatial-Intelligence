# Local verification record

Verified on 26 October 2026 in the local Windows workspace.

| Check | Result |
|---|---|
| Source extraction | 9,306,345 raw messages scanned; 37,843 final observations; 217 vessels |
| Benchmark | Five approaches; 151 training and 51 test vessels; zero identity overlap |
| Backend tests | 17 passed; one upstream Starlette/httpx deprecation warning |
| Frontend production build | Passed; application and vendor chunks separated |
| Frontend lint | Passed without warnings |
| npm dependency audit | Zero reported vulnerabilities |
| Production browser workflow | Passed against localhost:8080; zero page errors |
| Browser interactions | Type filter, empty search, CSV download, modal keyboard dismissal, trajectory inspection, scenario evaluate/save/delete, all five views |
| Mobile | 390 × 844 viewport, no document-level horizontal overflow |
| External-network independence | HTTPS requests blocked; local app and bundled coastline still rendered |
| EDA notebook | Seven code cells executed in order; real outputs and figure embedded |
| Report | 18 pages rendered and visually inspected; 25 unique DOI references |
| Handbook | Two pages rendered and visually inspected |

The browser script is `scripts/browser_check.cjs`. It uses the frontend's Playwright dependency and installed Edge on Windows. On other platforms install Playwright Chromium before running. Set `APP_URL` to choose the server; the default is the Vite development server at port 5173.

This record covers the exercised local workflows. GitHub Actions and Docker configuration were prepared but were not executed remotely or in Docker during this session. No repository was pushed and no public deployment was performed.
