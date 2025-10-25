# GOTHAM Backend

## Getting Started

### 1. Start FastAPI

```bash
cd backend
INNGEST_DEV=1 uvicorn app.main:app --reload
```

### 2. Start Inngest Dev Server (new terminal)

```bash
npx inngest-cli@latest dev
```

## Testing

### Trigger the example function:

```bash
python tests/test_trigger_event.py
```

Then check http://localhost:8288 to see the function run with 3 steps.

## Adding New Functions

1. Create file in `app/inngest/functions/`
2. Add to `ALL_FUNCTIONS` in `app/inngest/functions/__init__.py`
3. Restart FastAPI
