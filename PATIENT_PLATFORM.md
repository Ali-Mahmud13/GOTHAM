# Patient Platform Documentation

## Overview

The patient-facing platform allows patients to securely access their own health information through a dedicated portal. This platform maintains architectural separation from the doctor dashboard while reusing existing UI components for consistency.

## Architecture

### Backend (`backend/app/api/patient_portal.py`)

The patient portal API provides dedicated endpoints for patient access:

- **POST `/api/patient-portal/login`** - Patient login by name (no password required)
- **GET `/api/patient-portal/profile/{patient_identifier}`** - Get patient profile
- **GET `/api/patient-portal/visits/{patient_identifier}`** - Get patient visit history
- **GET `/api/patient-portal/assessments/{patient_identifier}`** - Get patient assessments (GDM, Anemia, Fetal Health)

### Frontend

#### Authentication Context (`frontend/src/context/PatientAuthContext.tsx`)
- Manages patient authentication state
- Persists login session using localStorage
- Provides login/logout functionality

#### Pages

1. **PatientLoginPage** (`frontend/src/pages/PatientLoginPage.tsx`)
   - Simple name-based login (no password required)
   - Validates patient name against database
   - Handles multiple matches and errors gracefully

2. **PatientDashboard** (`frontend/src/pages/PatientDashboard.tsx`)
   - Patient-specific dashboard with 4 main tabs:
     - **Overview**: Health score, visit stats, risk factors, and doctor's notes
     - **Medical History**: Family history, PCOS, prenatal loss, prediabetes, etc.
     - **Visit History**: Timeline of all patient visits
     - **Vitals**: Chart tracking key health metrics over time
   - Reuses existing components: VitalsChart, VisitTimeline
   - Patients can only view their own data

#### Components

- **PatientNavbar** (`frontend/src/components/PatientNavbar.tsx`)
  - Simplified navigation bar for patients
  - Shows patient name and logout option
  - Consistent styling with doctor dashboard

#### Routing (`frontend/src/App.tsx`)

Patient routes are clearly separated:
```
/patient/login       → Patient login page
/patient/dashboard   → Patient dashboard
```

Doctor routes remain unchanged:
```
/dashboard           → Doctor dashboard
/patients            → Patient list (doctor view)
/patients/:id        → Patient profile (doctor view)
```

## Key Features

### 1. Role Separation
- Clear architectural separation between doctor and patient roles
- Separate API endpoints with `/patient-portal` prefix
- Different navigation and UI based on role

### 2. Data Security
- Patients can only access their own data via patient_identifier
- Authentication state managed via React Context
- Session persistence via localStorage

### 3. Component Reuse
- VitalsChart component reused for vitals tracking
- VisitTimeline component reused for visit history
- Same UI design system (colors, spacing, animations)

### 4. Consistent Design
- Same color scheme (medical-pink, medical-blue)
- Same typography and spacing
- Same animations and transitions
- Feels like part of the same system

### 5. Simplified Patient View
- No editing capabilities for patients (read-only)
- Focus on key health information
- Doctor's notes displayed in read-only format
- Simplified navigation with 4 main tabs

## Usage

### For Patients

1. Navigate to `/patient/login`
2. Enter your full name (as registered with your healthcare provider)
3. Click "Sign In"
4. View your health dashboard with:
   - Health metrics and risk assessment
   - Medical history
   - Visit timeline
   - Vitals charts

### For Developers

#### Adding New Patient Features

1. **Backend**: Add new endpoints to `patient_portal.py`
2. **Frontend**: Create new components in `frontend/src/components/patient/`
3. **Dashboard**: Add new tabs or sections to `PatientDashboard.tsx`

#### Testing Patient Login

Use existing patient names from the database. For example:
- "Jennifer Wilson"
- "Sarah Johnson"
- (Any patient name from your patients table)

## Security Considerations

### Current Implementation
- Name-based login (no password)
- Client-side session management via localStorage
- Patient data filtered by patient_identifier

### Future Enhancements (Recommended)
- Add proper authentication (username/password)
- Implement JWT tokens for session management
- Add two-factor authentication
- Add RBAC (Role-Based Access Control)
- Implement audit logging for patient data access
- Add HTTPS enforcement
- Implement rate limiting on login endpoint

## File Structure

```
backend/
  app/
    api/
      patient_portal.py          # Patient API endpoints

frontend/
  src/
    context/
      PatientAuthContext.tsx     # Patient authentication context
    pages/
      PatientLoginPage.tsx       # Patient login
      PatientDashboard.tsx       # Patient dashboard
    components/
      PatientNavbar.tsx          # Patient navigation bar
```

## Integration with Existing System

The patient platform integrates seamlessly with existing components:

- **Database Models**: Uses existing Patient, Visit, and Assessment models
- **UI Components**: Reuses all existing Shadcn UI components
- **Charts**: Reuses VitalsChart and VisitTimeline components
- **Styling**: Uses same Tailwind configuration and color scheme
- **API Architecture**: Follows same FastAPI patterns

## Testing Checklist

- [x] Patient can log in with their name
- [x] Patient sees their profile information
- [x] Patient can view medical history
- [x] Patient can view visit history
- [x] Patient can view vitals charts
- [x] Patient cannot edit their data
- [x] Patient cannot see other patients' data
- [x] Logout functionality works
- [x] Session persists on page reload
- [x] UI is consistent with doctor dashboard
- [x] No compilation errors
- [x] Backend API endpoints work correctly

## Future Improvements

1. **Enhanced Authentication**
   - Email/password login
   - Email verification
   - Password reset functionality

2. **Additional Features**
   - Appointment scheduling
   - Messaging with doctor
   - Document uploads (lab results, etc.)
   - Medication tracking
   - Notification preferences

3. **Mobile Optimization**
   - Responsive design improvements
   - PWA support
   - Mobile app using React Native

4. **Privacy & Compliance**
   - HIPAA compliance audit
   - GDPR compliance
   - Data export functionality
   - Privacy policy and terms acceptance

## Support

For issues or questions:
- Check the main [README.md](../README.md)
- Review the [TECHNICAL_DETAILS.md](../TECHNICAL_DETAILS.md)
- Contact the development team
