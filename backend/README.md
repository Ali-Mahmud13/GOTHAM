# GOTHAM Backend

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
# Your Neon Postgres connection string
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require

# Inngest
INNGEST_APP_ID=GOTHAM

# App
DEBUG=false
```

### 3. Initialize Database

```bash
python scripts/init_db.py
```

## Running

### 1. Start FastAPI

```bash
cd backend
INNGEST_DEV=1 uvicorn app.main:app --reload (for windows: $env:INNGEST_DEV=1; uvicorn app.main:app --reload)
```


### 2. Start Inngest Dev Server (new terminal)

```bash
npx inngest-cli@latest dev
or
install -g inngest-cli
inngest dev
or npx inngest-cli@latest dev -u http://localhost:8000/api/inngest  #to auto sync


```

## Testing

### Trigger the example Inngest function:

```bash
python tests/test_trigger_event.py

```
### Check the agent setupYeah, no
```bash
python -m app.agent.cli
```

Then check http://localhost:8288 to see the function run with 3 steps.

## Database

### Models

Create models in `app/models/`:

```python
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    email: str = Field(unique=True)
    name: str
```

### Using in API

```python
from fastapi import Depends
from sqlmodel import Session
from app.db import get_session

@app.get("/users")
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users
```

## Adding Inngest Functions

1. Create file in `app/inngest/functions/`
2. Add to `ALL_FUNCTIONS` in `app/inngest/functions/__init__.py`
3. Restart FastAPI

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Config & settings
│   ├── db/               # Database setup
│   ├── inngest/          # Inngest functions
│   ├── models/           # SQLModel models
│   └── main.py           # App entry point
├── scripts/              # Utility scripts
├── tests/                # Tests
└── requirements.txt
```
