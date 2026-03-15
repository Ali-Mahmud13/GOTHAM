"""
Fetal Ultrasound XAI Runner
-----------------------------
Runs the detection + explanation pipeline on an ultrasound image.
"""

from .usxai import FetalUltrasoundXAI
from pathlib import Path
import asyncio


def generate_xai_report(image_path, patient_id="Patient_001", conf_threshold=0.25):
    model_path = str(Path(__file__).parent / "fetal_detection_best.pt")

    xai = FetalUltrasoundXAI(model_path)
    report = xai.generate_markdown_report(image_path, patient_id, conf_threshold)
    return report

async def predict_ultrasound(ultrasound_image_path: str) -> str:
    return await asyncio.to_thread(generate_xai_report, ultrasound_image_path)


if __name__ == "__main__":
    model_path = r"D:\New Downloads\fetal_detection_best.pt"
    image_path = r"D:\Models\ultrasound\test\images\346_HC_png_jpg.rf.e7992084383b0bf580fe51e1dd56d342.jpg"

    report = generate_xai_report(
        model_path=model_path,
        image_path=image_path,
        patient_id="TEST_001",
        conf_threshold=0.25,
    )

    print("=== Fetal Ultrasound XAI Report ===\n")
    print(report)