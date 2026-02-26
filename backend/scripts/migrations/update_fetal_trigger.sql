-- Update fetal trigger to include ALL CTG fields

DROP FUNCTION IF EXISTS update_patient_latest_assessments() CASCADE;

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
    
    -- Update Fetal Health fields if this is from fetal_health_assessments
    IF TG_TABLE_NAME = 'fetal_health_assessments' THEN
        UPDATE patient_latest_assessments
        SET
            -- Baseline and movements
            fetal_baseline_value = COALESCE(NEW.baseline_value, fetal_baseline_value),
            fetal_baseline_updated_at = CASE WHEN NEW.baseline_value IS NOT NULL THEN NOW() ELSE fetal_baseline_updated_at END,
            
            fetal_accelerations = COALESCE(NEW.accelerations, fetal_accelerations),
            fetal_accelerations_updated_at = CASE WHEN NEW.accelerations IS NOT NULL THEN NOW() ELSE fetal_accelerations_updated_at END,
            
            fetal_movement = COALESCE(NEW.fetal_movement, fetal_movement),
            fetal_movement_updated_at = CASE WHEN NEW.fetal_movement IS NOT NULL THEN NOW() ELSE fetal_movement_updated_at END,
            
            -- Contractions and decelerations
            uterine_contractions = COALESCE(NEW.uterine_contractions, uterine_contractions),
            uterine_contractions_updated_at = CASE WHEN NEW.uterine_contractions IS NOT NULL THEN NOW() ELSE uterine_contractions_updated_at END,
            
            light_decelerations = COALESCE(NEW.light_decelerations, light_decelerations),
            light_decelerations_updated_at = CASE WHEN NEW.light_decelerations IS NOT NULL THEN NOW() ELSE light_decelerations_updated_at END,
            
            severe_decelerations = COALESCE(NEW.severe_decelerations, severe_decelerations),
            severe_decelerations_updated_at = CASE WHEN NEW.severe_decelerations IS NOT NULL THEN NOW() ELSE severe_decelerations_updated_at END,
            
            prolongued_decelerations = COALESCE(NEW.prolongued_decelerations, prolongued_decelerations),
            prolongued_decelerations_updated_at = CASE WHEN NEW.prolongued_decelerations IS NOT NULL THEN NOW() ELSE prolongued_decelerations_updated_at END,
            
            -- Variability
            abnormal_short_term_variability = COALESCE(NEW.abnormal_short_term_variability, abnormal_short_term_variability),
            abnormal_short_term_variability_updated_at = CASE WHEN NEW.abnormal_short_term_variability IS NOT NULL THEN NOW() ELSE abnormal_short_term_variability_updated_at END,
            
            mean_value_of_short_term_variability = COALESCE(NEW.mean_value_of_short_term_variability, mean_value_of_short_term_variability),
            mean_value_of_short_term_variability_updated_at = CASE WHEN NEW.mean_value_of_short_term_variability IS NOT NULL THEN NOW() ELSE mean_value_of_short_term_variability_updated_at END,
            
            percentage_of_time_with_abnormal_long_term_variability = COALESCE(NEW.percentage_of_time_with_abnormal_long_term_variability, percentage_of_time_with_abnormal_long_term_variability),
            percentage_of_time_with_abnormal_long_term_variability_updated_at = CASE WHEN NEW.percentage_of_time_with_abnormal_long_term_variability IS NOT NULL THEN NOW() ELSE percentage_of_time_with_abnormal_long_term_variability_updated_at END,
            
            mean_value_of_long_term_variability = COALESCE(NEW.mean_value_of_long_term_variability, mean_value_of_long_term_variability),
            mean_value_of_long_term_variability_updated_at = CASE WHEN NEW.mean_value_of_long_term_variability IS NOT NULL THEN NOW() ELSE mean_value_of_long_term_variability_updated_at END,
            
            -- Histogram fields
            histogram_width = COALESCE(NEW.histogram_width, histogram_width),
            histogram_width_updated_at = CASE WHEN NEW.histogram_width IS NOT NULL THEN NOW() ELSE histogram_width_updated_at END,
            
            histogram_min = COALESCE(NEW.histogram_min, histogram_min),
            histogram_min_updated_at = CASE WHEN NEW.histogram_min IS NOT NULL THEN NOW() ELSE histogram_min_updated_at END,
            
            histogram_max = COALESCE(NEW.histogram_max, histogram_max),
            histogram_max_updated_at = CASE WHEN NEW.histogram_max IS NOT NULL THEN NOW() ELSE histogram_max_updated_at END,
            
            histogram_number_of_peaks = COALESCE(NEW.histogram_number_of_peaks, histogram_number_of_peaks),
            histogram_number_of_peaks_updated_at = CASE WHEN NEW.histogram_number_of_peaks IS NOT NULL THEN NOW() ELSE histogram_number_of_peaks_updated_at END,
            
            histogram_number_of_zeroes = COALESCE(NEW.histogram_number_of_zeroes, histogram_number_of_zeroes),
            histogram_number_of_zeroes_updated_at = CASE WHEN NEW.histogram_number_of_zeroes IS NOT NULL THEN NOW() ELSE histogram_number_of_zeroes_updated_at END,
            
            histogram_mode = COALESCE(NEW.histogram_mode, histogram_mode),
            histogram_mode_updated_at = CASE WHEN NEW.histogram_mode IS NOT NULL THEN NOW() ELSE histogram_mode_updated_at END,
            
            histogram_mean = COALESCE(NEW.histogram_mean, histogram_mean),
            histogram_mean_updated_at = CASE WHEN NEW.histogram_mean IS NOT NULL THEN NOW() ELSE histogram_mean_updated_at END,
            
            histogram_median = COALESCE(NEW.histogram_median, histogram_median),
            histogram_median_updated_at = CASE WHEN NEW.histogram_median IS NOT NULL THEN NOW() ELSE histogram_median_updated_at END,
            
            histogram_variance = COALESCE(NEW.histogram_variance, histogram_variance),
            histogram_variance_updated_at = CASE WHEN NEW.histogram_variance IS NOT NULL THEN NOW() ELSE histogram_variance_updated_at END,
            
            histogram_tendency = COALESCE(NEW.histogram_tendency, histogram_tendency),
            histogram_tendency_updated_at = CASE WHEN NEW.histogram_tendency IS NOT NULL THEN NOW() ELSE histogram_tendency_updated_at END,
            
            last_updated = NOW()
        WHERE patient_id = v_patient_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate trigger
CREATE TRIGGER fetal_update_latest
AFTER INSERT OR UPDATE ON fetal_health_assessments
FOR EACH ROW
EXECUTE FUNCTION update_patient_latest_assessments();

SELECT 'Fetal trigger updated with all CTG fields' AS status;
