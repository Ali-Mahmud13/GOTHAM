# GOTHAM - Future Improvements

## Code Quality & Consistency

### 1. Async Function Consistency in Predictor Pipeline
**Priority:** Medium  
**Location:** `backend/app/agent/main_agent/`

Currently, predictor functions have inconsistent async patterns:
- `predict_gdp()` is async
- `generate_anemia_xai_report()` is sync

**Current Workaround:** `run_maternal.py` uses `inspect.iscoroutinefunction()` to check before awaiting.

**Recommended Fix:** Make all predictor functions async for consistency:
```python
# In anemia.py
async def generate_anemia_xai_report(WBC, RBC, HGB, HCT, MCV, MCH, MCHC, PLT):
    # ... existing code
```

Then remove the `inspect.iscoroutinefunction()` check in `run_maternal.py`.

---

## Model Compatibility

### 2. Retrain GDP Model for Python 3.13 Compatibility
**Priority:** High  
**Blocker:** GDP model unusable until fixed

The `GDP_model.pkl` was saved with sklearn 1.6.1 + older numpy random generator format. It's incompatible with:
- Python 3.13
- numpy 1.24+

**Fix:** Retrain the MLPClassifier model and save with `joblib.dump(model, 'GDP_model.pkl', protocol=4)` in the current environment.

---

## Database

### 3. Remove SQL Workaround for CBC Data
**Priority:** Low  
**Location:** `backend/app/services/patient_service.py`

A SQL workaround was added to bypass SQLModel ORM mapping issues for CBC fields. Once the materialized table schema is stable, consider:
- Running fresh migrations
- Removing the workaround code (lines 108-150)
