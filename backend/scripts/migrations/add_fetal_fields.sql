-- Add missing fetal health fields to patient_latest_assessments

ALTER TABLE patient_latest_assessments
-- Already have: fetal_baseline_value, fetal_accelerations, fetal_movement

-- Add missing CTG fields
ADD COLUMN IF NOT EXISTS uterine_contractions DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS uterine_contractions_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS light_decelerations DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS light_decelerations_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS severe_decelerations DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS severe_decelerations_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS prolongued_decelerations DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS prolongued_decelerations_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS abnormal_short_term_variability DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS abnormal_short_term_variability_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS mean_value_of_short_term_variability DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS mean_value_of_short_term_variability_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS percentage_of_time_with_abnormal_long_term_variability DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS percentage_of_time_with_abnormal_long_term_variability_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS mean_value_of_long_term_variability DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS mean_value_of_long_term_variability_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_width DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS histogram_width_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_min DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS histogram_min_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_max DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS histogram_max_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_number_of_peaks INTEGER,
ADD COLUMN IF NOT EXISTS histogram_number_of_peaks_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_number_of_zeroes INTEGER,
ADD COLUMN IF NOT EXISTS histogram_number_of_zeroes_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_mode DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS histogram_mode_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_mean DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS histogram_mean_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_median DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS histogram_median_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_variance DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS histogram_variance_updated_at TIMESTAMP,

ADD COLUMN IF NOT EXISTS histogram_tendency INTEGER,
ADD COLUMN IF NOT EXISTS histogram_tendency_updated_at TIMESTAMP;

SELECT 'Added all fetal health CTG fields' AS status;
