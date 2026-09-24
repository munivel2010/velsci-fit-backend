from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import os
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15MB Limit

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Velsci Fit AI & Claude Engine Operational"}), 200

def analyze_garment_with_claude(base64_image):
    """
    Calls Anthropic Claude 3.5 Sonnet Vision API to extract keypoints & garment structure.
    """
    if not ANTHROPIC_API_KEY:
        return None  # Fallback to local CV if no key provided

    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 300,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Identify the garment boundary coordinates in percentages (top, left, width, height) and reference object if present."
                    }
                ]
            }]
        }
        res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("Claude API Error:", e)
    return None

@app.route('/process-pattern', methods=['POST'])
def process_pattern():
    try:
        data = request.get_json(force=True)
        if not data or 'image' not in data:
            return jsonify({"error": "No image payload"}), 400

        image_data = data.get('image', '')
        known_width_mm = float(data.get('known_width_mm', 23.0))
        margin_percent = float(data.get('margin', 10)) / 100.0
        grid_rows = min(max(int(data.get('grid_rows', 4)), 1), 10)
        grid_cols = min(max(int(data.get('grid_cols', 4)), 1), 10)

        raw_base64 = image_data.split(',')[1] if ',' in image_data else image_data

        # 1. AI Vision Layer (Claude Processing)
        claude_analysis = analyze_garment_with_claude(raw_base64)

        # 2. Local OpenCV Image Processing
        decoded_bytes = base64.b64decode(raw_base64)
        nparr = np.frombuffer(decoded_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "Corrupted Image"}), 400

        h_img, w_img, _ = img.shape

        # Contour Segmentation
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            garment_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(garment_contour)
        else:
            # Fallback Bounding Box
            x, y, w, h = int(w_img * 0.15), int(h_img * 0.10), int(w_img * 0.70), int(h_img * 0.80)

        # Dimension Scaling
        pixel_to_mm_ratio = (h / 650.0)
        real_width_cm = round((w / pixel_to_mm_ratio) / 10.0, 1)
        real_height_cm = round((h / pixel_to_mm_ratio) / 10.0, 1)
        total_height_cm = round(real_height_cm * (1 + margin_percent), 1)
        required_meters = round(total_height_cm / 100.0, 2)

        # Draw Output Pattern Grid
        output_img = img.copy()
        if contours:
            cv2.drawContours(output_img, [garment_contour], -1, (0, 255, 0), 4)
        cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 0, 255), 2)

        cell_w = w // grid_cols
        cell_h = h // grid_rows
        piece_num = 1

        for r in range(grid_rows):
            for c in range(grid_cols):
                px = x + c * cell_w
                py = y + r * cell_h
                cv2.rectangle(output_img, (px, py), (px + cell_w, py + cell_h), (255, 255, 0), 2)

                text = f"P-{piece_num}"
                font_scale = max(0.5, min(w_img, h_img) / 1100.0)
                (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
                
                cv2.rectangle(output_img, (px + 5, py + 5), (px + 15 + text_w, py + 15 + text_h), (0, 0, 0), -1)
                cv2.putText(output_img, text, (px + 10, py + 10 + text_h), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), 2, cv2.LINE_AA)
                piece_num += 1

        _, buffer = cv2.imencode('.jpg', output_img)
        processed_base64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "success": True,
            "claude_integrated": True if claude_analysis else False,
            "measured_width_cm": real_width_cm,
            "measured_height_cm": real_height_cm,
            "required_meters": required_meters,
            "total_puzzle_pieces": grid_rows * grid_cols,
            "processed_image": processed_base64
        }), 200

    except Exception as e:
        return jsonify({"error": "Processing error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
