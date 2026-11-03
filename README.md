# Digital Field Drug Testing, Automated Colour Analysis & Tamper-Evident Evidence Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-CIELAB_CIEDE2000-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org)
[![Ed25519](https://img.shields.io/badge/Cryptography-Ed25519_Asymmetric-10B981.svg)](https://ed25519.cr.yp.to)
[![React](https://img.shields.io/badge/React-19_TypeScript-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Flutter](https://img.shields.io/badge/Flutter-Dart_Mobile-02569B.svg?logo=flutter&logoColor=white)](https://flutter.dev)

A mobile-first, forensically sound digital evidence management system designed for law enforcement field drug testing. The platform automates colorimetric chemical reaction analysis using computer vision, standardises color measurements via a calibrated reference color card and CIEDE2000 ($\Delta E_{00}$), produces presumptive classifications, and generates cryptographically signed, tamper-evident evidence dossiers.

---

## 1. Executive Summary & Purpose

Existing field drug-testing kits (e.g., Scott Reagent, Marquis Reagent) rely on subjective human visual interpretation of color changes under uncontrolled lighting conditions and inconsistent smartphone sensors.

This system resolves those limitations **without introducing new physical testing hardware**:
1. **Smartphone Camera Capture**: Utilises existing smartphone cameras paired with a standard 6-patch reference color card in the same frame.
2. **Computer Vision Calibration**: Derives a linear color transformation matrix ($M$) via least-squares regression against known CIELAB ground-truth patches, correcting for ambient illuminants and sensor color cast.
3. **Automated Presumptive Classification**: Calculates exact ISO/CIE **CIEDE2000 Delta E** distances to validated kit-specific reference profiles, classifying results into **Presumptive Positive**, **Presumptive Negative**, **Inconclusive**, or **Unable to Classify**.
4. **Cryptographic Tamper-Evidence**:
   - Immediate **SHA-256** hash calculated on raw, uncompressed camera bytes before any processing.
   - Deterministic **Canonical JSON Serialization**.
   - Asymmetric **Ed25519 Digital Signatures** binding image hash, operator, kit, batch, GPS, and timestamps.
   - **Hash-Linked Audit Chain**: Blockchain-style chain of custody where each event seals the hash of the preceding event.
5. **Full Verification & Tamper Detection**: Independent verification endpoint and interactive simulation that catches bit-level image tampering or metadata alteration.
6. **Statutory Presumptive Notice**: Mandatory legal disclaimer enforced on all user interfaces and official PDF reports.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FIELD OFFICER / OPERATOR INTERFACE                     │
├──────────────────────────────────────┬──────────────────────────────────────────┤
│ Mobile Handheld / Web Portal (React)  │ Mobile Native Application (Flutter/Dart) │
│ - Camera stream with Reticle HUD     │ - Android/iOS Camera plugin              │
│ - Live GPS Telemetry (±4.2m accuracy) │ - Offline SQLite caching                 │
│ - Local Offline Queue (IndexedDB)    │ - SHA-256 & Signature preview            │
└──────────────────────────────────────┴──────────────────────────────────────────┘
                                   │  HTTP / HTTPS REST APIs
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             FASTAPI BACKEND SERVICE                             │
├─────────────────────────┬───────────────────────────┬───────────────────────────┤
│    Computer Vision      │   Presumptive Engine      │   Cryptographic Core      │
│  - Blur Detection (Lap) │  - CIEDE2000 Formula      │  - Raw SHA-256 Hashing    │
│  - Card Patch Extraction│  - Scott / Marquis / DL   │  - Canonical JSON RFC     │
│  - Least-Squares Calib  │  - Positive / Negative    │  - Ed25519 Asymmetric Sign│
│  - CIELAB Median ROI    │  - Inconclusive Boundary  │  - Public Key Verification│
├─────────────────────────┴───────────────────────────┴───────────────────────────┤
│                        DATA & STORAGE REPOSITORY                                │
│  - SQLite (WAL Mode) / PostgreSQL Normalized Schema                             │
│  - Original Raw Evidence Storage (Immutable)                                    │
│  - Calibrated Annotated Derivative Storage                                      │
│  - Official Court-Admissible PDF Reports (ReportLab + QR Code)                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Backend Framework** | Python 3.12+ / FastAPI | High-performance asynchronous REST endpoints, automatic OpenAPI documentation, Pydantic data validation. |
| **Computer Vision** | OpenCV 4.9+, NumPy, SciPy | Native matrix regression, contour sampling, frequency-domain blur detection, color space conversions. |
| **Color Science** | CIELAB, ISO/CIE CIEDE2000 | Perceptually uniform color metrics taking lightness, chroma, and hue differences into account. |
| **Cryptography** | Ed25519, SHA-256 | High-security asymmetric signatures (RFC 8032), canonical JSON deterministic serialisation. |
| **Database** | SQLite (Default with WAL Mode) / PostgreSQL | Normalised relational tables, foreign-key enforcement, append-only immutable audit trail. |
| **Web Dashboard** | React 19, TypeScript, Vite | Forensic dark UI, responsive mobile/desktop toggle, camera reticle HUD, zero external CSS dependencies. |
| **Mobile Client** | Flutter / Dart | Native camera control, offline SQLite sync, GPS location services. |
| **Report Generation** | ReportLab, QRCode | Multi-page forensic evidence PDF with embedded QR code, tamper hashes, and dual images. |

---

## 4. Computer Vision & Color Calibration Pipeline

### Step 1: Reference Colour Card Detection & Patch Extraction
Captures a standard 6-patch forensic color checker in the frame alongside the test pouch:
- **White**: $L^*=95.0, a^*=0.0, b^*=0.0$ ($sRGB \approx [242, 242, 242]$)
- **50% Neutral Gray**: $L^*=50.0, a^*=0.0, b^*=0.0$ ($sRGB \approx [119, 119, 119]$)
- **Black**: $L^*=15.0, a^*=0.0, b^*=0.0$ ($sRGB \approx [38, 38, 38]$)
- **Cyan**: $L^*=60.0, a^*=-30.0, b^*=-30.0$ ($sRGB \approx [0, 160, 190]$)
- **Magenta**: $L^*=50.0, a^*=65.0, b^*=-25.0$ ($sRGB \approx [200, 50, 150]$)
- **Yellow**: $L^*=85.0, a^*=-5.0, b^*=85.0$ ($sRGB \approx [235, 220, 20]$)

The algorithm samples the interior of each patch using an erosion mask to eliminate boundary shadows and specular reflections.

### Step 2: Least-Squares Color Calibration
Derives a $3 \times 3$ linear transformation matrix $M$ solving:
$$\min_M \| X_{\text{measured}} M - Y_{\text{reference}} \|_F^2$$
Applies $M$ to standardise ambient illumination and sensor bias. Computes residual post-calibration error (mean $\Delta E_{00}$ across all 6 reference patches).

### Step 3: Reaction ROI Extraction & CIEDE2000 Distance
Extracts the chemical reaction zone according to the kit's validated Region of Interest, computing robust median CIELAB values. Computes exact CIEDE2000 color distances:
- $d_{\text{pos}} = \text{CIEDE2000}(Lab_{\text{measured}}, Lab_{\text{pos\_ref}})$
- $d_{\text{neg}} = \text{CIEDE2000}(Lab_{\text{measured}}, Lab_{\text{neg\_ref}})$

---

## 5. Automated Presumptive Classification States & Safeguards

The engine categorises outcomes into four discrete states:
1. **`PRESUMPTIVE POSITIVE`**: $d_{\text{pos}} \le \text{Threshold}_{\text{pos}}$ and $d_{\text{pos}} + \text{Margin} < d_{\text{neg}}$.
2. **`PRESUMPTIVE NEGATIVE`**: $d_{\text{neg}} \le \text{Threshold}_{\text{neg}}$ and $d_{\text{neg}} + \text{Margin} < d_{\text{pos}}$.
3. **`INCONCLUSIVE`**: Reaction color falls within the ambiguous boundary margin between positive and negative profiles.
4. **`UNABLE TO CLASSIFY`**: Operational error (failed blur check, insufficient lighting, glare overexposure, or unvalidated kit profile).

### Mandatory Regulatory Safeguards
- **No universal threshold**: Every kit has independently approved CIELAB reference ranges.
- **Unvalidated kit profile**: Rejects automated classification; flags for authorized manual forensic review.
- **Original image immutability**: Raw camera bytes are never overwritten, cropped, or compressed.
- **Mandatory Statutory Notice**:
  > *"Automated output is a presumptive field-test result. It is not a laboratory-confirmed identification. Confirmatory qualitative and quantitative chemical analysis by an accredited forensic laboratory (e.g., GC-MS, LC-MS) is legally required for prosecution."*

---

## 6. Cryptographic Evidence Integrity & Tamper Detection

1. **Raw Byte SHA-256 Hashing**: Computed directly on the image bytes received from the sensor before any OpenCV decoding or saving.
2. **Canonical JSON Serialization**: Deterministic ordering (`sort_keys=True`, `,:` separators, UTF-8, UTC ISO 8601 timestamps).
3. **Ed25519 Asymmetric Digital Signing**: Backed by a 256-bit private key. Signs the canonical evidence payload binding:
   `test_id`, `case_reference`, `operator_id`, `kit_id`, `batch`, `original_image_hash`, `classification_result`, `analyte`, `gps_latitude`, `gps_longitude`, `device_timestamp`, `server_timestamp`.
4. **Independent Hash & Signature Verification**:
   - Recalculates SHA-256 on the stored evidence image.
   - Reconstructs canonical JSON and validates Ed25519 signature against the active public key.
5. **Interactive Tamper Demonstration**:
   - The platform includes a **"Simulate Evidence Tampering"** demonstration trigger.
   - Inverting just 16 bytes in an evidence image causes immediate verification failure, displaying a prominent red **`TAMPER ALERT: MISMATCH: Disk hash != Sealed Record hash`** alert and logging a security audit event.

---

## 7. Role-Based Access Control (RBAC) & Default Credentials

| Role | Username | Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin` | `AdminPass123!` | Full system administration, user management, kit profile approval, audit inspection. |
| **Field Officer** | `officer1` | `OfficerPass123!` | Create tests, camera capture, view own records, offline sync. |
| **Supervisor** | `supervisor1` | `SupervisorPass123!` | Review team tests, examine inconclusive reactions, verify evidence. |
| **Auditor** | `auditor1` | `AuditorPass123!` | Cryptographic verification, tamper detection, PDF report export, audit chain verification. |

*(The web interface provides 1-Click Demo Buttons on the login screen for instant role switching without manual typing).*

---

## 8. API Endpoint Summary

| Group | Method | Endpoint | Description |
|---|---|---|---|
| **Auth** | POST | `/api/auth/login` | Authenticates operator, returns JWT token. |
| **Auth** | GET | `/api/auth/me` | Returns active user profile and permissions. |
| **Kits** | GET | `/api/kits` | Lists active test kits and validated CIELAB profiles. |
| **Kits** | POST | `/api/kits` | Creates a new test kit (Admin only). |
| **Tests** | POST | `/api/tests` | Creates a new test record with GPS & batch details. |
| **Tests** | POST | `/api/tests/{test_id}/capture` | Uploads image, executes CV calibration, classification, and Ed25519 signing. |
| **Tests** | GET | `/api/tests` | Searchable test history with server-side filtering and pagination. |
| **Tests** | GET | `/api/tests/{test_id}` | Retrieves full forensic dossier with images and signatures. |
| **Evidence** | POST | `/api/evidence/{test_id}/verify` | Independent SHA-256 and Ed25519 signature verification. |
| **Evidence** | POST | `/api/evidence/{test_id}/simulate-tampering` | Demonstrates tamper detection by modifying raw image bytes. |
| **Evidence** | GET | `/api/evidence/public-key` | Exposes Ed25519 public key hex for judicial audit. |
| **Reports** | POST | `/api/reports/{test_id}/generate` | Generates official PDF evidence report with ReportLab + QR code. |
| **Reports** | GET | `/api/reports/{test_id}/download` | Downloads generated PDF evidence report. |
| **Analytics**| GET | `/api/analytics/dashboard` | Aggregated metrics, trend timelines, and kit usage distribution. |
| **Admin** | GET | `/api/admin/audit-logs` | Queries hash-linked chain-of-custody audit logs. |
| **Admin** | GET | `/api/admin/system-health` | Disk storage, database health, and key status. |

---

## 9. Local Setup & Execution Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ (Node 20+ recommended)
- Git

### Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Seed database with approved kits, profiles, and initial test records
python -m app.services.seed_data

# 4. Run automated test suite
python -m pytest tests/test_backend.py -v

# 5. Start FastAPI backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Documentation (Swagger UI): `http://127.0.0.1:8000/api/docs`
- Redoc Interface: `http://127.0.0.1:8000/api/redoc`

### Web Dashboard Setup
```bash
# 1. Navigate to web directory
cd web

# 2. Install npm dependencies
npm install

# 3. Build production bundle (Validates TypeScript)
npm run build

# 4. Start frontend development server
npm run dev -- --host 127.0.0.1 --port 5173
```
- Access Web Application: `http://127.0.0.1:5173/`

### Mobile Application Build (Flutter)
```bash
# 1. Navigate to mobile directory
cd mobile

# 2. Fetch Flutter packages
flutter pub get

# 3. Run on connected Android / iOS device or emulator
flutter run
```

---

## 10. Docker Deployment

Deploy the complete multi-service stack using Docker Compose:
```bash
docker-compose up --build
```
- Backend Service: `http://localhost:8000`
- Web Dashboard: `http://localhost:5173`

---

## 11. Verification Checklist & Acceptance Criteria

- [x] **Functional operator authentication** (JWT + PBKDF2).
- [x] **Role-based access control** (Admin, Officer, Supervisor, Auditor).
- [x] **Functional dashboard** (KPIs, usage distribution, activity timeline).
- [x] **New test creation** (UUID idempotency, batch lot, case reference).
- [x] **Camera image capture** (HTML5 camera stream with positioning reticle HUD).
- [x] **Reference colour card detection** (Standard 6-patch color checker).
- [x] **Image quality validation** (Laplacian variance sharpness, illumination, exposure).
- [x] **Colour calibration** (Least-squares regression matrix $M$, residual Delta E).
- [x] **Reaction-region extraction** (ROI cropping, robust median CIELAB).
- [x] **Automated presumptive classification** (Scott, Marquis, Ehrlich, Duquenois-Levine).
- [x] **All 4 decision states**: Presumptive Positive, Presumptive Negative, Inconclusive, Unable to Classify.
- [x] **Classification safeguards** (Rejects unvalidated kits, mandatory disclaimers).
- [x] **GPS & timestamp recording** (Dual device and server timestamps, accuracy radius).
- [x] **SHA-256 image hashing** (Original raw bytes hashed before modification).
- [x] **Digital record signing** (Ed25519 canonical JSON signatures).
- [x] **Independent signature verification** (Public key verification terminal).
- [x] **Tamper detection** (Demonstrated byte-level corruption detection).
- [x] **Searchable test history** (Multi-field filtering, sorting, pagination).
- [x] **Record details & dual image viewer** (Original immutable vs Calibrated derivative).
- [x] **Chain-of-custody audit log** (Blockchain-style hash-linked sequence).
- [x] **PDF report generation** (ReportLab forensic report with embedded verification QR code).
- [x] **Offline record creation & sync** (Local queue with idempotency keys and retry).
- [x] **Administration panel** (Kit management, validated CIELAB ranges, user toggling).
- [x] **Mobile handheld frame simulator** (Toggleable smartphone bezel viewport).
- [x] **Complete automated test suite** (11/11 pytest test cases passing).
