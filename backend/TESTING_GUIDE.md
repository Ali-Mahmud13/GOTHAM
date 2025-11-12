# Testing Inngest Background Jobs

## Prerequisites

Before testing, you need to have both servers running:

### 1. Start Inngest Dev Server

```bash
npx inngest-cli@latest dev
```

This will start the Inngest dev server on `http://localhost:8288`

### 2. Start FastAPI Server

```bash
cd backend
uvicorn app.main:app --reload
```

This will start FastAPI on `http://localhost:8000`

---

## Testing Methods

### Method 1: Using CLI (Recommended for Quick Testing)

#### Direct Mode (Without Inngest)
```bash
cd backend
python -m app.agent.cli
```

This runs the agent directly without background jobs.

#### Inngest Mode (With Background Jobs)
```bash
cd backend
python -m app.agent.cli --inngest
```

This triggers Inngest background jobs. You'll see:
- Assessment ID generated
- Link to Inngest dashboard
- Job running in the background

**Example:**
```bash
$ python -m app.agent.cli --inngest

============================================================
Antenatal Care Assistant - CLI Mode (Inngest)
============================================================
⚠️  Make sure Inngest dev server is running!
   Run: npx inngest-cli@latest dev
   Dashboard: http://localhost:8288
============================================================
Type 'exit' or 'quit' to end the conversation

You: Assess risk for patient P-001

[Triggering background assessment: 3f7a1b2c-...]

✓ Assessment triggered successfully!
  Assessment ID: 3f7a1b2c-...
  Check Inngest dashboard: http://localhost:8288
  (Results will appear in the dashboard)
```

---

### Method 2: Using Test Script

#### Test Full Assessment
```bash
cd backend
python tests/test_inngest_trigger.py
```

#### Test Individual Components
```bash
# Test maternal prediction only
python tests/test_inngest_trigger.py maternal

# Test fetal prediction only
python tests/test_inngest_trigger.py fetal

# Test RAG retrieval only
python tests/test_inngest_trigger.py rag
```

---

### Method 3: Using API (cURL)

#### Background Assessment
```bash
curl -X POST http://localhost:8000/api/chat/assess \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Assess risk for patient P-001",
    "patient_id": "P-001"
  }'
```

**Response:**
```json
{
  "assessment_id": "3f7a1b2c-...",
  "session_id": "a1b2c3d4-...",
  "status": "processing",
  "message": "Risk assessment started. Check status using assessment_id."
}
```

#### Traditional Chat (Synchronous)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is gestational diabetes?",
    "session_id": "test-session-123"
  }'
```

---

### Method 4: Using API Docs (Interactive)

1. Open browser: `http://localhost:8000/docs`
2. Find `/api/chat/assess` endpoint
3. Click "Try it out"
4. Enter request body:
   ```json
   {
     "message": "Assess risk for patient",
     "patient_id": "P-001"
   }
   ```
5. Click "Execute"
6. Get `assessment_id` from response
7. Check Inngest dashboard

---

## Viewing Results

### Inngest Dashboard

1. Open: `http://localhost:8288`
2. You'll see:
   - **Functions**: All registered Inngest functions
   - **Runs**: All executed jobs
   - **Events**: All triggered events

### What to Look For

#### In Functions Tab:
- `agent-assessment` - Main workflow
- `maternal-prediction` - Maternal models
- `fetal-prediction` - Fetal models
- `rag-retrieval` - RAG retrieval

#### In Runs Tab:
- Click on any run to see:
  - Steps executed
  - Input data
  - Output results
  - Execution time
  - Any errors

---

## Example Test Workflow

### Complete Test Flow

1. **Start servers:**
   ```bash
   # Terminal 1
   npx inngest-cli@latest dev
   
   # Terminal 2
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Run CLI in Inngest mode:**
   ```bash
   # Terminal 3
   cd backend
   python -m app.agent.cli --inngest
   ```

3. **Test assessment:**
   ```
   You: Assess risk for patient P-001
   ```

4. **Check Inngest dashboard:**
   - Open `http://localhost:8288`
   - Go to "Runs" tab
   - Find your assessment
   - Click to see details

5. **Verify execution:**
   - Check all steps completed
   - Verify data passed correctly
   - Check for any errors

---

## Common Issues

### Issue 1: "Connection refused" error
**Solution:** Make sure Inngest dev server is running
```bash
npx inngest-cli@latest dev
```

### Issue 2: Function not appearing in dashboard
**Solution:** 
1. Restart FastAPI server
2. Check `app/inngest/functions/__init__.py` - function should be in `ALL_FUNCTIONS`
3. Check server logs for errors

### Issue 3: Job runs but fails
**Solution:**
1. Check Inngest dashboard for error details
2. Check FastAPI logs for exceptions
3. Verify all dependencies are installed
4. Check that patient data format is correct

---

## Testing Checklist

- [ ] Inngest dev server running
- [ ] FastAPI server running
- [ ] Can see functions in Inngest dashboard
- [ ] CLI triggers assessment successfully
- [ ] Assessment appears in Inngest "Runs" tab
- [ ] All steps execute without errors
- [ ] Can trigger via API endpoint
- [ ] Can trigger via test script

---

## Next Steps

After successful testing:

1. **Add Result Storage**: Store assessment results in database
2. **Add Status Endpoint**: Check assessment status via API
3. **Add Notifications**: Notify when assessment completes
4. **Add Frontend Integration**: Update React app to use background assessments
5. **Add Parallel Execution**: Run maternal/fetal models in parallel

---

## Quick Reference

### Start Everything
```bash
# Terminal 1: Inngest
npx inngest-cli@latest dev

# Terminal 2: FastAPI
cd backend
uvicorn app.main:app --reload

# Terminal 3: Test
cd backend
python -m app.agent.cli --inngest
```

### Check Dashboards
- Inngest: http://localhost:8288
- FastAPI Docs: http://localhost:8000/docs
- FastAPI Health: http://localhost:8000

---

**Happy Testing! 🚀**

