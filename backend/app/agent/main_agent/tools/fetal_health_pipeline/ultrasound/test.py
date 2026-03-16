import os
from us import generate_xai_report

if __name__ == "__main__":
    image_path = "https://res.cloudinary.com/dnztftils/image/upload/v1773519159/gotham/patient_P012/visit_292/stream_rdgy89.jpg"
    report = generate_xai_report(image_path)
    print(report)