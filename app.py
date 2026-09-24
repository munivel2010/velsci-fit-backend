from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Velsci Fit Engine Operational"}), 200

@app.route('/process-pattern', methods=['POST'])
def process_pattern():
    try:
        data = request.get_json()
        image_data = data.get('image')
        known_width_mm = float(data.get('known_width_mm', 23.0))
        margin_percent = float(data.get('margin', 10)) / 100.0
        grid_rows = int(data.get('grid_rows', 4))
        grid_cols = int(data.get('grid_cols', 4))

        # Base64 Decode
        encoded_data = image_data.split(',')[1] if ',' in image_data else image_data
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"error": "Invalid image format"}), 400

        h_img, w_img, _ = img.shape

        # 1. Edge Segmentation & Contour Extraction
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 30, 120)

        # Dilate to connect edges
        kernel = np.ones((5,5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return jsonify({"error": "No clear garment contour detected"}), 400

        # Find main garment contour
        garment_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(garment_contour)

        # 2. Precise Scaling Calculation
        pixel_to_mm_ratio = (h / 650.0)
        real_width_cm = round((w / pixel_to_mm_ratio) / 10.0, 1)
        real_height_cm = round((h / pixel_to_mm_ratio) / 10.0, 1)

        total_height_cm = round(real_height_cm * (1 + margin_percent), 1)
        required_meters = round(total_height_cm / 100.0, 2)

        # 3. DRAW PATTERN & PUZZLE OVERLAY
        output_img = img.copy()

        # Draw Neon Green Garment Contour
        cv2.drawContours(output_img, [garment_contour], -1, (0, 255, 0), 4)

        # Draw Red Bounding Box around Garment
        cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 0, 255), 3)

        # Draw Numbered Puzzle Grid
        cell_w = w // grid_cols
        cell_h = h // grid_rows
        piece_num = 1

        for r in range(grid_rows):
            for c in range(grid_cols):
                px = x + c * cell_w
                py = y + r * cell_h
                
                # Draw Cyan Grid Tile
                cv2.rectangle(output_img, (px, py), (px + cell_w, py + cell_h), (255, 255, 0), 2)
                
                # Overlay Yellow Text with Dark Background for Readability
                text = f"P-{piece_num}"
                font_scale = max(0.5, min(w_img, h_img) / 1000.0)
                thickness = 2
                
                # Text Background Box
                (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                cv2.rectangle(output_img, (px + 5, py + 5), (px + 15 + text_w, py + 15 + text_h), (0, 0, 0), -1)
                
                # Text
                cv2.putText(output_img, text, (px + 10, py + 10 + text_h), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), thickness, cv2.LINE_AA)
                piece_num += 1

        # Encode processed image back to JPEG Base64
        _, buffer = cv2.imencode('.jpg', output_img)
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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
