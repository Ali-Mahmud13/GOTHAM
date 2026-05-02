"""
Fetal Ultrasound XAI Runner
-----------------------------
Runs the detection + explanation pipeline on an ultrasound image.
"""

from .usxai import FetalUltrasoundXAI
from pathlib import Path
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_xai_report(image_path, patient_id="Patient_001", conf_threshold=0.25):
    model_path = str(Path(__file__).parent / "fetal_detection_best.pt")

    xai = FetalUltrasoundXAI(model_path)
    report = xai.generate_markdown_report(image_path, patient_id, conf_threshold)
    return report


async def predict_ultrasound(latest_ultrasound_image_url: str) -> str:
    """
    Predict fetal ultrasound structures from image.
    
    Args:
        latest_ultrasound_image_url: Path to ultrasound image or None/empty string
        
    Returns:
        Markdown report or warning message if no image available
    """
    
    # ✅ FIX: Handle None, empty string, and whitespace properly
    logger.info(f"predict_ultrasound called with: {repr(latest_ultrasound_image_url)}")
    
    if not latest_ultrasound_image_url:
        logger.info("No ultrasound image provided - skipping ultrasound analysis")
        return "⚠️ **Ultrasound Image Not Available**\nNo ultrasound image found for this patient. Ultrasound analysis skipped."
    
    if isinstance(latest_ultrasound_image_url, str) and latest_ultrasound_image_url.strip() == "":
        logger.info("Empty ultrasound image URL - skipping ultrasound analysis")
        return "⚠️ **Ultrasound Image Not Available**\nNo ultrasound image found for this patient. Ultrasound analysis skipped."
    
    # Check if file exists (only if it looks like a local path)
    if isinstance(latest_ultrasound_image_url, str) and latest_ultrasound_image_url.startswith(('/', 'C:', 'D:', 'E:', '.')):
        if not Path(latest_ultrasound_image_url).exists():
            logger.warning(f"Ultrasound image file not found: {latest_ultrasound_image_url}")
            return f"⚠️ **Ultrasound Image Not Found**\nImage file does not exist: {latest_ultrasound_image_url}"
    
    logger.info(f"Running ultrasound analysis on image: {latest_ultrasound_image_url}")
    try:
        report = await asyncio.to_thread(generate_xai_report, latest_ultrasound_image_url)
        logger.info("✓ Ultrasound analysis completed successfully")
        return report
    except Exception as e:
        logger.error(f"Error during ultrasound analysis: {str(e)}", exc_info=True)
        return f"❌ **Ultrasound Analysis Error**\n{str(e)}"


if __name__ == "__main__":
    model_path = r"D:\New Downloads\fetal_detection_best.pt"
    image_path = r"D:\Models\ultrasound\test\images\346_HC_png_jpg.rf.e7992084383b0bf580fe51e1dd56d342.jpg"

    report = generate_xai_report(
        image_path=image_path,
        patient_id="TEST_001",
        conf_threshold=0.25,
    )

    print("=== Fetal Ultrasound XAI Report ===\n")
    print(report)