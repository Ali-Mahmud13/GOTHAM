# GOTHAM — Comprehensive Code Review

> Security, Performance & Architecture audit of the entire codebase

---

## 🔴 Critical Security Issues

### 1. API Keys Committed to Git History

> [!CAUTION]
> [.env](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/.env) contains **live** credentials for OpenAI, Groq, Gemini, Pinecone, and your Neon **database**. Even though `.gitignore` lists `.env`, these keys were committed in earlier commits and **remain in git history forever**.

**Impact**: Anyone who clones your repo (or if it was ever public) has full access to your database and paid AI APIs.

**Fix**:
1. **Rotate every key immediately** — generate new keys for OpenAI, Groq, Gemini, Pinecone, Cloudinary, and change the Neon database password
2. Run `git filter-branch` or use [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) to scrub `.env` from history
3. Add `.env.example` with placeholder values instead

---

### 2. SHA-256 Password Hashing (No Salt, No Stretch)

> [!CAUTION]
> [auth.py:54-56](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/auth.py#L54-L56) uses `hashlib.sha256()` — a **fast hash** with no salt. Attackers can crack passwords with rainbow tables in seconds.

```diff
- def hash_password(password: str) -> str:
-     return hashlib.sha256(password.encode()).hexdigest()
+ from passlib.context import CryptContext
+ pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
+ 
+ def hash_password(password: str) -> str:
+     return pwd_context.hash(password)
+ 
+ def verify_password(plain: str, hashed: str) -> bool:
+     return pwd_context.verify(plain, hashed)
```

---

### 3. No Token-Based Authentication (Header-Only Email Trust)

> [!WARNING]
> **All endpoints authenticate via a plain `X-User-Email` header** — anyone can spoof any user by setting this header. There are no JWTs, no session tokens, no signed cookies.

**Impact**: Any API client can impersonate any doctor or patient.

**Fix**: Implement JWT-based auth:
1. On login, issue a signed JWT with user ID, role, and expiry
2. Replace all `X-User-Email` header checks with a JWT verification dependency
3. Add token refresh and expiry logic

---

### 4. Patient Portal Login by Name Only

> [!WARNING]
> [patient_portal.py:81-115](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/patient_portal.py#L81-L115) allows login with **just a patient name** — no password, no verification. This is a direct **HIPAA-style violation** for a medical system.

---

### 5. No Authorization on Profile/Visit Endpoints

Endpoints like `GET /api/patient-portal/profile/{patient_identifier}` and `PUT /api/patient-portal/profile/{patient_identifier}` have **no ownership checks** — any user can read or modify any patient's profile by guessing the identifier (P001, P002, etc.).

Similarly, `DELETE /api/patients/{patient_identifier}` has **no auth** at all.

---

### 6. SQL Injection in Startup Migrations

[main.py:56](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/main.py#L56) uses f-string SQL:
```python
conn.execute(text(f"ALTER TABLE appointments ADD COLUMN {col_name} {col_type}"))
```
While the values are hardcoded currently, this pattern is dangerous and should use parameterized DDL.

---

### 7. `/auth/users` Endpoint Exposes All Users

[auth.py:224-244](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/auth.py#L224-L244) — `GET /auth/users` lists **all users** (emails, IDs, roles, activity) with zero authentication. This should be admin-only or removed entirely.

---

### 8. No Rate Limiting

No rate limiting on login, signup, chat, or assessment endpoints. Bad actors can:
- Brute-force passwords
- Abuse expensive LLM calls at your cost
- DDoS the server

---

### 9. Minimum Password Length is 3 Characters

[auth.py:42](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/auth.py#L42) — `if len(v) < 3` is effectively no password policy. Require 8+ characters with complexity rules.

---

## 🟠 Performance Issues

### 10. N+1 Query Problem in Dashboard Visits

[dashboard.py:328-348](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/dashboard.py#L328-L348) — `get_patient_visits()` loops over up to 50 visits and runs **4 separate queries per visit** (anemia, fetal, GDM, ultrasound). That's **200+ queries** for one page load.

**Fix**: Use `.options(selectinload(...))` or a single joined query to batch-load all assessments.

---

### 11. Assessment Results Stored In-Memory

[assessment_results.py](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/services/assessment_results.py) uses a global Python dictionary (`_assessment_results`). This means:
- All results are **lost on server restart**
- Memory grows unboundedly (no cleanup/TTL)
- Won't work with **multiple workers** (Gunicorn, multiple uvicorn instances)

**Fix**: Use Redis with TTL, or persist to PostgreSQL.

---

### 12. `get_next_patient_id()` Loads All Patients

[patients.py:113-133](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/patients.py#L112-L133) — Iterates **all patients** to find the max ID. Same issue in [auth.py:166-175](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/auth.py#L166-L175).

**Fix**: Use `SELECT MAX(...)` or a database sequence.

```python
# Replace linear scan with a single SQL query
result = session.exec(
    select(func.max(Patient.id))
).one()
```

---

### 13. Dashboard `get_dashboard_stats()` Fires 10+ Separate Queries

[dashboard.py:71-290](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/dashboard.py#L71-L290) — Each stat (total patients, high risk, medium risk, low risk, total visits, assessments this week × 3 types, recent patients, high risk patients) is a **separate round-trip** to the database.

**Fix**: Combine into 1-2 queries using `CASE WHEN` aggregation:
```sql
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE risk_level = 'high') AS high_risk,
    COUNT(*) FILTER (WHERE risk_level = 'medium') AS medium_risk,
    COUNT(*) FILTER (WHERE risk_level = 'low') AS low_risk
FROM patients WHERE doctor_id = :doc_id;
```

---

### 14. No Response Caching

Dashboard stats, risk distributions, and patient lists are re-computed on every request. Adding HTTP cache headers or short-lived Redis cache (30-60s TTL) would dramatically reduce DB load.

---

### 15. Appointments File is 1,151 Lines

[appointments.py](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/api/appointments.py) at **1,151 lines** is a maintenance burden. Split into:
- `availability.py` — Doctor availability CRUD
- `booking.py` — Booking and slot logic
- `notifications.py` — Reschedule/cancel notifications
- `registration.py` — Registration request handling

---

## 🟡 Architecture Improvements

### 16. No Proper Migration System

Startup runs raw `ALTER TABLE` DDL ([main.py:38-80](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/main.py#L38-L80)) to patch schema drift. This is fragile and error-prone.

**Fix**: Use **Alembic** for versioned database migrations:
```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

### 17. Deprecated `@app.on_event("startup")`

FastAPI has deprecated `on_event()`. Use **lifespan** context manager instead:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
```

---

### 18. Frontend Auth is Client-Side Only

[AuthContext.tsx](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/frontend/src/context/AuthContext.tsx) stores user data in `localStorage` with no signed token. Any user can modify localStorage to change their role from `patient` → `doctor` and access all endpoints.

**Fix**: After implementing JWT on the backend, store only the JWT in localStorage/httpOnly cookies, and validate it server-side on every request.

---

### 19. CORS is Wide Open for Development

[main.py:121-149](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/main.py#L120-L149) allows **any localhost origin** with `allow_origin_regex`, plus a custom middleware that force-injects CORS headers. For production, restrict to your actual deployed domain.

---

### 20. No Input Sanitization on Clinical Notes

Clinical notes, visit notes, and chat messages flow directly from user input → database → LLM prompts. This creates risk for:
- **Stored XSS** if notes are rendered as HTML
- **Prompt injection** if user-supplied text is concatenated into LLM prompts

---

### 21. Patient Service Singleton Anti-Pattern

[patient_service.py](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/services/patient_service.py) and [agent_service.py](file:///Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend/app/services/agent_service.py) use module-level singletons. This is **not thread-safe** under concurrent requests and makes testing harder.

**Fix**: Use FastAPI's dependency injection with proper scoping.

---

## 🛠 Quick Wins

| Issue | Effort | Impact |
|-------|--------|--------|
| Rotate all API keys | 30 min | 🔴 Critical |
| Switch to bcrypt (`passlib`) | 15 min | 🔴 Critical |
| Add JWT auth | 2-3 hrs | 🔴 Critical |
| Remove `/auth/users` or protect it | 5 min | 🔴 High |
| Enforce password policy (8+ chars) | 5 min | 🟠 Medium |
| Add rate limiting (`slowapi`) | 30 min | 🟠 Medium |
| Fix N+1 with `selectinload` | 1 hr | 🟠 High perf |
| Use `SELECT MAX` for patient IDs | 10 min | 🟡 Low |
| Switch to Alembic migrations | 1-2 hrs | 🟡 Medium |
| Add Redis for assessment results | 1-2 hrs | 🟡 Medium |
| Split `appointments.py` | 1 hr | 🟡 Maintainability |

---

## Summary Priority Order

1. **Rotate leaked credentials** — do this right now
2. **Implement JWT + bcrypt** — the current auth is effectively nonexistent
3. **Add authorization checks** — ensure users can only access their own data
4. **Fix N+1 queries and dashboard stats** — major performance wins
5. **Set up Alembic** — replace startup migration hacks
6. **Add rate limiting** — protect LLM endpoints from abuse
7. **Move assessment results to Redis/DB** — required for any multi-process deployment
