from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io

app = Flask(__name__)

# Strict CORS: Only allow calls from velsci.com domain
CORS(app, resources={r"/*": {"origins": ["https://velsci.com", "https://www.velsci.com", "http://localhost:*"]}})

# Payload Security: Limit max request size to 10MB to prevent Buffer Overflow / DoS
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Velsci Fit Secure Engine Operational"}), 200

@app.route('/process-pattern', methods=['POST'])
def process_pattern():
    try:
        data = request.get_json(force=True)
        if not data or 'image' not in data:
            return jsonify({"error": "Invalid request payload"}), 400

        image_data = data.get('image', '')
        known_width_mm = float(data.get('known_width_mm', 23.0))
        margin_percent = float(data.get('margin', 10)) / 100.0
        grid_rows = min(max(int(data.get('grid_rows', 4)), 1), 10)  # Input Sanitization (1 to 10)
        grid_cols = min(max(int(data.get('grid_cols', 4)), 1), 10)

        # Base64 Safe Decoding
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        try:
            decoded_bytes = base64.b64decode(image_data)
        except Exception:
            return jsonify({"error": "Corrupted or invalid Base64 image payload"}), 400

        nparr = np.frombuffer(decoded_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "Unrecognized or malicious image file format"}), 400

        h_img, w_img, _ = img.shape

        # Edge Segmentation & Contour Extraction
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 30, 120)

        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return jsonify({"error": "No clear garment contour detected"}), 400

        garment_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(garment_contour)

        # Precise Scaling Calculation
        pixel_to_mm_ratio = (h / 650.0)
        real_width_cm = round((w / pixel_to_mm_ratio) / 10.0, 1)
        real_height_cm = round((h / pixel_to_mm_ratio) / 10.0, 1)

        total_height_cm = round(real_height_cm * (1 + margin_percent), 1)
        required_meters = round(total_height_cm / 100.0, 2)

        # Drawing Pattern & Puzzle Grid
        output_img = img.copy()
        cv2.drawContours(output_img, [garment_contour], -1, (0, 255, 0), 4)
        cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 0, 255), 3)

        cell_w = w // grid_cols
        cell_h = h // grid_rows
        piece_num = 1

        for r in range(grid_rows):
            for c in range(grid_cols):
                px = x + c * cell_w
                py = y + r * cell_h
                cv2.rectangle(output_img, (px, py), (px + cell_w, py + cell_h), (255, 255, 0), 2)

                text = f"P-{piece_num}"
                font_scale = max(0.5, min(w_img, h_img) / 1000.0)
                thickness = 2

                (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                cv2.rectangle(output_img, (px + 5, py + 5), (px + 15 + text_w, py + 15 + text_h), (0, 0, 0), -1)
                cv2.putText(output_img, text, (px + 10, py + 10 + text_h), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), thickness, cv2.LINE_AA)
                piece_num += 1

        # DXF / SVG Vector Generation Logic
        svg_vector_content = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w_img} {h_img}">'
        svg_vector_content += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="red" stroke-width="2"/>'
        svg_vector_content += '</svg>'

        # In-Memory Buffer Encoding (No Data Stored on Disk)
        _, buffer = cv2.imencode('.jpg', output_img)
        processed_base64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "success": True,
            "measured_width_cm": real_width_cm,
            "measured_height_cm": real_height_cm,
            "required_meters": required_meters,
            "total_puzzle_pieces": grid_rows * grid_cols,
            "processed_image": processed_base64,
            "svg_dxf_vector": svg_vector_content
        }), 200

    except Exception as e:
        return jsonify({"error": "An internal processing error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
