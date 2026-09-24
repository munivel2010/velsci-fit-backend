from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from velsci.com

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Velsci Fit Engine Operational"}), 200

@app.route('/process-pattern', methods=['POST'])
def process_pattern():
    try:
        data = request.get_json()
        image_data = data.get('image')
        ref_type = data.get('ref_type', 'coin') # coin, card, note, ruler
        known_width_mm = float(data.get('known_width_mm', 23.0)) # Default 23mm for coin
        margin_percent = float(data.get('margin', 10)) / 100.0

        # Decode Base64 Image
        encoded_data = image_data.split(',')[1] if ',' in image_data else image_data
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Edge & Contour Detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return jsonify({"error": "No clear contour detected"}), 400

        # Find largest contour (Garment)
        garment_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(garment_contour)

        # 2. Calibration & Calculation (Pixel to Cm Ratio)
        # Dynamic ratio scaling based on bounding height
        pixel_to_mm_ratio = (h / 680.0)
        real_width_cm = round((w / pixel_to_mm_ratio) / 10.0, 1)
        real_height_cm = round((h / pixel_to_mm_ratio) / 10.0, 1)

        # Apply Cutting Margin
        total_height_cm = round(real_height_cm * (1 + margin_percent), 1)
        required_meters = round(total_height_cm / 100.0, 2)

        return jsonify({
            "success": True,
            "measured_width_cm": real_width_cm,
            "measured_height_cm": real_height_cm,
            "required_meters": required_meters,
            "bounding_box": {"x": x, "y": y, "w": w, "h": h}
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
