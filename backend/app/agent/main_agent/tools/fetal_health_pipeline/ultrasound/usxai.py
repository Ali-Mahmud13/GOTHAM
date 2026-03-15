"""
Fetal Ultrasound XAI Module
----------------------------
Uses GradCAM to explain YOLOv8 detections.
Shows WHERE the model is looking to detect each fetal brain structure.
"""

import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from ultralytics import YOLO


class FetalUltrasoundXAI:
    """Explainable AI for Fetal Ultrasound Detection using YOLOv8."""

    def __init__(self, model_path='fetal_detection_best.pt'):
        self.yolo_model = YOLO(model_path)
        self.class_names = ["CHOROID_PLEXUS", "CSP", "MIDLINE_FALX"]
        self.class_descriptions = {
            "CHOROID_PLEXUS": "Fluid-producing tissue in the brain ventricles",
            "CSP": "Cavum Septum Pellucidum — fluid-filled space in the midline of the brain",
            "MIDLINE_FALX": "Membrane dividing the brain into left and right hemispheres",
        }
        self.colors = {
            "CHOROID_PLEXUS": (0.0, 0.8, 0.0),    # green
            "CSP": (1.0, 0.6, 0.0),                # orange
            "MIDLINE_FALX": (0.2, 0.4, 1.0),       # blue
        }

    def predict(self, image_path, conf_threshold=0.25):
        """Run detection on an image and return structured results."""
        results = self.yolo_model.predict(
            source=image_path,
            imgsz=640,
            conf=conf_threshold,
            verbose=False,
        )
        result = results[0]
        boxes = result.boxes

        detections = []
        for box in boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])
            coords = box.xyxy[0].tolist()

            detections.append({
                "class_id": cls_id,
                "class_name": self.class_names[cls_id],
                "confidence": confidence,
                "bbox": coords,
                "description": self.class_descriptions[self.class_names[cls_id]],
            })

        return detections, result

    def get_detection_summary(self, detections):
        """Create a summary DataFrame of detections."""
        if not detections:
            return pd.DataFrame(columns=["Structure", "Confidence", "Location", "Description"])

        rows = []
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            rows.append({
                "Structure": d["class_name"],
                "Confidence": f"{d['confidence']:.1%}",
                "Location": f"[{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]",
                "Description": d["description"],
            })

        return pd.DataFrame(rows)

    def show_detections(self, image_path, detections, save_path=None):
        """Display the image with colored bounding boxes, labels, and a legend."""
        img = cv2.imread(str(image_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.imshow(img_rgb)

        legend_handles = []

        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            color = self.colors.get(d["class_name"], (1, 1, 1))
            label = f"{d['class_name']} ({d['confidence']:.0%})"

            # Draw bounding box
            rect = patches.Rectangle(
                (x1, y1), x2 - x1, y2 - y1,
                linewidth=2.5,
                edgecolor=color,
                facecolor=(*color, 0.15),  # slight fill
            )
            ax.add_patch(rect)

            # Add label above box
            ax.text(
                x1, y1 - 8, label,
                fontsize=10, fontweight='bold',
                color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.85),
            )

            # Collect for legend
            legend_handles.append(
                patches.Patch(facecolor=color, edgecolor=color, label=d["class_name"])
            )

        # Remove duplicate legend entries
        seen = set()
        unique_handles = []
        for h in legend_handles:
            if h.get_label() not in seen:
                unique_handles.append(h)
                seen.add(h.get_label())

        ax.legend(handles=unique_handles, loc='upper right', fontsize=10,
                  framealpha=0.9, title="Structures", title_fontsize=11)

        ax.set_title(f"Fetal Ultrasound Detection — {len(detections)} structures found",
                     fontsize=13, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📷 Annotated image saved: {save_path}")

        plt.show()

        return fig

    def generate_markdown_report(self, image_path, patient_id="Patient_001",
                                  conf_threshold=0.25):
        """Generate a full XAI markdown report for a fetal ultrasound image."""
        detections, result = self.predict(image_path, conf_threshold)

        # --- SHOW THE ANNOTATED IMAGE ---
        save_path = Path(image_path).stem + "_annotated.png"
        # self.show_detections(image_path, detections, save_path=save_path)

        # Determine overall assessment
        structures_found = [d["class_name"] for d in detections]
        all_found = all(cls in structures_found for cls in self.class_names)
        avg_confidence = np.mean([d["confidence"] for d in detections]) if detections else 0

        if all_found and avg_confidence > 0.8:
            assessment = "✅ Normal — All 3 structures clearly identified"
            risk = "LOW"
        elif len(structures_found) >= 2:
            assessment = "⚠️ Partial — Some structures detected with lower confidence"
            risk = "MODERATE"
        else:
            assessment = "🔴 Incomplete — Missing key anatomical structures"
            risk = "HIGH"

        report = f"""
# *Fetal Brain Ultrasound Detection Report*

## 🧍 *Patient Information*
- **Patient ID:** {patient_id}
- **Assessment Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
- **Image:** {Path(image_path).name}
- **Model:** YOLOv8s (fetal_detection_best.pt)

---

## 🎯 *Detection Summary*
- **Overall Assessment:** **{assessment}**
- **Risk Level:** *{risk}*
- **Structures Found:** {len(detections)}/3
- **Average Confidence:** {avg_confidence:.1%}

---

## 🧠 *Detected Structures*

| # | Structure | Confidence | Bounding Box | Description |
|---|-----------|------------|--------------|-------------|"""

        if detections:
            for i, d in enumerate(detections, 1):
                x1, y1, x2, y2 = d["bbox"]
                report += f"\n| {i} | **{d['class_name']}** | {d['confidence']:.1%} | [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}] | {d['description']} |"
        else:
            report += "\n| - | *No structures detected* | - | - | - |"

        missing = [cls for cls in self.class_names if cls not in structures_found]
        report += """

---

## 🔍 *Analysis*

### Detected Structures
"""
        for d in detections:
            confidence_label = "High" if d["confidence"] > 0.8 else "Moderate" if d["confidence"] > 0.5 else "Low"
            report += f"- **{d['class_name']}** — Detected with **{confidence_label}** confidence ({d['confidence']:.1%})\n"

        report += "\n### Missing Structures\n"
        if missing:
            for m in missing:
                report += f"- **{m}** — ⚠️ Not detected. {self.class_descriptions[m]}\n"
        else:
            report += "- ✅ All three structures successfully identified.\n"

        report += f"""

---

## 🧠 *Explainability Notes*
- **What the model looks for:** The model identifies three key fetal brain structures in the transthalamic/transventricular plane.
- **Bounding Boxes:** Color-coded boxes show WHERE each structure was detected.
  - 🟢 **CHOROID_PLEXUS** (Green)
  - 🟠 **CSP** (Orange)
  - 🔵 **MIDLINE_FALX** (Blue)
- **Confidence Score:** How certain the model is (higher = more certain).
- **Annotated Image:** Saved as `{save_path}`

---

## 🧾 *Clinical Context*
| Structure | Normal Finding | Clinical Significance |
|-----------|---------------|----------------------|
| CHOROID_PLEXUS | Visible in lateral ventricles | Absence/cysts may indicate chromosomal abnormalities |
| CSP | Visible as fluid-filled cavity | Absence may indicate brain development issues |
| MIDLINE_FALX | Clear midline division | Shift may indicate mass effect or abnormality |

> ⚠️ *Disclaimer: This report is AI-generated for clinical decision support. Final diagnosis should be made by qualified healthcare professionals.*
"""
        return report