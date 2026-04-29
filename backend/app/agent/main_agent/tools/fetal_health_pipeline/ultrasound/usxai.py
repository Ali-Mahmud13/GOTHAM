"""
Fetal Ultrasound XAI Module
----------------------------
Uses YOLOv8 to detect fetal brain structures and generate explainable outputs.
Produces annotated ultrasound images + structured markdown reports.
"""
import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from ultralytics import YOLO
import requests
from app.core.cloudinary_utils import upload_image_to_cloudinary


class FetalUltrasoundXAI:
    """Explainable AI for Fetal Ultrasound Detection using YOLOv8."""

    def __init__(self, model_path="fetal_detection_best.pt"):
        self.yolo_model = YOLO(model_path)

        self.class_names = [
            "CHOROID_PLEXUS",
            "CSP",
            "MIDLINE_FALX",
        ]

        self.class_descriptions = {
            "CHOROID_PLEXUS": "Fluid-producing tissue in the brain ventricles",
            "CSP": "Cavum Septum Pellucidum — fluid-filled midline cavity",
            "MIDLINE_FALX": "Membrane separating left and right hemispheres",
        }

        self.colors = {
            "CHOROID_PLEXUS": (0.0, 0.8, 0.0),
            "CSP": (1.0, 0.6, 0.0),
            "MIDLINE_FALX": (0.2, 0.4, 1.0),
        }

    # ---------------------------------------------------------
    # Unified Image Loader (Local + URL)
    # ---------------------------------------------------------

    def load_image(self, image_path):
        """Load image from local path or URL."""

        image_path = str(image_path)

        if image_path.startswith("http"):
            response = requests.get(image_path, timeout=10)
            response.raise_for_status()

            image_array = np.frombuffer(response.content, np.uint8)
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        return img

    # ---------------------------------------------------------
    # Detection
    # ---------------------------------------------------------

    def predict(self, image_path, conf_threshold=0.25):
        """Run YOLO detection on ultrasound image."""

        img = self.load_image(image_path)

        results = self.yolo_model.predict(
            source=img,
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

    # ---------------------------------------------------------
    # Visualization
    # ---------------------------------------------------------

    def show_detections(self, image_path, detections, save_path=None):
        """Draw bounding boxes and save annotated image."""

        img = self.load_image(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.imshow(img_rgb)

        legend_handles = []

        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            color = self.colors.get(d["class_name"], (1, 1, 1))
            label = f"{d['class_name']} ({d['confidence']:.0%})"

            rect = patches.Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                linewidth=2.5,
                edgecolor=color,
                facecolor=(*color, 0.15),
            )

            ax.add_patch(rect)

            ax.text(
                x1,
                y1 - 8,
                label,
                fontsize=10,
                fontweight="bold",
                color="white",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor=color,
                    alpha=0.85,
                ),
            )

            legend_handles.append(
                patches.Patch(
                    facecolor=color,
                    edgecolor=color,
                    label=d["class_name"],
                )
            )

        seen = set()
        unique_handles = []

        for h in legend_handles:
            if h.get_label() not in seen:
                unique_handles.append(h)
                seen.add(h.get_label())

        ax.legend(
            handles=unique_handles,
            loc="upper right",
            fontsize=10,
            framealpha=0.9,
            title="Structures",
            title_fontsize=11,
        )

        ax.set_title(
            f"Fetal Ultrasound Detection — {len(detections)} structures found",
            fontsize=13,
            fontweight="bold",
        )

        ax.axis("off")
        plt.tight_layout()

        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches="tight")

        plt.close(fig)

        return save_path

    # ---------------------------------------------------------
    # Markdown Report
    # ---------------------------------------------------------

    def generate_markdown_report(
        self,
        image_path,
        patient_id="Patient_001",
        conf_threshold=0.25,
    ):
        """Generate full explainable ultrasound report."""

        detections, result = self.predict(image_path, conf_threshold)

        local_path = Path(str(image_path)).stem + "_annotated.png"
        self.show_detections(image_path, detections, local_path)
        cloud_url = upload_image_to_cloudinary(local_path)

        structures_found = [d["class_name"] for d in detections]
        all_found = all(cls in structures_found for cls in self.class_names)

        avg_conf = (
            np.mean([d["confidence"] for d in detections])
            if detections else 0
        )

        if all_found and avg_conf > 0.8:
            assessment = "Normal — All structures identified"
            risk = "LOW"
        elif len(structures_found) >= 2:
            assessment = "Partial — Some structures detected"
            risk = "MODERATE"
        else:
            assessment = "Incomplete — Missing structures"
            risk = "HIGH"

        report = f"""
# Fetal Brain Ultrasound Detection Report

## Patient Information
- Patient ID: {patient_id}
- Assessment Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
- Image: {Path(str(image_path)).name}

---

## Detection Summary
- Overall Assessment: {assessment}
- Risk Level: {risk}
- Structures Found: {len(detections)}/3
- Average Confidence: {avg_conf:.1%}

---

## Annotated Detection Image
![Annotated Ultrasound]({cloud_url})

---

## Detected Structures

| # | Structure | Confidence | Bounding Box | Description |
|---|-----------|------------|--------------|-------------|
"""

        if detections:
            for i, d in enumerate(detections, 1):
                x1, y1, x2, y2 = d["bbox"]
                report += f"""
| {i} | {d['class_name']} | {d['confidence']:.1%} | [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}] | {d['description']} |
"""
        else:
            report += """
| - | No structures detected | - | - | - |
"""

        report += """

---

⚠️ Disclaimer: AI output for clinical decision support only.
Final interpretation must be made by qualified healthcare professionals.
"""

        return report