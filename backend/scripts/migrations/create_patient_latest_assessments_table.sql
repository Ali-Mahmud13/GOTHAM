-- CREATE patient_latest_assessments table
-- Run this before the triggers can work

CREATE TABLE IF NOT EXISTS patient_latest_assessments (
    patient_id INTEGER PRIMARY KEY REFERENCES patients(id),
    
    -- GDM fields
    glucose_level DOUBLE PRECISION,
    glucose_updated_at TIMESTAMP,
    sys_bp INTEGER,
    sys_bp_updated_at TIMESTAMP,
    dia_bp INTEGER,
    dia_bp_updated_at TIMESTAMP,
    bmi DOUBLE PRECISION,
    bmi_updated_at TIMESTAMP,
    ogtt DOUBLE PRECISION,
    ogtt_updated_at TIMESTAMP,
    hdl DOUBLE PRECISION,
    hdl_updated_at TIMESTAMP,
    gestation_weeks INTEGER,
    gestation_weeks_updated_at TIMESTAMP,
    sedentary_lifestyle BOOLEAN,
    sedentary_lifestyle_updated_at TIMESTAMP,
    insulin_level DOUBLE PRECISION,
    insulin_level_updated_at TIMESTAMP,
    
    -- Anemia/CBC fields
    wbc DOUBLE PRECISION,
    wbc_updated_at TIMESTAMP,
    rbc DOUBLE PRECISION,
    rbc_updated_at TIMESTAMP,
    hgb DOUBLE PRECISION,
    hgb_updated_at TIMESTAMP,
    hct DOUBLE PRECISION,
    hct_updated_at TIMESTAMP,
    mcv DOUBLE PRECISION,
    mcv_updated_at TIMESTAMP,
    mch DOUBLE PRECISION,
    mch_updated_at TIMESTAMP,
    mchc DOUBLE PRECISION,
    mchc_updated_at TIMESTAMP,
    plt DOUBLE PRECISION,
    plt_updated_at TIMESTAMP,
    
    -- Fetal Health fields
    fetal_baseline_value DOUBLE PRECISION,
    fetal_baseline_updated_at TIMESTAMP,
    fetal_accelerations DOUBLE PRECISION,
    fetal_accelerations_updated_at TIMESTAMP,
    fetal_movement DOUBLE PRECISION,
    fetal_movement_updated_at TIMESTAMP,
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Verify
SELECT 'Table created successfully!' AS status;
