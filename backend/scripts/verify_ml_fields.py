"""
Check if materialized table has all required fields for ML models.
"""

# GDM Model Required Fields (from typical GDM risk models)
gdm_required = [
    'glucose_level', 'blood_pressure_systolic', 'blood_pressure_diastolic',
    'bmi', 'ogtt', 'hdl', 'gestation_weeks', 'sedentary_lifestyle',
    'age', 'family_history', 'pcos', 'number_of_pregnancies'
]

# Anemia Model Required Fields (CBC parameters)
anemia_required = [
    'wbc', 'rbc', 'hgb', 'hct', 'mcv', 'mch', 'mchc', 'plt'
]

# Fetal Health Model Required Fields (CTG parameters)
fetal_required = [
    'baseline_value', 'accelerations', 'fetal_movement',
    'uterine_contractions', 'light_decelerations', 'severe_decelerations',
    'prolongued_decelerations', 'abnormal_short_term_variability',
    'mean_value_of_short_term_variability',
    'percentage_of_time_with_abnormal_long_term_variability',
    'mean_value_of_long_term_variability', 'histogram_width',
    'histogram_min', 'histogram_max', 'histogram_number_of_peaks',
    'histogram_number_of_zeroes', 'histogram_mode', 'histogram_mean',
    'histogram_median', 'histogram_variance', 'histogram_tendency'
]

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def check_ml_model_fields():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    # Get all column names from materialized table
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'patient_latest_assessments'
          AND column_name NOT LIKE '%_updated_at'
          AND column_name != 'patient_id'
          AND column_name != 'last_updated'
    """)
    
    available_fields = set(row[0] for row in cursor.fetchall())
    
    print("="*70)
    print("ML MODEL FIELD VERIFICATION")
    print("="*70)
    
    # Check GDM fields
    print("\n🏥 GDM MODEL FIELDS:")
    gdm_mat_fields = {'glucose_level', 'sys_bp', 'dia_bp', 'bmi', 'ogtt', 
                      'hdl', 'gestation_weeks', 'sedentary_lifestyle', 'insulin_level'}
    missing_gdm = gdm_mat_fields - available_fields
    
    if missing_gdm:
        print(f"  ❌ MISSING: {missing_gdm}")
    else:
        print(f"  ✅ All GDM assessment fields present ({len(gdm_mat_fields)} fields)")
    
    print(f"  📋 Available: {sorted(gdm_mat_fields & available_fields)}")
    
    # Check Anemia fields
    print("\n🩸 ANEMIA MODEL FIELDS:")
    anemia_mat_fields = {'wbc', 'rbc', 'hgb', 'hct', 'mcv', 'mch', 'mchc', 'plt'}
    missing_anemia = anemia_mat_fields - available_fields
    
    if missing_anemia:
        print(f"  ❌ MISSING: {missing_anemia}")
    else:
        print(f"  ✅ All CBC fields present ({len(anemia_mat_fields)} fields)")
    
    print(f"  📋 Available: {sorted(anemia_mat_fields & available_fields)}")
    
    # Check Fetal fields
    print("\n👶 FETAL HEALTH MODEL FIELDS:")
    fetal_mat_fields = {
        'fetal_baseline_value', 'fetal_accelerations', 'fetal_movement',
        'uterine_contractions', 'light_decelerations', 'severe_decelerations',
        'prolongued_decelerations', 'abnormal_short_term_variability',
        'mean_value_of_short_term_variability',
        'percentage_of_time_with_abnormal_long_term_variability',
        'mean_value_of_long_term_variability', 'histogram_width',
        'histogram_min', 'histogram_max', 'histogram_number_of_peaks',
        'histogram_number_of_zeroes', 'histogram_mode', 'histogram_mean',
        'histogram_median', 'histogram_variance', 'histogram_tendency'
    }
    missing_fetal = fetal_mat_fields - available_fields
    
    if missing_fetal:
        print(f"  ❌ MISSING: {missing_fetal}")
    else:
        print(f"  ✅ All CTG fields present ({len(fetal_mat_fields)} fields)")
    
    # Sample a few
    sample = sorted(list(fetal_mat_fields & available_fields))[:5]
    print(f"  📋 Sample fields: {sample}...")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY:")
    print("="*70)
    total_missing = len(missing_gdm) + len(missing_anemia) + len(missing_fetal)
    
    if total_missing == 0:
        print("✅ ALL ML MODEL FIELDS PRESENT IN MATERIALIZED TABLE!")
        print(f"   - GDM: {len(gdm_mat_fields)} fields")
        print(f"   - Anemia: {len(anemia_mat_fields)} fields")
        print(f"   - Fetal: {len(fetal_mat_fields)} fields")
    else:
        print(f"❌ {total_missing} MISSING FIELDS FOUND")
        if missing_gdm:
            print(f"   - GDM: {missing_gdm}")
        if missing_anemia:
            print(f"   - Anemia: {missing_anemia}")
        if missing_fetal:
            print(f"   - Fetal: {missing_fetal}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_ml_model_fields()
