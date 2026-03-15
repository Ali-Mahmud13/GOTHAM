# Authentication System Documentation

## Overview

The GOTHAM system now includes authentication for doctors and patients using username + password credentials.

## Database Structure

### AuthUser Table (`auth_users`)

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| username | String | Unique username for login |
| password_hash | String | SHA256 hashed password |
| role | String | User role: "doctor" or "patient" |
| patient_id | Integer | Foreign key to patients table (for patient users) |
| created_at | DateTime | Account creation timestamp |
| last_login | DateTime | Last successful login timestamp |
| is_active | Boolean | Whether account is active |

## Setup

### Initial Setup

Run the setup script to create the auth table and seed users:

```bash
python backend/scripts/setup_auth.py
```

This will:
1. Create the `auth_users` table
2. Add 1 doctor: **Dr. Ali Mahmud**
3. Add all existing patients as users

### Default Credentials

All users have the default password: **123**

**Doctor:**
- Username: `Dr. Ali Mahmud`
- Password: `123`
- Role: `doctor`

**Patients:**
- Username: `[Patient Name]` (e.g., "Ayesha Khan")
- Password: `123`
- Role: `patient`

## API Endpoints

### POST /auth/login

Login with username and password.

**Request Body:**
```json
{
  "username": "Dr. Ali Mahmud",
  "password": "123"
}
```

**Success Response (200):**
```json
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
```

**Patient Success Response (200):**
```json
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

**Error Response (401):**
```json
{
  "detail": "Invalid username or password"
}
```

### GET /auth/users

List all authentication users (for admin/testing).

**Response (200):**
```json
{
  "total": 9,
  "users": [
    {
      "id": 1,
      "username": "Dr. Ali Mahmud",
      "role": "doctor",
      "patient_id": null,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "last_login": "2024-01-01T12:00:00"
    },
    ...
  ]
}
```

## Testing

### Test Login Functionality

```bash
python backend/scripts/test_auth_login.py
```

This will test:
- Doctor login (valid)
- Patient login (valid)
- Invalid password
- Invalid username

### Test via API

Start the FastAPI server:
```bash
cd backend
uvicorn app.main:app --reload
```

Then visit: http://localhost:8000/docs

Use the interactive Swagger UI to test the `/auth/login` endpoint.

### cURL Example

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "Dr. Ali Mahmud", "password": "123"}'
```

## Current Users

### Doctor (1)
- Dr. Ali Mahmud

### Patients (8)
1. Ayesha Khan (P001)
2. Fatima Ahmed (P002)
3. Sana Malik (P003)
4. Mariam Sheikh (P004)
5. Mehreen Hassan (P005)
6. Hina Khan (P006)
7. Rabia Mahmood (P007)
8. Sana Jatt (P008)

## Security Notes

⚠️ **Current Implementation:**
- Uses SHA256 for password hashing (development only)
- All passwords are hardcoded to "123"
- No JWT tokens or session management

🔒 **For Production:**
- Replace SHA256 with bcrypt/argon2 (use `passlib` library)
- Implement JWT tokens for session management
- Add password complexity requirements
- Add rate limiting for login attempts
- Add email verification
- Add password reset functionality
- Store passwords securely (never in plain text)

## Future Enhancements

- [ ] Implement JWT token-based authentication
- [ ] Add password change functionality
- [ ] Add role-based access control (RBAC)
- [ ] Add session management
- [ ] Add "remember me" functionality
- [ ] Add 2FA (two-factor authentication)
- [ ] Add OAuth integration (Google, etc.)
- [ ] Add audit logging for login attempts
