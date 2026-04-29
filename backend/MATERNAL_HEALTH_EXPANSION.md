# Maternal Health Pipeline Expansion

## Overview
Expand GOTHAM to support additional maternal health models beyond GDM (Gestational Diabetes Mellitus).

## New Model Features

### ANEMIA Detection
- WBC (White Blood Cell count)
- RBC (Red Blood Cell count)
- HGB (Hemoglobin)
- HCT (Hematocrit)
- MCV (Mean Corpuscular Volume)
- MCH (Mean Corpuscular Hemoglobin)
- MCHC (Mean Corpuscular Hemoglobin Concentration)
- PLT (Platelet count)

### MATERNAL MORTALITY Risk
- Age
- SystolicBP (Systolic Blood Pressure)
- DiastolicBP (Diastolic Blood Pressure)
- BS (Blood Sugar)
- BodyTemp (Body Temperature)
- HeartRate

## Architecture Approach (Agreed)

### Simple Approach ✅
1. **Storage**: Expand `visits` table with new columns
   - Each visit stores only what was measured that day
   - Fields can be NULL if not measured
   
2. **Feature Aggregation**: Application-level caching
   - Service method: `get_latest_features(patient_id)`
   - Use Python `@lru_cache` or Redis
   - Invalidate cache after new visit creation

3. **No materialized views** (start simple, add later if needed)

## Implementation Steps (Future)

1. **Database Migration**
   - Add columns to `Visit` model for ANEMIA features
   - Add columns for MATERNAL MORTALITY features

2. **AI Extraction**
   - Update LLM prompt in `DataEntryService` to recognize new fields
   - Map extracted values to new database columns

3. **Service Layer**
   - Create `get_latest_features(patient_id)` method
   - Implement caching strategy
   - Add cache invalidation on visit creation

4. **Model Endpoints**
   - `POST /api/predict/anemia` - ANEMIA risk prediction
   - `POST /api/predict/mortality` - MATERNAL MORTALITY risk prediction

5. **Frontend Updates**
   - Categorize extracted fields (GDM / ANEMIA / MORTALITY)
   - Display prediction results when data available
   - Show which features are missing for each model

## Workflow

**Patient Creation:**
```
Doctor → Create Patient → Save (Name, Age, Contact, Address)
```

**Data Entry per Visit:**
```
Doctor → Select Patient → Enter Clinical Notes
         ↓
    AI Extracts Available Fields
         ↓
    Save as New Visit (only measured values)
         ↓
    Cache Invalidation for patient
```

**Model Prediction:**
```
Get Latest Features from Cache/DB
         ↓
    Run Prediction (ANEMIA / MORTALITY / GDM)
         ↓
    Return Risk Assessment
```

## Benefits
- ✅ Incremental data collection
- ✅ Temporal tracking of patient progression
- ✅ Reuses existing architecture
- ✅ Flexible model addition
