from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Velsci Fit Precision Engine Operational"}), 200

@app.route('/process-pattern', methods=['POST'])
def process_pattern():
    try:
        data = request.get_json(force=True)
        if not data or 'image' not in data:
            return jsonify({"error": "No image payload"}), 400

        image_data = data.get('image', '')
        margin_percent = float(data.get('margin', 10)) / 100.0
        grid_rows = min(max(int(data.get('grid_rows', 4)), 1), 10)
        grid_cols = min(max(int(data.get('grid_cols', 4)), 1), 10)

        raw_base64 = image_data.split(',')[1] if ',' in image_data else image_data
        decoded_bytes = base64.b64decode(raw_base64)
        nparr = np.frombuffer(decoded_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "Corrupted Image File"}), 400

        h_img, w_img, _ = img.shape

        # 1. Focus ROI on Central Region to eliminate outer table noise/bottom furniture
        roi_y1, roi_y2 = int(h_img * 0.15), int(h_img * 0.85)
        roi_x1, roi_x2 = int(w_img * 0.10), int(w_img * 0.90)
        roi = img[roi_y1:roi_y2, roi_x1:roi_x2]

        # 2. Advanced HSV Color & Contrast Masking
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Blur & Threshold to ignore floral/leaf background
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3)

        # Morphology to remove thin lines (leaf patterns)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            rx, ry, rw, rh = cv2.boundingRect(c)
            # Map back to full image coordinates
            x, y, w, h = rx + roi_x1, ry + roi_y1, rw, rh
            garment_contour = c + np.array([roi_x1, roi_y1])
        else:
            # Safe Default Box around the t-shirt
            x, y, w, h = int(w_img * 0.15), int(h_img * 0.20), int(w_img * 0.70), int(h_img * 0.65)
            garment_contour = None

        # Scaling & Measurements
        pixel_to_mm_ratio = (h / 650.0) if h > 0 else 1.0
        real_width_cm = round((w / pixel_to_mm_ratio) / 10.0, 1)
        real_height_cm = round((h / pixel_to_mm_ratio) / 10.0, 1)
        total_height_cm = round(real_height_cm * (1 + margin_percent), 1)
        required_meters = round(total_height_cm / 100.0, 2)

        # Draw Output
        output_img = img.copy()
        if garment_contour is not None:
            cv2.drawContours(output_img, [garment_contour], -1, (0, 255, 0), 3)
        
        # Red Box over exact Garment Area
        cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 0, 255), 3)

        # Draw Puzzle Grid inside the T-Shirt Box
        cell_w = max(w // grid_cols, 1)
        cell_h = max(h // grid_rows, 1)
        piece_num = 1

        for r in range(grid_rows):
            for c in range(grid_cols):
                px = x + c * cell_w
                py = y + r * cell_h
                cv2.rectangle(output_img, (px, py), (px + cell_w, py + cell_h), (255, 255, 0), 2)

                text = f"P-{piece_num}"
                cv2.putText(output_img, text, (px + 10, py + 25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
                piece_num += 1

        _, buffer = cv2.imencode('.jpg', output_img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        processed_base64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "success": True,
            "measured_width_cm": real_width_cm,
            "measured_height_cm": real_height_cm,
            "required_meters": required_meters,
            "total_puzzle_pieces": grid_rows * grid_cols,
            "processed_image": processed_base64
        }), 200

    except Exception as e:
        return jsonify({"error": "Error in pattern bounding"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
