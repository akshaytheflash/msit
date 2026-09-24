Build a complete, genuinely working prototype of a college laboratory asset management and maintenance reporting system for an engineering college such as Maharaja Surajmal Institute of Technology (MSIT).

The system should be designed around the actual operational problem:

College laboratories have different types of equipment and computers. When a machine, computer, projector, laboratory instrument, peripheral, or other asset develops a problem, a teacher/lab staff member should be able to scan the QR/barcode attached to that asset, immediately see its details, submit a fault/maintenance report, and automatically route that report to the appropriate technician/maintenance person while also giving administrators a copy and maintaining an auditable history.

The system must begin with QR/barcode-based asset identification and maintenance reporting. A second module should provide lightweight monitoring of college-owned Windows laboratory computers for operational/security anomalies. This monitoring must be privacy-conscious: do NOT implement keylogging, webcam capture, microphone capture, screen recording, password collection, browsing-content inspection, or student surveillance. Only collect technical telemetry required for machine health and security detection.

TECH STACK

Backend:

* Python 3.12+
* FastAPI
* SQLAlchemy
* SQLite for the prototype
* Pydantic
* Alembic or a simple controlled database initialization/migration mechanism
* Jinja2 templates OR a clean frontend served by FastAPI
* SMTP email integration through environment variables
* Optional Twilio-compatible interface for technician calls/SMS, but the prototype must work even when the provider is not configured

Frontend:

* HTML5
* CSS3
* JavaScript
* Bootstrap 5 or a similarly mature UI framework
* Use a small amount of custom CSS for institutional styling
* Use Chart.js only where charts genuinely help
* Use ZXing Browser or another reliable browser barcode/QR scanning library that supports real camera-based scanning
* Do NOT fake scanning with a text input labelled “scanner”
* The webcam scanner must actually access the user's camera and decode real QR/barcode values

Do not introduce React/Next.js unless there is a strong technical reason. Prefer a maintainable Python-first architecture for this prototype.

DATABASE

Create a SQLite database with proper relational structure.

Minimum entities:

1. User

* id
* name
* email
* phone
* role
* department
* active
* created_at

Roles:

* Admin
* Faculty
* Lab Assistant
* Technician

2. Lab

* id
* name
* building
* room_number
* department
* lab_type
* description
* active

Examples:

* OOPS Lab
* Computer Programming Lab
* Computer Networks Lab
* Physics Lab
* Chemistry Lab
* EVS Lab

Do not hardcode assumptions about exact MSIT room numbers.

3. Asset

* id
* asset_code
* barcode_value
* qr_token
* name
* category
* manufacturer
* model
* serial_number
* lab_id
* status
* purchase_date
* warranty_expiry
* assigned_department
* description
* created_at
* updated_at

Asset categories should include:

* Computer
* Monitor
* Keyboard
* Mouse
* Projector
* Network Equipment
* Laboratory Equipment
* Electrical Equipment
* Furniture
* Other

Asset status:

* Operational
* Reported Fault
* Under Diagnosis
* Under Repair
* Temporarily Unavailable
* Retired

4. MaintenanceReport

* id
* asset_id
* reported_by
* title
* description
* severity
* issue_type
* attachment_path
* status
* assigned_technician
* created_at
* updated_at
* resolved_at

Severity:

* Low
* Medium
* High
* Critical

Status:

* Open
* Acknowledged
* Assigned
* In Progress
* Awaiting Parts
* Resolved
* Closed

5. MaintenanceUpdate

* id
* report_id
* user_id
* message
* previous_status
* new_status
* created_at

6. Notification

* id
* report_id
* recipient
* channel
* subject
* status
* sent_at
* error_message

Channels:

* Email
* SMS
* Internal

7. ComputerTelemetry

* id
* asset_id
* hostname
* timestamp
* cpu_usage
* ram_usage
* disk_usage
* uptime_seconds
* user_session_present
* idle_seconds
* process_count
* network_bytes_sent
* network_bytes_received
* active_process_summary

8. SecurityEvent

* id
* asset_id
* timestamp
* event_type
* severity
* description
* evidence
* status

Examples:

* Unexpected process
* Unauthorized executable
* Excessive network usage
* Crypto-mining-like resource usage
* Remote administration tool detected
* Repeated failed login
* Abnormal process activity during unusual hours
* Agent offline

9. AuditLog

* id
* user_id
* action
* entity_type
* entity_id
* metadata
* timestamp

IMPORTANT DESIGN PRINCIPLE

Every maintenance-related action must be auditable.

Do not allow a report's history to simply disappear when its status changes. Every status transition, assignment, comment, notification, and administrative change should be recorded in AuditLog/MaintenanceUpdate.

CORE USER FLOW 1 — SCAN AN ASSET

Create a page:

/scan

The page should open the browser camera and provide a real-time scanning interface.

Support:

* QR codes
* common 1D barcodes such as Code 128/EAN where practical
* camera selection if multiple cameras are available
* flashlight support where browser/device supports it
* manual asset-code fallback

When a code is scanned:

1. Decode the identifier.
2. Query the backend.
3. Open the asset details page.
4. Display:

   * asset name
   * asset code
   * category
   * lab
   * room
   * model
   * serial number
   * current status
   * warranty status
   * recent maintenance incidents
5. Show prominent action:
   “Report an Issue”

CORE USER FLOW 2 — REPORT A FAULT

From the asset page:

“Report an Issue”

Form:

* Issue title
* Issue description
* Severity
* Issue type
* Optional image attachment
* Reporter identity
* Optional contact number

Examples:

* “System does not boot”
* “Monitor displaying horizontal lines”
* “Keyboard keys not working”
* “Projector lamp not functioning”
* “Oscilloscope channel not responding”

Upon submission:

1. Create MaintenanceReport.
2. Automatically change asset status to “Reported Fault”.
3. Identify the appropriate technician based on configured lab/category rules.
4. Send an email containing:

   * asset name
   * asset code
   * lab
   * room
   * reporter
   * issue
   * severity
   * report ID
   * timestamp
5. Send a separate administrative notification/copy.
6. Display confirmation with report ID.
7. Add an audit event.

EMAIL TEMPLATE

Create a proper professional HTML email, not plain ugly debug text.

Subject example:

[LAB MAINTENANCE] High Priority Issue — Computer LAB-COMP-023

Body should contain:

Asset
Location
Reported By
Severity
Issue
Report ID
Timestamp

and a button/link:

“Open Maintenance Report”

The report URL should work inside the local prototype.

TECHNICIAN WORKFLOW

Technicians get a dashboard showing:

* New reports
* High priority reports
* Assigned reports
* Reports awaiting parts
* Resolved reports
* Overdue reports

A technician can:

* acknowledge a report
* accept assignment
* change status
* add diagnostic notes
* upload an image
* mark parts required
* resolve the issue
* add resolution notes

When resolved:

* record resolved_at
* update the asset status
* preserve the complete maintenance history

ADMIN DASHBOARD

Create a professional institutional dashboard.

Display:

* Total assets
* Operational assets
* Faulted assets
* Assets under repair
* Open maintenance reports
* Critical reports
* Technician workload
* Reports by lab
* Reports by category
* Average resolution time
* Most frequently faulting assets

Charts should be restrained and useful.

Avoid the typical AI-generated dashboard full of:

* giant glowing cards
* gradients everywhere
* excessive rounded rectangles
* unnecessary animations
* meaningless statistics
* fake “AI” labels

INSTITUTIONAL UI DIRECTION

Take visual inspiration from real Indian engineering-college/institution websites, especially the structure of MSIT's current website.

The MSIT site uses an institutional information architecture with:

* college identity/header
* primary navigation
* department sections
* student sections
* committees
* notices
* news
* administrative/contact information

Use that general information architecture, not a literal copy of their website.

Visual direction:

* white/light neutral background
* restrained institutional blue/navy/maroon accent palette
* serious academic/administrative appearance
* clear typography
* strong table hierarchy
* compact navigation
* minimal animation
* proper breadcrumbs
* clear page titles
* dense but readable administrative tables
* status badges using subtle colors
* consistent spacing
* no glassmorphism
* no cyberpunk/neon appearance
* no “startup SaaS” visual language

The application should look like something a college administration could realistically deploy.

MAIN NAVIGATION

Dashboard
Assets
Labs
Scan Asset
Maintenance
Technicians
Computer Monitoring
Security Events
Reports
Audit Logs
Administration

ROLE-BASED ACCESS

Admin:

* everything

Faculty:

* scan assets
* view assets
* report faults
* view their submitted reports

Lab Assistant:

* scan assets
* report faults
* view lab assets
* update basic operational status

Technician:

* view assigned reports
* update repair status
* add notes
* resolve incidents

COMPUTER ASSET SUPPORT

Computers should be first-class assets.

Example asset:
Asset code: COMP-105-014
Type: Computer
Lab: OOPS Lab
Room: 105
Hostname: OOPS-PC-014

Every computer should optionally have an installed lightweight monitoring agent.

Create a separate Python Windows agent in:

/agent

The agent should periodically send:

* hostname
* asset code
* CPU utilization
* RAM utilization
* disk utilization
* uptime
* idle time
* currently logged-in session presence
* process count
* network transfer statistics
* a limited allowlisted/denylisted process-name summary

Use a configurable heartbeat interval such as 30–60 seconds.

The agent must authenticate to the server using a per-machine token.

Do NOT collect:

* keystrokes
* passwords
* clipboard contents
* webcam images
* microphone audio
* screenshots
* browser history
* document contents
* personal files

SUSPICIOUS ACTIVITY / SECURITY MODULE

Implement a simple rule-based anomaly detection engine first. Do not pretend that a basic rules engine is machine learning.

Examples of rules:

1. Known unauthorized process
   Flag configured applications such as:

* unauthorized remote administration tools
* cryptocurrency miners
* known prohibited utilities

2. Abnormally high CPU usage
   If CPU remains above configurable threshold for a sustained period, generate an event.

3. Abnormal network usage
   Detect unexpectedly high network transfer compared with the configured baseline.

4. Repeated failed login events
   Create a security event after configurable repeated failures.

5. Machine active outside normal lab hours
   Use configurable college/lab operating hours.

6. Monitoring agent stopped communicating
   If a machine misses multiple heartbeats, mark it:
   “Agent Offline”

7. Unexpected software
   Maintain a configurable approved software inventory and flag executables outside policy.

Important:
Do not automatically accuse a student of wrongdoing.

The interface should say:
“Potential Security Event”
rather than:
“Student is doing suspicious activity.”

Security events should require staff/admin review.

Show:

* machine
* timestamp
* rule triggered
* evidence
* severity
* review status

Provide:

* Open
* Under Review
* False Positive
* Confirmed
* Resolved

LOW-USAGE MACHINE VIEW

Create a section showing computers with unusually low utilization.

Example metrics:

* average CPU utilization
* average active time
* average idle time
* number of sessions
* last heartbeat
* last detected process activity

Purpose:
Help administrators identify:

* machines that may be unused
* machines that may be offline
* broken machines
* abnormal utilization
* potential security issues

Do not infer wrongdoing solely from low usage.

ASSET QR GENERATION

For every asset create:

* QR code
* human-readable asset code

Provide:
“Print Asset Label”

The printable label should contain:

* Institution name
* Lab
* Asset name
* Asset code
* QR code
* short instruction:
  “Scan to report an issue”

Create a print-friendly page with no web-navigation UI.

SEARCH/FILTERING

Assets:

* search by asset code
* serial number
* hostname
* name
* lab
* category
* status

Maintenance:

* report ID
* severity
* lab
* technician
* status
* date range

Security events:

* asset
* severity
* event type
* review status
* date range

API

Create documented FastAPI endpoints.

Minimum:
GET /api/assets
GET /api/assets/{id}
GET /api/assets/code/{code}
POST /api/assets
PUT /api/assets/{id}
GET /api/labs
POST /api/maintenance
GET /api/maintenance
GET /api/maintenance/{id}
PATCH /api/maintenance/{id}/status
POST /api/maintenance/{id}/updates
GET /api/security-events
PATCH /api/security-events/{id}
POST /api/telemetry
POST /api/heartbeat

Use proper HTTP status codes and validation.

AUTHENTICATION

Implement real authentication for the prototype.

Use:

* session-based authentication or JWT
* hashed passwords
* role-based authorization
* protected admin/technician routes

Seed demo accounts through a setup script rather than hardcoding passwords into application code.

CONFIGURATION

Use a .env file for:

* SECRET_KEY
* DATABASE_URL
* SMTP_HOST
* SMTP_PORT
* SMTP_USER
* SMTP_PASSWORD
* SMTP_FROM
* TECHNICIAN_EMAIL
* ADMIN_EMAIL
* TELEMETRY_API_KEY
* optional SMS configuration

Do not commit secrets.

PROJECT STRUCTURE

Use a clean structure such as:

app/
main.py
config.py
database.py
models/
schemas/
routers/
services/
templates/
static/
auth/
notifications/
monitoring/
security/

agent/
agent.py
config.py

scripts/
seed.py
create_admin.py
generate_asset_labels.py

tests/
test_assets.py
test_maintenance.py
test_auth.py
test_notifications.py
test_security_events.py
test_telemetry.py

requirements.txt
.env.example
README.md
run.py

QUALITY REQUIREMENTS

This is a real prototype, not a mockup.

Do NOT:

* fake API responses
* hardcode dashboard numbers
* use static JSON pretending to be a database
* use placeholder buttons that don't work
* make a fake barcode scanner
* create fake “AI detection”
* leave core buttons non-functional

All major flows must work end to end.

Example complete test:

1. Open application.
2. Login as faculty.
3. Go to Scan Asset.
4. Camera starts.
5. Scan a generated QR code for COMP-105-014.
6. Asset details appear.
7. Faculty submits:
   “System shuts down randomly.”
8. Maintenance report is created.
9. Asset becomes “Reported Fault”.
10. Technician receives notification.
11. Admin receives notification/copy.
12. Technician logs in.
13. Technician accepts report.
14. Technician changes status to In Progress.
15. Technician adds diagnostic note.
16. Technician resolves report.
17. Asset returns to Operational.
18. Maintenance history contains every event.
19. Dashboard statistics update automatically.

SEED DATA

Populate the prototype with realistic demo data:

* 5–10 laboratories
* 30–50 assets
* 15–25 computers
* several faculty members
* technicians
* maintenance reports
* resolved historical incidents
* telemetry samples
* several example security events

Do not invent specific real MSIT room numbers unless they are explicitly provided in configuration/data.

TESTING

Write automated tests for:

* asset creation
* asset lookup
* barcode/QR identifier lookup
* report creation
* automatic status update
* role permissions
* technician assignment
* audit logging
* notification generation
* telemetry ingestion
* security rule triggering

Also provide a manual acceptance-testing checklist.

README

The README must contain:

1. Project overview
2. Architecture
3. Installation
4. Virtual environment setup
5. SQLite database initialization
6. Seed data
7. Running backend
8. Opening frontend
9. Camera permissions for barcode scanning
10. SMTP configuration
11. Running the Windows monitoring agent
12. Registering a machine
13. Example API calls
14. Running tests
15. Security/privacy considerations
16. Prototype limitations
17. Future deployment architecture

DOCKER

Provide an optional Dockerfile/docker-compose setup for the backend, but the application must also run directly with Python on Windows/Linux.

FINAL DELIVERABLE

The finished repository must be immediately runnable.

Running something equivalent to:

python -m venv .venv
pip install -r requirements.txt
python scripts/seed.py
uvicorn app.main:app --reload

should start the working application.

The final UI should feel like a real college administrative/laboratory management portal that could be shown to a professor.

Most importantly, prioritize:

1. real barcode/QR camera scanning
2. real SQLite persistence
3. real maintenance workflow
4. real email notification
5. real role-based access
6. real audit history
7. working computer telemetry prototype
8. explainable security rules
9. professional institutional UI

Build the complete prototype, not just the frontend.
