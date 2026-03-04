# Frontend Authentication Implementation

## Overview

The GOTHAM frontend now includes a complete authentication system for both doctors and patients using the new `/auth/login` API endpoint.

## Changes Made

### 1. New Auth Context (`src/context/AuthContext.tsx`)

Created a unified authentication context that handles both doctor and patient authentication:

- **User Interface**: Stores user data including role, username, and patient information
- **Role-based helpers**: `isDoctor` and `isPatient` computed properties
- **Persistent sessions**: Automatically saves to/loads from localStorage
- **Type-safe**: Full TypeScript support

### 2. Updated Login Pages

#### Patient Login (`src/pages/PatientLoginPage.tsx`)
- Added password field for secure authentication
- Uses new `/auth/login` endpoint
- Validates user role (must be patient)
- Displays patient information on successful login
- Link to doctor portal at the bottom

#### Doctor Login (`src/pages/DoctorLoginPage.tsx`) - NEW
- Similar UI to patient login with different styling
- Uses same `/auth/login` endpoint
- Validates user role (must be doctor)
- Redirects to dashboard on successful login
- Link to patient portal at the bottom

### 3. Updated Components

#### Patient Dashboard (`src/pages/PatientDashboard.tsx`)
- Now uses new `AuthContext` instead of old `PatientAuthContext`
- Extracts patient identifier from user object
- Proper authentication checks before loading data

#### Patient Navbar (`src/components/PatientNavbar.tsx`)
- Updated to use new `AuthContext`
- Displays patient name from user object

### 4. Routing Updates (`src/App.tsx`)

```tsx
<AuthProvider>
  <PatientAuthProvider>  {/* Kept for backward compatibility */}
    <Routes>
      {/* Doctor Routes */}
      <Route path="/doctor/login" element={<DoctorLoginPage />} />
      <Route path="/login" element={<Navigate to="/doctor/login" />} />
      <Route path="/dashboard" element={<Index />} />
      
      {/* Patient Routes */}
      <Route path="/patient/login" element={<PatientLoginPage />} />
      <Route path="/patient/dashboard" element={<PatientDashboard />} />
    </Routes>
  </PatientAuthProvider>
</AuthProvider>
```

## Testing the Implementation

### 1. Start the Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```

### 3. Test Doctor Login

1. Navigate to http://localhost:5173/doctor/login
2. Enter credentials:
   - Name: `Dr. Ali Mahmud`
   - Password: `123`
3. Should redirect to dashboard on success

### 4. Test Patient Login

1. Navigate to http://localhost:5173/patient/login
2. Enter any patient credentials (e.g.):
   - Name: `Ayesha Khan`
   - Password: `123`
3. Should redirect to patient dashboard with profile info

## Available Login Credentials

### Doctor
- **Name**: Dr. Ali Mahmud
- **Password**: 123

### Patients (all with password: 123)
1. Ayesha Khan (P001)
2. Fatima Ahmed (P002)
3. Sana Malik (P003)
4. Mariam Sheikh (P004)
5. Mehreen Hassan (P005)
6. Hina Khan (P006)
7. Rabia Mahmood (P007)
8. Sana Jatt (P008)

## API Integration

### Login Request

```typescript
POST http://localhost:8000/auth/login

Body:
{
  "username": "Dr. Ali Mahmud",
  "password": "123"
}

Response (Doctor):
{
  "success": true,
  "message": "Welcome, Dr. Ali Mahmud!",
  "user": {
    "id": 1,
    "username": "Dr. Ali Mahmud",
    "role": "doctor",
    "patient_id": null
  }
}

Response (Patient):
{
  "success": true,
  "message": "Welcome, Ayesha Khan!",
  "user": {
    "id": 2,
    "username": "Ayesha Khan",
    "role": "patient",
    "patient_id": 40,
    "patient_info": {
      "patient_identifier": "P001",
      "name": "Ayesha Khan",
      "age": 28,
      "contact_number": "+92-300-1234567",
      "risk_level": "high"
    }
  }
}
```

## Session Management

- Authentication state is stored in `localStorage` under the key `auth_user`
- Persists across browser refreshes
- Call `logout()` from `useAuth()` to clear session and redirect

## Using Authentication in Components

```typescript
import { useAuth } from '@/context/AuthContext';

function MyComponent() {
  const { isAuthenticated, user, isDoctor, isPatient, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }
  
  return (
    <div>
      <h1>Welcome, {user?.username}</h1>
      {isDoctor && <p>You are a doctor</p>}
      {isPatient && <p>You are a patient</p>}
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

## Protected Routes (Future Enhancement)

To add route protection, create a `ProtectedRoute` component:

```typescript
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export const ProtectedRoute = ({ 
  children, 
  requireRole 
}: { 
  children: React.ReactNode;
  requireRole?: 'doctor' | 'patient';
}) => {
  const { isAuthenticated, user } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/doctor/login" replace />;
  }
  
  if (requireRole && user?.role !== requireRole) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

// Usage in App.tsx
<Route 
  path="/dashboard" 
  element={
    <ProtectedRoute requireRole="doctor">
      <Index />
    </ProtectedRoute>
  } 
/>
```

## Navigation Structure

```
/ (Landing Page)
├── /doctor/login (Doctor Login)
│   └── /dashboard (Doctor Dashboard - requires doctor role)
│   └── /patients (Patients List)
│   └── /chat (AI Chat)
│   └── /data-entry (Data Entry)
│
└── /patient/login (Patient Login)
    └── /patient/dashboard (Patient Dashboard - requires patient role)
```

## Logout Functionality

Both portals include logout functionality in their navigation:

- **Patient**: Click user avatar → Log out
- **Doctor**: Similar logout option in navbar

Logout will:
1. Clear authentication state
2. Remove localStorage data
3. Redirect to appropriate login page

## Styling Notes

- Patient portal uses pink/blue gradient theme
- Doctor portal uses blue/purple gradient theme
- Both use consistent Shadcn UI components
- Responsive design for mobile and desktop

## Error Handling

Both login pages handle:
- Empty username/password
- Invalid credentials (401 error)
- Wrong user role (doctor trying patient login or vice versa)
- Network errors
- Server errors

All errors are displayed in a user-friendly alert box below the form.

## Future Improvements

- [ ] Add "Remember Me" checkbox
- [ ] Add "Forgot Password" functionality
- [ ] Implement JWT tokens for better security
- [ ] Add token refresh mechanism
- [ ] Add session timeout warnings
- [ ] Add role-based route guards
- [ ] Add loading states for protected routes
- [ ] Add password strength requirements
- [ ] Add multi-factor authentication
