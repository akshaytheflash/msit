# Institute Laboratory Services

A runnable FastAPI prototype for college laboratory inventory, QR/barcode identification, maintenance reports, technician workflow, staff review, and privacy-conscious Windows computer health telemetry.

## Architecture

FastAPI serves HTML pages and documented JSON endpoints; SQLAlchemy persists the relational data in SQLite; Jinja templates and Bootstrap provide the interface. Browser scanning uses ZXing's browser library for live camera decoding of QR and common 1D barcode formats. QR labels resolve to opaque asset tokens. SMTP is optional and reports are recorded in the notification table whether email is configured or not. The separate Windows agent reports technical health metrics using a per-agent bearer token. Security indicators are explicit rules and remain reviewable by staff.

## Install and run

Requires Python 3.12 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/seed.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API documentation is at `/docs`. SQLite tables are initialized on application start; the database file defaults to `lab_assets.db`.

## Deploy to Render

The root-level `render.yaml` is a Render Blueprint. Push this repository to a Git provider, then in Render choose **New → Blueprint** and select the repository. The Blueprint creates a Python web service with a persistent disk for SQLite and issue attachments. Persistent disks require a paid Render web-service plan and limit the service to one instance; do not scale this SQLite deployment horizontally. See [Render Blueprint docs](https://render.com/docs/blueprint-spec) and [persistent disk docs](https://render.com/docs/disks).

During the initial Blueprint setup, provide `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` (12 or more characters), and `INITIAL_ADMIN_NAME`. The first-deploy hook creates that administrator only when the database has no users. Configure SMTP as Render environment variables if email delivery is needed. After deployment, use the service's `onrender.com` URL. Do not run `scripts/seed.py` on a public deployment because it installs publicly documented demo credentials. The Render disk keeps SQLite data and uploads across deploys; deleting or replacing the disk removes that data.

Seed creates 8 labs, 40 assets (20 computers), demo work orders, telemetry, and events. Every demo account has password `ChangeMe123!`; accounts are `admin@college.example`, `aditi.sharma@college.example`, `rohan.mehta@college.example`, `sanjay.kumar@college.example`, `priya.nair@college.example`, and `neha.verma@college.example`. Change demo passwords before use beyond a local demonstration. For a private administrator account, run `python scripts/create_admin.py`.

## Using the prototype

Sign in as faculty or lab assistant, open **Scan Asset**, and allow camera permission. Browsers require HTTPS or localhost for camera access. Use the camera drop-down to select a device; QR and practical 1D formats are decoded in the browser. The manual fallback accepts asset codes. An asset page shows details and recent work orders; submit an issue there. A technician can acknowledge, add notes, change status, or resolve it. Admin can assign a technician. Status changes and notes are retained in maintenance updates and the audit log. When an issue is resolved, the asset returns to Operational.

Print labels from an asset record. Labels include institution heading, lab, asset code, QR image, and instruction text. SMTP is optional. Configure SMTP variables in `.env` for email delivery; without SMTP configured, report and notification records remain stored and show the email state as not configured.

## SMTP configuration

Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `TECHNICIAN_EMAIL`, and `ADMIN_EMAIL` in `.env`. Email uses STARTTLS. The prototype sends separate copies to the assigned technician, configured technician address, and admin address when addresses are present.

## Windows monitoring agent

Register a computer as an asset, then set a unique machine token via your deployment's secret provisioning process. Configure `.env` with a strong `TELEMETRY_API_KEY` (prototype accepts a shared bearer key), and on the Windows machine set:

```powershell
$env:LAB_SERVER_URL='http://server-host:8000'
$env:LAB_ASSET_CODE='COMP-105-001'
$env:LAB_AGENT_TOKEN='same-value-as-TELEMETRY_API_KEY'
$env:LAB_HEARTBEAT_SECONDS='45'
pip install psutil requests
python agent/agent.py
```

Metrics are CPU/RAM/disk use, uptime, session presence, process count, aggregate network bytes, and a bounded list of process names. No keylogging, passwords, clipboard, webcam, microphone, screenshots, browser history/content, files, or command lines are collected. The current prototype accepts a shared token; use per-machine credentials, TLS, token rotation, and an offline-heartbeat scheduler for deployment. High CPU and configured process-name matches create potential events requiring staff review.

## API examples

Authenticated browser session is required for user APIs; telemetry uses bearer authentication.

```bash
curl -b cookies.txt http://127.0.0.1:8000/api/assets?q=COMP
curl -b cookies.txt http://127.0.0.1:8000/api/assets/code/COMP-105-001
curl -b cookies.txt -H 'Content-Type: application/json' -d '{"asset_id":1,"title":"No power","description":"Does not start","severity":"High"}' http://127.0.0.1:8000/api/maintenance
curl -H 'Authorization: Bearer change-this-agent-token' -H 'Content-Type: application/json' -d '{"asset_code":"COMP-105-001","cpu_usage":12,"ram_usage":48,"disk_usage":60,"hostname":"LAB-PC-01"}' http://127.0.0.1:8000/api/telemetry
```

Key endpoints: `GET /api/assets`, `GET /api/assets/{id}`, `GET /api/assets/code/{code}`, `POST /api/assets`, `PUT /api/assets/{id}`, `GET /api/labs`, `POST /api/maintenance`, `GET /api/maintenance`, `GET /api/maintenance/{id}`, `PATCH /api/maintenance/{id}/status`, `POST /api/maintenance/{id}/updates`, `GET /api/security-events`, `PATCH /api/security-events/{id}`, `POST /api/telemetry`, `POST /api/heartbeat`.

## Manual acceptance checklist

- Sign in as faculty; scan a printed QR using a camera on localhost/HTTPS and open matching asset.
- Submit issue and confirm report ID, asset fault status, maintenance history, audit row, and notification row.
- Sign in as technician; assign/accept work, add a note, change status, resolve; verify asset returns to Operational and history remains.
- Sign in as admin; inspect dashboard, assign a technician, review audit logs, and update a security event status.
- Run agent against a registered computer and confirm telemetry appears in Computer Monitoring.
- Confirm camera permission works and manual code lookup remains available.

## Prototype limitations and deployment direction

No student surveillance is implemented. The prototype does not claim machine learning; its rules are illustrative thresholds and process-name matches. There is no scheduled stale-heartbeat detector yet, no automated database migration framework, and no per-machine token registry or user self-service password reset. Production should add TLS termination, secure cookie settings, CSRF protection, strong provisioned credentials, per-machine token rotation, rate limiting, upload scanning, database migrations/backups, notification retries, retention controls, offline-agent scheduling, and institution-specific assignment rules. Replace seeded demo data and credentials before deployment. Camera library and Bootstrap are loaded from public CDNs.
