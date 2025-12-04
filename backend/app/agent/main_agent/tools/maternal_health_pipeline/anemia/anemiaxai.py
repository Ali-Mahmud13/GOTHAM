import shap
import numpy as np
import pandas as pd
import joblib

class AnemiaXAI:
    def __init__(self, model_path='D:/Models/Anemia/catboost_ovr_model.pkl',
                 label_encoder_path='D:/Models/Anemia/label_encoder.pkl'):
        self.model = joblib.load(model_path)
        self.le = joblib.load(label_encoder_path)
        self.feature_names = ['WBC', 'RBC', 'HGB', 'HCT', 'MCV', 'MCH', 'MCHC', 'PLT']
        self.cat_models = self.model.estimators_
        self.explainers = [shap.TreeExplainer(m) for m in self.cat_models]
        self.risk_mapping = dict(zip(range(len(self.le.classes_)), self.le.classes_))

    def predict_anemia(self, input_data):
        missing = [f for f in self.feature_names if f not in input_data]
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        x_input = np.array([input_data[f] for f in self.feature_names]).reshape(1, -1)
        pred_class = self.model.predict(x_input)[0]
        pred_label = self.risk_mapping[pred_class]
        probs = self.model.predict_proba(x_input)[0]
        prob_dict = {self.risk_mapping[i]: prob for i, prob in enumerate(probs)}
        return pred_label, prob_dict, x_input

    def get_shap_explanation(self, x_input):
        class_idx = np.argmax(self.model.predict_proba(x_input))
        shap_vals = self.explainers[class_idx].shap_values(x_input)[0]  # [0] for positive class SHAP

        shap_df = pd.DataFrame({
            'feature': self.feature_names,
            'shap_value': shap_vals,
            'feature_value': [x_input[0][i] for i in range(len(self.feature_names))]
        }).sort_values('shap_value', key=abs, ascending=False)

        return shap_df, class_idx

    def generate_markdown_report(self, input_data):
        pred_label, probabilities, x_input = self.predict_anemia(input_data)
        shap_df, _ = self.get_shap_explanation(x_input)

        md = []
        md.append(f"# Anemia Diagnosis Prediction Report")
        md.append("\n---\n")

        md.append("## Prediction Summary")
        md.append(f"- **Predicted Diagnosis:** **{pred_label.upper()}**")
        md.append(f"- **Overall Assessment:** {pred_label}")
        md.append("\n---\n")

        md.append("## Confidence Scores")
        for diag, prob in probabilities.items():
            md.append(f"- **{diag}:** {prob:.1%}")
        md.append("\n---\n")

        md.append("## Explainable AI Analysis")
        md.append("Top features ranked by impact on this prediction:\n")
        md.append("| Rank | Feature | Value | SHAP Importance |")
        md.append("|------|----------|--------|-----------------|")

        for i, (_, row) in enumerate(shap_df.iterrows(), 1):
            md.append(f"| {i} | {row['feature']} | {row['feature_value']} | {row['shap_value']:+.6f} |")

        md.append("\n---\n")

        md.append("## Key Clinical Insights")
        top_features = shap_df.head(3)
        md.append(f"**Top 3 factors driving the `{pred_label}` prediction:**")
        for i, (_, row) in enumerate(top_features.iterrows(), 1):
            direction = "↑ increased" if row['shap_value'] > 0 else "↓ decreased"
            md.append(f"{i}. **{row['feature']}** = {row['feature_value']} ({direction} risk)")
        md.append("\n---\n")

        md.append("## Interpretation Notes")
        md.append("- Positive SHAP values **increase** probability of the predicted diagnosis")
        md.append("- Negative SHAP values **decrease** probability")
        md.append("- Larger absolute values mean **stronger influence**")
        md.append("\n---\n")

        return "\n".join(md)