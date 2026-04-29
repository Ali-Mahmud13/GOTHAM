import shap
import numpy as np
import pandas as pd
import joblib

class MaternalHealthXAI:
    def __init__(self, model_path='maternal_health_model.pkl'):
        self.model = joblib.load(model_path)
        # Hardcoded feature names (matches mm-contract.yml input features)
        self.feature_names = ['Age', 'SystolicBP', 'DiastolicBP', 'BS', 'BodyTemp', 'HeartRate']
        self.explainer = shap.TreeExplainer(self.model)
        self.risk_mapping = {0: "Low Risk", 1: "Mid Risk", 2: "High Risk"}

    def predict_risk(self, input_data):
        missing = [f for f in self.feature_names if f not in input_data]
        if missing:
            raise ValueError(f"Missing features: {missing}")
            
        x_input = np.array([input_data[feat] for feat in self.feature_names]).reshape(1, -1)
        pred_class = self.model.predict(x_input)[0]
        pred_label = self.risk_mapping[pred_class]
        probs = self.model.predict_proba(x_input)[0]
        prob_dict = {self.risk_mapping[i]: prob for i, prob in enumerate(probs)}
        return pred_label, prob_dict, x_input

    def get_shap_explanations(self, x_input):
        shap_values = self.explainer.shap_values(x_input)
        expected_value = self.explainer.expected_value

        if isinstance(shap_values, list):
            class_idx = np.argmax(self.model.predict_proba(x_input))
            shap_vals_raw = shap_values[class_idx]
        else:
            shap_vals_raw = shap_values

        # Ensure we get the right dimensions - flatten and take only needed length
        shap_vals_flat = np.array(shap_vals_raw).flatten()[:len(self.feature_names)]
        feature_vals_flat = np.array(x_input).flatten()[:len(self.feature_names)]

        shap_df = pd.DataFrame({
            'feature': self.feature_names,
            'shap_value': shap_vals_flat,
            'feature_value': feature_vals_flat
        }).sort_values('shap_value', key=abs, ascending=False)

        return shap_df, shap_values, expected_value

    def generate_markdown_report(self, input_data, patient_id="Patient_001",
                                 condition_name="Maternal Health Risk Assessment"):
        pred_label, probabilities, x_input = self.predict_risk(input_data)
        shap_df, shap_values, expected_value = self.get_shap_explanations(x_input)

        top_risk_factors = shap_df[shap_df['shap_value'] > 0].head(3)
        protective_factors = shap_df[shap_df['shap_value'] < 0].head(3)

        report = f"""
# *{condition_name} Report*

## 🧍 *Patient Information*
- **Patient ID:** {patient_id}
- **Assessment Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
- **Model Type:** {type(self.model).__name__}

---

## 🎯 *Prediction Summary*
- **Overall Assessment:** **{pred_label}**
- **Risk Category:** *{'HIGH' if pred_label == 'High Risk' else 'MODERATE' if pred_label == 'Mid Risk' else 'LOW'}*
- **Confidence Scores:**
"""
        for risk_level, prob in probabilities.items():
            report += f"\n  - *{risk_level}:* {prob:.1%}"

        report += """

---

## 🧠 *Explainable AI Feature Impact*

| Rank | Feature | Value | SHAP Importance | Impact |
|------|----------|--------|-----------------|---------|"""
        for i, (_, row) in enumerate(shap_df.iterrows(), 1):
            impact = "🔼 Increases Risk" if row['shap_value'] > 0 else "🔽 Decreases Risk" if row['shap_value'] < 0 else "⚖️ Neutral"
            report += f"\n| {i} | *{row['feature']}* | {row['feature_value']} | *{row['shap_value']:+.5f}* | {impact} |"

        report += """

---

## 🔍 *Key Clinical Insights*

### Top Risk Contributors
"""
        if not top_risk_factors.empty:
            for _, row in top_risk_factors.iterrows():
                report += f"- *{row['feature']}* (Value: {row['feature_value']}) — increases overall risk\n"
        else:
            report += "- No major risk contributors identified.\n"

        report += "\n### Protective Factors\n"
        if not protective_factors.empty:
            for _, row in protective_factors.iterrows():
                report += f"- *{row['feature']}* (Value: {row['feature_value']}) — lowers risk\n"
        else:
            report += "- No significant protective factors detected.\n"

        report += """

---

## 🧾 *Interpretation Notes*
- **Importance Score:** Reflects each feature's contribution to the model's prediction.
- **Positive SHAP values:** Push prediction toward *higher risk*.
- **Negative SHAP values:** Push prediction toward *lower risk*.
- **Clinical Use:** This helps clinicians understand *why* the AI made its decision.

> ⚠️ *Disclaimer: This report is AI-generated for clinical decision support. Final judgment should be made by qualified healthcare professionals.*
"""
        return report