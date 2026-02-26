# GOTHAM - Technical Documentation

> **G**estational **O**utcome **T**racking with **H**ealth **A**nalytics for **M**others  
> AI-powered maternal health monitoring system

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Frontend Components](#frontend-components)
5. [Theme & Design System](#theme--design-system)
6. [Data Models](#data-models)
7. [Deployment](#deployment)
8. [Development Workflow](#development-workflow)

---

## System Architecture

### Tech Stack

#### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Neon.tech hosted)
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **AI Processing**: Inngest (background job processing)
- **AI Model**: Groq API (Llama models)

#### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Charts**: Recharts

### System Flow

```
┌─────────────┐      HTTP/REST      ┌──────────────┐
│   Frontend  │ ◄─────────────────► │   Backend    │
│   (React)   │                     │  (FastAPI)   │
└─────────────┘                     └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │  PostgreSQL  │
                                    │   Database   │
                                    └──────────────┘
                                           ▲
                                           │
                                    ┌──────┴───────┐
                                    │   Inngest    │
                                    │ (Background) │
                                    └──────────────┘
```

---

## Database Schema

### Core Tables

#### `patients`
Primary patient information with static/semi-static features.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `patient_identifier` | VARCHAR | Unique patient ID (e.g., P001) |
| `name` | VARCHAR | Patient full name |
| `age` | INTEGER | Current age |
| `contact_number` | VARCHAR | Phone number |
| `clinical_notes` | TEXT | General clinical notes |
| `risk_level` | VARCHAR | Overall risk (low/medium/high) |
| `number_of_pregnancies` | INTEGER | Gravida count |
| `bmi_category` | INTEGER | BMI classification (0-4) |
| `family_history` | BOOLEAN | Family history of diabetes |
| `pcos` | BOOLEAN | PCOS diagnosis |
| `unexplained_prenatal_loss` | BOOLEAN | History of pregnancy loss |
| `large_child_or_birth_default` | BOOLEAN | Previous large baby |
| `prediabetes` | BOOLEAN | Pre-existing prediabetes |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

#### `visits`
Individual patient visits/checkups.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `patient_id` | INTEGER | Foreign key to patients |
| `visit_date` | TIMESTAMP | Date/time of visit |
| `visit_type` | VARCHAR | Type of visit |
| `notes` | TEXT | Visit-specific notes |
| `created_at` | TIMESTAMP | Record creation time |

#### `anemia_assessments`
Complete Blood Count (CBC) results and anemia diagnosis.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `visit_id` | INTEGER | Foreign key to visits |
| `wbc` | FLOAT | White Blood Cells (10³/μL) |
| `rbc` | FLOAT | Red Blood Cells (10⁶/μL) |
| `hgb` | FLOAT | Hemoglobin (g/dL) |
| `hct` | FLOAT | Hematocrit (%) |
| `mcv` | FLOAT | Mean Corpuscular Volume (fL) |
| `mch` | FLOAT | Mean Corpuscular Hemoglobin (pg) |
| `mchc` | FLOAT | MCHC (g/dL) |
| `plt` | FLOAT | Platelet count (10³/μL) |
| `diagnosis` | VARCHAR | AI anemia diagnosis |
| `confidence` | FLOAT | AI confidence (0-1) |
| `ai_report` | TEXT | AI analysis report |
| `created_at` | TIMESTAMP | Assessment time |

#### `fetal_health_assessments`
Cardiotocography (CTG) results and fetal health predictions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `visit_id` | INTEGER | Foreign key to visits |
| `baseline_value` | FLOAT | Fetal heart rate baseline (bpm) |
| `accelerations` | FLOAT | FHR accelerations |
| `fetal_movement` | FLOAT | Fetal movement count |
| `uterine_contractions` | FLOAT | Contraction frequency |
| `light_decelerations` | FLOAT | Light decelerations |
| `severe_decelerations` | FLOAT | Severe decelerations |
| `prolongued_decelerations` | FLOAT | Prolonged decelerations |
| `abnormal_short_term_variability` | FLOAT | Abnormal STV |
| `mean_value_of_short_term_variability` | FLOAT | Mean STV |
| `percentage_of_time_with_abnormal_long_term_variability` | FLOAT | Abnormal LTV% |
| `mean_value_of_long_term_variability` | FLOAT | Mean LTV |
| `histogram_*` | FLOAT | Various histogram metrics |
| `status` | INTEGER | Fetal status (1=Normal, 2=Suspect, 3=Pathological) |
| `confidence` | FLOAT | AI confidence (0-1) |
| `ai_report` | TEXT | AI analysis report |
| `created_at` | TIMESTAMP | Assessment time |

#### `gdm_assessments`
Gestational Diabetes Mellitus screening and diagnosis.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `visit_id` | INTEGER | Foreign key to visits |
| `glucose_level` | FLOAT | Blood glucose (mg/dL) |
| `blood_pressure_systolic` | INTEGER | Systolic BP (mmHg) |
| `blood_pressure_diastolic` | INTEGER | Diastolic BP (mmHg) |
| `bmi` | FLOAT | Body Mass Index |
| `ogtt` | FLOAT | Oral Glucose Tolerance Test result |
| `gestation_weeks` | INTEGER | Gestational age (weeks) |
| `risk_level` | INTEGER | GDM risk (0=Normal, 1=Elevated, 2=High) |
| `confidence` | FLOAT | AI confidence (0-1) |
| `ai_report` | TEXT | AI analysis report |
| `created_at` | TIMESTAMP | Assessment time |

### Relationships

```
patients (1) ──< (N) visits
visits (1) ──< (0-1) anemia_assessments
visits (1) ──< (0-1) fetal_health_assessments
visits (1) ──< (0-1) gdm_assessments
```

---

## API Endpoints

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: TBD

### Patients API

#### `GET /api/patients/`
Get all patients with merged profile data.

**Response**: Array of Patient objects
```json
[
  {
    "id": 1,
    "patient_identifier": "P001",
    "name": "Ayesha Khan",
    "age": 28,
    "contact_number": "+92-300-1234567",
    "risk_level": "medium",
    ...
  }
]
```

#### `GET /api/patients/{patient_identifier}`
Get single patient by identifier.

**Parameters**:
- `patient_identifier`: String (e.g., "P001")

#### `POST /api/patients/`
Create new patient.

**Request Body**:
```json
{
  "patient_identifier": "P005",
  "family_history": false,
  "pcos": false,
  ...
}
```

#### `PUT /api/patients/{patient_identifier}`
Update patient information.

### Dashboard API

#### `GET /api/dashboard/stats`
Get dashboard statistics.

**Response**:
```json
{
  "total_patients": 4,
  "high_risk_count": 2,
  "medium_risk_count": 1,
  "low_risk_count": 1,
  "total_assessments": 21,
  "recent_patients": [...]
}
```

#### `GET /api/dashboard/risk-distribution`
Get patient risk distribution for charts.

**Response**:
```json
{
  "high": 2,
  "medium": 1,
  "low": 1
}
```

#### `GET /api/dashboard/patient/{patient_identifier}/visits`
Get all visits with complete assessment data for a patient.

**Response**:
```json
[
  {
    "id": 1,
    "visit_date": "2025-08-17T22:54:13",
    "notes": "...",
    "wbc": 7.2,
    "rbc": 3.97,
    "hgb": 9.0,
    ...
    "baseline_value": 132.0,
    "fetal_health_status": 1,
    ...
    "glucose_level": 145.0,
    "gdm_risk_level": 1
  }
]
```

---

## Frontend Components

### Page Components

#### `Index.tsx`
Main dashboard page.
- Real-time statistics from `/api/dashboard/stats`
- Risk overview chart
- Recent patients list
- High-risk alerts

#### `PatientsPage.tsx`
Patient list with search and filtering.
- Fetches from `/api/patients/`
- Real-time patient count
- Add new patient modal
- Search by name or ID

#### `PatientProfilePage.tsx`
Detailed patient view with tabs:
- **Overview**: Health metrics and stats
- **Vitals**: Vitals tracking (VitalsChart)
- **Assessments**: Clinical history
- **Visit History**: VisitTimeline component

### Key Components

#### `PatientCard.tsx`
Patient card with theme-consistent styling.

**Props**:
```typescript
{
  id: string;
  name: string;
  age: string;
  contactNumber: string;
  riskLevel: 'high' | 'medium' | 'low';
}
```

**Features**:
- Color-coded risk badges
- Medical-pink/blue theming
- Hover effects
- Click to navigate to profile

#### `VisitTimeline.tsx`
Complete visit history with all assessments.

**Features**:
- Three assessment type sections:
  - CBC/Anemia (Medical-Pink)
  - CTG/Fetal Health (Medical-Blue)
  - GDM Screening (Cyan/Teal)
- Collapsible cards
- Preview metrics when collapsed
- Color-coded status badges
- Clinical notes display

**Data Flow**:
```typescript
interface Visit {
  id: number;
  visit_date: string;
  notes: string;
  
  // CBC (8 parameters)
  wbc, rbc, hgb, hct, mcv, mch, mchc, plt: number | null;
  
  // FHP (CTG)
  baseline_value, accelerations: number | null;
  fetal_health_status: number | null;
  fetal_health_confidence: number | null;
  
  // GDM
  glucose_level, blood_pressure_systolic, 
  blood_pressure_diastolic, bmi, ogtt: number | null;
  gdm_risk_level: number | null;
  gdm_confidence: number | null;
  
  // Diagnoses
  anemia_diagnosis: string | null;
  anemia_confidence: number | null;
}
```

#### `RiskOverviewChart.tsx`
Donut chart showing risk distribution.
- Fetches from `/api/dashboard/risk-distribution`
- Medical-pink (high), Purple (medium), Medical-blue (low)
- Animated transitions

---

## Theme & Design System

### Color Palette

| Usage | Color Name | Hex | CSS Variable |
|-------|------------|-----|--------------|
| High Risk / Blood | Medical-Pink | `#EC4899` | `medical-pink` |
| Low Risk / Fetal | Medical-Blue | `#3B82F6` | `medical-blue` |
| GDM / Glucose | Cyan/Teal | `#06B6D4` | N/A |
| Medium Risk | Purple | `#A855F7` | N/A |
| Suspect Status | Purple | `#9333EA` | N/A |

### Typography
- **Font Family**: Inter (Google Fonts)
- **Headings**: Bold, gradient text effects
- **Body**: Regular, 14-16px
- **Small**: 12px for labels

### Components Styling

#### Cards
```css
bg-card/60 backdrop-blur-sm
rounded-2xl shadow-xl
border border-border/30
```

#### Buttons (Primary)
```css
bg-gradient-to-r from-medical-pink to-medical-blue
text-white font-semibold
rounded-lg shadow-lg
hover:shadow-xl hover:scale-105
```

#### Badges
```css
/* High Risk */
bg-gradient-to-r from-medical-pink to-rose-500

/* Medium Risk */
bg-gradient-to-r from-purple-400 to-pink-400

/* Low Risk */
bg-gradient-to-r from-medical-blue to-cyan-400
```

---

## Data Models

### Patient Risk Levels

| Level | Criteria | Color |
|-------|----------|-------|
| **High** | Multiple risk factors, pathological CTG, severe anemia | Medical-Pink |
| **Medium** | Some risk factors, elevated GDM, mild anemia | Purple |
| **Low** | Normal parameters, no risk factors | Medical-Blue |

### GDM Risk Classification

| Level | Value | Criteria |
|-------|-------|----------|
| Normal | 0 | Glucose < 140 mg/dL |
| Elevated | 1 | Glucose 140-180 mg/dL |
| High Risk | 2 | Glucose > 180 mg/dL |

### Fetal Health Status

| Status | Value | Criteria |
|--------|-------|----------|
| Normal | 1 | Healthy FHR patterns |
| Suspect | 2 | Some concerning patterns |
| Pathological | 3 | Critical distress patterns |

### BMI Categories

| Category | Value | Range |
|----------|-------|-------|
| Underweight | 0 | < 18.5 |
| Normal | 1 | 18.5-24.9 |
| Overweight | 2 | 25-29.9 |
| Obese | 3 | 30-34.9 |
| Severely Obese | 4 | ≥ 35 |

---

## Deployment

### Environment Variables

#### Backend (`.env`)
```bash
DATABASE_URL=postgresql://user:pass@host/db
GROQ_API_KEY=gsk_...
INNGEST_APP_ID=gotham-maternal-health
INNGEST_SIGNING_KEY=signkey-...
INNGEST_EVENT_KEY=...
DEBUG=True  # Set to False in production
```

#### Frontend (`.env`)
```bash
VITE_API_URL=http://localhost:8000  # Production URL
```

### Database Setup

1. **Initialize Tables**:
```bash
python scripts/init_db.py
```

2. **Seed Demo Data**:
```bash
python scripts/seed_refactored_schema.py
```

3. **Verify**:
```bash
python scripts/verify_db.py
```

### Running Services

#### Backend
```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Start Inngest dev server (Terminal 1)
npx inngest-cli@latest dev

# Start FastAPI (Terminal 2)
INNGEST_DEV=1 uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm run dev
```

**Ports**:
- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- Inngest: `http://localhost:8288`

---

## Development Workflow

### Adding New Patients

1. **Frontend**: Use "Add New Patient" button
2. **API Call**: POST to `/api/patients/`
3. **Data**: Creates Patient record with identifier

### Adding Visit Data

1. **Create Visit**: POST to visits table
2. **Add Assessments**: POST to assessment tables (anemia, fetal, gdm)
3. **Link**: All link via `visit_id` foreign key

### Updating Seed Data

File: `backend/scripts/seed_refactored_schema.py`

```python
# Add new patient function
def create_patient_5(session: Session, base_date: datetime):
    patient = Patient(
        patient_identifier="P005",
        name="New Patient",
        age=30,
        contact_number="+92-XXX-XXXXXXX",
        ...
    )
```

### Database Migrations

For schema changes, use SQLAlchemy migrations or create migration scripts in `scripts/` directory.

---

## Performance Considerations

### Database
- Indexes on `patient_identifier`, `visit_date`
- Foreign key constraints enforce data integrity
- Neon.tech provides auto-scaling

### Frontend
- React.lazy() for code splitting
- Vite for fast HMR
- Component memoization where needed

### API
- FastAPI async endpoints
- Connection pooling (SQLAlchemy)
- Background jobs via Inngest

---

## Security

### Authentication
- Currently: Development mode (no auth)
- TODO: Implement JWT-based authentication

### Data Protection
- HTTPS in production
- Database credentials in environment variables
- CORS configured for frontend domain

### PHI/PII Handling
- Patient data encrypted at rest (PostgreSQL)
- Access logs for audit trail (TODO)

---

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### API Testing
Use included scripts:
- `scripts/check_db_connection.py`
- Manual testing via Postman/cURL

---

## Troubleshooting

### Database Connection Issues
```bash
python scripts/check_db_connection.py
```

### Inngest Not Working
1. Check `INNGEST_DEV=1` is set
2. Verify Inngest dev server is running
3. Check logs in terminal

### Frontend Not Loading Data
1. Verify backend is running on port 8000
2. Check browser console for CORS errors
3. Verify API endpoints in Network tab

---

## Version History

- **v1.0** (Dec 2025): Initial release with refactored schema
  - Separated assessment tables
  - Pakistani patient data
  - Complete theme consistency
  - GDM assessment integration

---

## Contributing

### Code Style
- **Backend**: PEP 8, type hints
- **Frontend**: ESLint + Prettier
- **Commits**: Conventional commits format

### Pull Request Process
1. Create feature branch
2. Update documentation
3. Add tests
4. Submit PR with description

---

## Contact & Support

For technical questions or issues:
- Check existing documentation
- Review code comments
- Create issue in repository

---

**Last Updated**: December 8, 2025  
**Maintained By**: GOTHAM Development Team
