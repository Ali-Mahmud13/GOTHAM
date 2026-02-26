-- ============================================================================
-- PostgreSQL Trigger Function for Patient Latest Assessments
-- ============================================================================
-- 
-- Purpose: Automatically maintain patient_latest_assessments table with the
--          latest non-null value for each assessment field.
--
-- Triggered on: INSERT or UPDATE to gdm_assessments, anemia_assessments,
--               fetal_health_assessments
--
-- Author: GOTHAM Backend Team
-- Created: 2024-12-10
-- ============================================================================

-- Drop existing triggers and function if they exist
DROP TRIGGER IF EXISTS gdm_update_latest ON gdm_assessments;
DROP TRIGGER IF EXISTS anemia_update_latest ON anemia_assessments;
DROP TRIGGER IF EXISTS fetal_update_latest ON fetal_health_assessments;
DROP FUNCTION IF EXISTS update_patient_latest_assessments();

-- ============================================================================
-- Main Trigger Function
-- ============================================================================

CREATE OR REPLACE FUNCTION update_patient_latest_assessments()
RETURNS TRIGGER AS $$
DECLARE
    v_patient_id INT;
BEGIN
    -- Get patient_id from the visit
    SELECT patient_id INTO v_patient_id 
    FROM visits WHERE id = NEW.visit_id;
    
    -- Create record if doesn't exist
    INSERT INTO patient_latest_assessments (patient_id, last_updated)
    VALUES (v_patient_id, NOW())
    ON CONFLICT (patient_id) DO NOTHING;
    
    -- ========================================================================
    -- Update GDM fields if this is from gdm_assessments
    -- ========================================================================
    IF TG_TABLE_NAME = 'gdm_assessments' THEN
        UPDATE patient_latest_assessments
        SET
            glucose_level = COALESCE(NEW.glucose_level, glucose_level),
            glucose_updated_at = CASE 
                WHEN NEW.glucose_level IS NOT NULL THEN NOW() 
                ELSE glucose_updated_at 
            END,
            
            sys_bp = COALESCE(NEW.blood_pressure_systolic, sys_bp),
            sys_bp_updated_at = CASE 
                WHEN NEW.blood_pressure_systolic IS NOT NULL THEN NOW() 
                ELSE sys_bp_updated_at 
            END,
            
            dia_bp = COALESCE(NEW.blood_pressure_diastolic, dia_bp),
            dia_bp_updated_at = CASE 
                WHEN NEW.blood_pressure_diastolic IS NOT NULL THEN NOW() 
                ELSE dia_bp_updated_at 
            END,
            
            bmi = COALESCE(NEW.bmi, bmi),
            bmi_updated_at = CASE 
                WHEN NEW.bmi IS NOT NULL THEN NOW() 
                ELSE bmi_updated_at 
            END,
            
            ogtt = COALESCE(NEW.ogtt, ogtt),
            ogtt_updated_at = CASE 
                WHEN NEW.ogtt IS NOT NULL THEN NOW() 
                ELSE ogtt_updated_at 
            END,
            
            hdl = COALESCE(NEW.hdl, hdl),
            hdl_updated_at = CASE 
                WHEN NEW.hdl IS NOT NULL THEN NOW() 
                ELSE hdl_updated_at 
            END,
            
            gestation_weeks = COALESCE(NEW.gestation_weeks, gestation_weeks),
            gestation_weeks_updated_at = CASE 
                WHEN NEW.gestation_weeks IS NOT NULL THEN NOW() 
                ELSE gestation_weeks_updated_at 
            END,
            
            sedentary_lifestyle = COALESCE(NEW.sedentary_lifestyle, sedentary_lifestyle),
            sedentary_lifestyle_updated_at = CASE 
                WHEN NEW.sedentary_lifestyle IS NOT NULL THEN NOW() 
                ELSE sedentary_lifestyle_updated_at 
            END,
            
            insulin_level = COALESCE(NEW.insulin_level, insulin_level),
            insulin_level_updated_at = CASE 
                WHEN NEW.insulin_level IS NOT NULL THEN NOW() 
                ELSE insulin_level_updated_at 
            END,
            
            last_updated = NOW()
        WHERE patient_id = v_patient_id;
    END IF;
    
    -- ========================================================================
    -- Update Anemia/CBC fields if this is from anemia_assessments
    -- ========================================================================
    IF TG_TABLE_NAME = 'anemia_assessments' THEN
        UPDATE patient_latest_assessments
        SET
            wbc = COALESCE(NEW.wbc, wbc),
            wbc_updated_at = CASE 
                WHEN NEW.wbc IS NOT NULL THEN NOW() 
                ELSE wbc_updated_at 
            END,
            
            rbc = COALESCE(NEW.rbc, rbc),
            rbc_updated_at = CASE 
                WHEN NEW.rbc IS NOT NULL THEN NOW() 
                ELSE rbc_updated_at 
            END,
            
            hgb = COALESCE(NEW.hgb, hgb),
            hgb_updated_at = CASE 
                WHEN NEW.hgb IS NOT NULL THEN NOW() 
                ELSE hgb_updated_at 
            END,
            
            hct = COALESCE(NEW.hct, hct),
            hct_updated_at = CASE 
                WHEN NEW.hct IS NOT NULL THEN NOW() 
                ELSE hct_updated_at 
            END,
            
            mcv = COALESCE(NEW.mcv, mcv),
            mcv_updated_at = CASE 
                WHEN NEW.mcv IS NOT NULL THEN NOW() 
                ELSE mcv_updated_at 
            END,
            
            mch = COALESCE(NEW.mch, mch),
            mch_updated_at = CASE 
                WHEN NEW.mch IS NOT NULL THEN NOW() 
                ELSE mch_updated_at 
            END,
            
            mchc = COALESCE(NEW.mchc, mchc),
            mchc_updated_at = CASE 
                WHEN NEW.mchc IS NOT NULL THEN NOW() 
                ELSE mchc_updated_at 
            END,
            
            plt = COALESCE(NEW.plt, plt),
            plt_updated_at = CASE 
                WHEN NEW.plt IS NOT NULL THEN NOW() 
                ELSE plt_updated_at 
            END,
            
            last_updated = NOW()
        WHERE patient_id = v_patient_id;
    END IF;
    
    -- ========================================================================
    -- Update Fetal Health fields if this is from fetal_health_assessments
    -- ========================================================================
    IF TG_TABLE_NAME = 'fetal_health_assessments' THEN
        UPDATE patient_latest_assessments
        SET
            fetal_baseline_value = COALESCE(NEW.baseline_value, fetal_baseline_value),
            fetal_baseline_updated_at = CASE 
                WHEN NEW.baseline_value IS NOT NULL THEN NOW() 
                ELSE fetal_baseline_updated_at 
            END,
            
            fetal_accelerations = COALESCE(NEW.accelerations, fetal_accelerations),
            fetal_accelerations_updated_at = CASE 
                WHEN NEW.accelerations IS NOT NULL THEN NOW() 
                ELSE fetal_accelerations_updated_at 
            END,
            
            fetal_movement = COALESCE(NEW.fetal_movement, fetal_movement),
            fetal_movement_updated_at = CASE 
                WHEN NEW.fetal_movement IS NOT NULL THEN NOW() 
                ELSE fetal_movement_updated_at 
            END,
            
            last_updated = NOW()
        WHERE patient_id = v_patient_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Create Triggers on Assessment Tables
-- ============================================================================

CREATE TRIGGER gdm_update_latest
AFTER INSERT OR UPDATE ON gdm_assessments
FOR EACH ROW
EXECUTE FUNCTION update_patient_latest_assessments();

CREATE TRIGGER anemia_update_latest
AFTER INSERT OR UPDATE ON anemia_assessments
FOR EACH ROW
EXECUTE FUNCTION update_patient_latest_assessments();

CREATE TRIGGER fetal_update_latest
AFTER INSERT OR UPDATE ON fetal_health_assessments
FOR EACH ROW
EXECUTE FUNCTION update_patient_latest_assessments();

-- ============================================================================
-- Verification
-- ============================================================================

-- Verify triggers were created
SELECT 
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name IN ('gdm_update_latest', 'anemia_update_latest', 'fetal_update_latest');

-- Done!
