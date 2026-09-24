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
    return jsonify({"status": "Velsci Fit Fast Local Engine Operational"}), 200

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

        # Fast Image Contour Extraction (Lightweight Processing)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive Threshold
        thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            garment_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(garment_contour)
        else:
            x, y, w, h = int(w_img * 0.1), int(h_img * 0.1), int(w_img * 0.8), int(h_img * 0.8)

        # Measurements Calculation
        pixel_to_mm_ratio = (h / 650.0) if h > 0 else 1.0
        real_width_cm = round((w / pixel_to_mm_ratio) / 10.0, 1)
        real_height_cm = round((h / pixel_to_mm_ratio) / 10.0, 1)
        total_height_cm = round(real_height_cm * (1 + margin_percent), 1)
        required_meters = round(total_height_cm / 100.0, 2)

        # Fast Output Drawing
        output_img = img.copy()
        if contours:
            cv2.drawContours(output_img, [garment_contour], -1, (0, 255, 0), 4)
        cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 0, 255), 3)

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

        _, buffer = cv2.imencode('.jpg', output_img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
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
        return jsonify({"error": "Fast Engine Recovery Triggered"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
