# Inngest Background Jobs Setup

## Overview

GOTHAM now uses Inngest for background processing of risk assessments. This allows the API to respond immediately while heavy ML model computations run asynchronously.

## Architecture

### Background Jobs

1. **`agent_assessment`** - Main orchestrator that runs the full LangGraph workflow
2. **`maternal_prediction`** - Runs maternal health ML models (GDP, preeclampsia, etc.)
3. **`fetal_prediction`** - Runs fetal health ML models
4. **`rag_retrieval`** - Performs RAG retrieval from medical literature

### API Endpoints

#### `/chat` (Synchronous)
Traditional chat endpoint - waits for full agent response before returning.

```bash
POST /api/chat
{
  "message": "What is gestational diabetes?",
  "session_id": "optional-session-id"
}

Response:
{
  "response": "Gestational diabetes is...",
  "session_id": "session-123"
}
```

#### `/chat/assess` (Asynchronous)
Background assessment endpoint - returns immediately with assessment_id.

```bash
POST /api/chat/assess
{
  "message": "Assess risk for patient",
  "session_id": "optional-session-id",
  "patient_id": "P-123"
}

Response:
{
  "assessment_id": "a1b2c3d4-...",
  "session_id": "session-123",
  "status": "processing",
  "message": "Risk assessment started. Check status using assessment_id."
}
```

## File Structure

```
backend/app/inngest/functions/
├── __init__.py                    # Registers all functions
├── agent_assessment.py            # Main workflow orchestrator
├── maternal_prediction.py         # Maternal health models
├── fetal_prediction.py            # Fetal health models
├── rag_retrieval.py               # RAG retrieval
├── risk_processing.py             # (existing)
└── example.py                     # (existing)
```

## Event Flow

### Background Assessment Flow

```
1. Doctor sends request
   POST /api/chat/assess
   
2. API generates assessment_id and triggers Inngest
   Event: "agent/assessment.request"
   
3. API returns immediately with assessment_id
   
4. Inngest runs agent workflow in background
   - Checks clarity
   - Decides which predictions to run
   - Loads patient data
   - Runs maternal/fetal predictions
   - Performs RAG retrieval
   - Generates final response
   
5. Results stored (TODO: implement storage)
   
6. Doctor notified (TODO: implement notification)
```

## Inngest Events

### `agent/assessment.request`
Triggers the main assessment workflow.

**Data:**
- `assessment_id`: Unique identifier
- `message`: User's query
- `session_id`: Session ID for conversation
- `patient_id`: Optional patient identifier

### `prediction/maternal.run`
Triggers maternal health predictions.

**Data:**
- `assessment_id`: Unique identifier
- `patient_data`: Patient data dictionary
- `models`: List of models to run (e.g., ['gdp', 'preeclampsia'])

### `prediction/fetal.run`
Triggers fetal health predictions.

**Data:**
- `assessment_id`: Unique identifier
- `patient_data`: Patient data dictionary
- `models`: List of models to run

### `rag/retrieve`
Triggers RAG retrieval.

**Data:**
- `assessment_id`: Unique identifier
- `keywords`: Keywords for retrieval
- `query`: Original query

## Running Inngest

### Development

1. Start Inngest dev server:
```bash
npx inngest-cli@latest dev
```

2. Start FastAPI with Inngest enabled:
```bash
cd backend
INNGEST_DEV=1 uvicorn app.main:app --reload
```

3. Access Inngest dashboard:
```
http://localhost:8288
```

### Testing

Trigger a background assessment:

```bash
curl -X POST http://localhost:8000/api/chat/assess \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Assess risk for patient P-123",
    "patient_id": "P-123"
  }'
```

Check Inngest dashboard to see the job running.

## Implementation Details

### Simple Approach (Current)

- Full agent workflow runs as single background job
- Maternal and fetal predictions currently run within the workflow
- No parallelization yet (can be added later)
- Clean, modular code structure

### Future Enhancements (Optional)

1. **Parallel Execution**: Run maternal and fetal models in parallel
2. **Real-time Updates**: Add SSE or WebSocket for progress updates
3. **Result Storage**: Store assessment results in database
4. **Status Endpoint**: Add `/assessment/{assessment_id}` to check status
5. **Notifications**: Notify doctor when assessment completes

## Key Functions

### `agent_assessment.py`

```python
@inngest_client.create_function(
    fn_id="agent-assessment",
    trigger=inngest_client.create_trigger(event="agent/assessment.request"),
)
async def process_agent_assessment(ctx: Context, step: Step):
    # Runs full LangGraph workflow
    result = await step.run("run-agent-workflow", run_agent_workflow, ...)
    return result
```

### `maternal_prediction.py`

```python
@inngest_client.create_function(
    fn_id="maternal-prediction",
    trigger=inngest_client.create_trigger(event="prediction/maternal.run"),
)
async def run_maternal_prediction(ctx: Context, step: Step):
    # Runs maternal health models
    results = await step.run("run-maternal-models", execute_maternal_models, ...)
    return results
```

## Benefits

1. ✅ **Immediate API Response** - Doctor doesn't wait for ML models
2. ✅ **Reliability** - Automatic retries on failure
3. ✅ **Observability** - Track all assessments in Inngest dashboard
4. ✅ **Scalability** - Handle multiple assessments simultaneously
5. ✅ **Audit Trail** - Complete history of all assessments

## TODO

- [ ] Add database storage for assessment results
- [ ] Add status check endpoint
- [ ] Add notification system
- [ ] Implement parallel execution for models
- [ ] Add real-time progress updates (SSE)
- [ ] Add timeout handling
- [ ] Add comprehensive error handling
- [ ] Add metrics and monitoring

---

**Created**: November 12, 2025  
**Status**: ✅ Basic implementation complete

