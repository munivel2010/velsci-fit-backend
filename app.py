from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
import math

app = FastAPI(
    title="Velsci Open-Source Parametric Pattern Engine API",
    version="3.1.0",
    description="100% open-source hybrid pattern engine combining OpenCV computer vision style extraction with parametric measurement inputs."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def analyze_garment_open_source(image_bytes: bytes) -> dict:
    """Uses 100% open-source OpenCV computer vision to analyze garment photos and extract geometric style features."""
    if not image_bytes:
        return {"ease_modifier": 1.0, "notes": "Standard parametric generation active."}
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {"ease_modifier": 1.0, "notes": "Image decode error."}

        # Convert to grayscale and find contours / edges
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ease_mod = 1.0
        aspect_ratio = 2.0
        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = h / float(w) if w > 0 else 2.0
            if aspect_ratio > 2.5:
                ease_mod = 1.05  # Relaxed fit adjustment

        return {
            "ease_modifier": ease_mod,
            "notes": f"OpenCV Vision Analyzed: Aspect Ratio {aspect_ratio:.2f} | Fit modifier applied."
        }
    except Exception as e:
        return {"ease_modifier": 1.0, "notes": f"CV fallback active: {str(e)}"}

def process_parametric_pattern(
    image_bytes: bytes = None,
    chest_cm: float = 92.0,
    waist_cm: float = 76.0,
    hips_cm: float = 98.0,
    shoulder_cm: float = 40.0,
    sleeve_cm: float = 22.0,
    length_cm: float = 68.0,
    stretch_ratio: float = 0.10,
    seam_cm: float = 1.5,
    grid_rows: int = 3,
    grid_cols: int = 2
):
    cv_insights = analyze_garment_open_source(image_bytes)
    ease_mod = cv_insights.get("ease_modifier", 1.0)

    adj_chest = (chest_cm * ease_mod) * (1.0 - stretch_ratio)
    adj_waist = (waist_cm * ease_mod) * (1.0 - stretch_ratio)
    adj_hips = (hips_cm * ease_mod) * (1.0 - stretch_ratio)

    scale = 5.0
    margin_px = int(seam_cm * scale * 2)
    canvas_w = int((shoulder_cm + 20) * scale) + (margin_px * 2)
    canvas_h = int((length_cm + 15) * scale) + (margin_px * 2)

    canvas = np.ones((canvas_h, canvas_w), dtype=np.uint8) * 255

    start_x = canvas_w // 2
    top_y = margin_px + 20
    half_shoulder = int((shoulder_cm * scale) / 2)
    half_chest = int((adj_chest * scale) / 4)
    half_waist = int((adj_waist * scale) / 4)
    garment_len = int(length_cm * scale)

    pts = np.array([
        [start_x - 25, top_y],
        [start_x - half_shoulder, top_y + 15],
        [start_x - half_chest, top_y + 90],
        [start_x - half_waist, top_y + 180],
        [start_x - half_waist, top_y + garment_len],
        [start_x + half_waist, top_y + garment_len],
        [start_x + half_waist, top_y + 180],
        [start_x + half_chest, top_y + 90],
        [start_x + half_shoulder, top_y + 15],
        [start_x + 25, top_y]
    ], np.int32)

    cv2.ellipse(canvas, (start_x, top_y), (25, 20), 0, 0, 180, (0), 2)
    cv2.polylines(canvas, [pts], isClosed=False, color=(0), thickness=2)

    seam_offset_px = int(seam_cm * scale)
    seam_pts = pts.copy()
    seam_pts[:5, 0] -= seam_offset_px
    seam_pts[5:, 0] += seam_offset_px
    seam_pts[0:2, 1] -= seam_offset_px
    seam_pts[4:6, 1] += seam_offset_px

    cv2.polylines(canvas, [seam_pts], isClosed=False, color=(120), thickness=1, lineType=cv2.LINE_AA)

    if image_bytes:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            photo_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if photo_img is not None:
                gray_photo = cv2.cvtColor(photo_img, cv2.COLOR_BGR2GRAY)
                blurred = cv2.bilateralFilter(gray_photo, 9, 75, 75)
                edges = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                resized_edges = cv2.resize(edges, (canvas_w // 3, canvas_h // 3))
                canvas[10:10+(canvas_h // 3), 10:10+(canvas_w // 3)] = cv2.bitwise_and(
                    canvas[10:10+(canvas_h // 3), 10:10+(canvas_w // 3)], resized_edges
                )
        except Exception:
            pass

    tile_h, tile_w = canvas_h // grid_rows, canvas_w // grid_cols
    puzzle_tiles = []

    for r in range(grid_rows):
        for c in range(grid_cols):
            y1, y2 = r * tile_h, (r + 1) * tile_h
            x1, x2 = c * tile_w, (c + 1) * tile_w
            tile = canvas[y1:y2, x1:x2].copy()

            csz = 12
            cv2.line(tile, (5, csz), (5 + csz, csz), (150), 1)
            cv2.line(tile, (csz, 5), (csz, 5 + csz), (150), 1)

            tag = f"Tile [{r+1},{c+1}] | Chest: {chest_cm}cm"
            cv2.putText(tile, tag, (10, tile_h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100), 1)

            _, buf = cv2.imencode('.png', tile)
            tile_b64 = base64.b64encode(buf).decode('utf-8')
            puzzle_tiles.append({
                "tile_id": f"R{r+1}-C{c+1}",
                "data": f"data:image/png;base64,{tile_b64}"
            })

    _, master_buf = cv2.imencode('.png', canvas)
    master_b64 = base64.b64encode(master_buf).decode('utf-8')

    return f"data:image/png;base64,{master_b64}", puzzle_tiles, cv_insights.get("notes")


@app.get("/")
def api_status():
    return {
        "service": "Velsci Open-Source Parametric Pattern Engine",
        "status": "Online",
        "version": "v3.1.0",
        "notice": "Using 100% Open-Source OpenCV Computer Vision."
    }


@app.post("/generate-pattern/")
async def generate_pattern_endpoint(
    file: UploadFile = File(None),
    chest_cm: float = Form(92.0),
    waist_cm: float = Form(76.0),
    hips_cm: float = Form(98.0),
    shoulder_cm: float = Form(40.0),
    sleeve_cm: float = Form(22.0),
    length_cm: float = Form(68.0),
    stretch_ratio: float = Form(0.10),
    seam_allowance_cm: float = Form(1.5)
):
    try:
        image_bytes = await file.read() if file else None
        master_img, tiles, dynamic_notice = process_parametric_pattern(
            image_bytes=image_bytes,
            chest_cm=chest_cm,
            waist_cm=waist_cm,
            hips_cm=hips_cm,
            shoulder_cm=shoulder_cm,
            sleeve_cm=sleeve_cm,
            length_cm=length_cm,
            stretch_ratio=stretch_ratio,
            seam_cm=seam_allowance_cm
        )

        return {
            "status": "success",
            "version": "v3.1-opensource",
            "notice": dynamic_notice,
            "master_pattern": master_img,
            "puzzle_tiles": tiles
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
