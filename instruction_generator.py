from PIL import Image, ImageDraw, ImageFont
import os

def generate_sewing_instruction_sheet(garment_type="Pants", size_label="L", height=172, waist=82, hips=98):
    # Create a high-resolution sheet layout (A4 / Letter proportions)
    width, height_px = 2480, 3508  # 300 DPI layout
    sheet = Image.new("RGB", (width, height_px), "#FFFFFF")
    draw = ImageDraw.Draw(sheet)
    
    # Try loading standard font or fallback to default
    try:
        font_title = ImageFont.truetype("usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_header = ImageFont.truetype("usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_body = ImageFont.truetype("usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except:
        font_title = font_header = font_body = ImageFont.load_default()

    # Draw Header Branding
    draw.rectangle([100, 100, width - 100, 280], outline="#0a231b", width=4)
    draw.text((140, 145), f"VELSCI FIT — PROFESSIONAL SEWING & FITTING GUIDE", fill="#0a231b", font=font_title)
    draw.text((140, 220), f"Garment: {garment_type} | Size: {size_label} | Height: {height}cm | Waist: {waist}cm | Hips: {hips}cm", fill="#2d735d", font=font_header)

    # Panel 1: Grainline & Layout Rules (Similar to Butterick layout guides)
    draw.rectangle([100, 340, 1180, 1200], outline="#94a3b8", width=2)
    draw.text((140, 380), "1. FABRIC LAYOUT & GRAINLINE RULES", fill="#0a231b", font=font_header)
    
    layout_instructions = [
        "• GRAINLINE: Place arrow parallel to the selvage edge of the fabric.",
        "• SINGLE THICKNESS: Place fabric right side up. (For directional prints, face down).",
        "• DOUBLE THICKNESS: Fold fabric right sides together (selvage to selvage).",
        "• WITH FOLD: Place exact edge aligned along the fold line. Never cut on this line."
    ]
    y_offset = 450
    for instruction in layout_instructions:
        draw.text((140, y_offset), instruction, fill="#334155", font=font_body)
        y_offset += 60

    # Panel 2: Crotch Depth & Fit Adjustments (Fitting Method)
    draw.rectangle([1220, 340, width - 100, 1200], outline="#94a3b8", width=2)
    draw.text((1260, 380), "2. FITTING & CROTCH ADJUSTMENTS", fill="#0a231b", font=font_header)
    
    fitting_tips = [
        "• CROTCH DEPTH: Goal is 1-2cm ease below body. If tight, add tissue to lengthen.",
        "• CROTCH WRINKLES: Horizontal lines indicate a tight inner thigh or flat derriere.",
        "• BAGGY BACK: If fabric droops in back, pin out excess at center back waist.",
        "• FLAT DERRIERERE: Remove width across the back using vertical adjustment lines."
    ]
    y_offset = 450
    for tip in fitting_tips:
        draw.text((1260, y_offset), tip, fill="#334155", font=font_body)
        y_offset += 60

    # Panel 3: Step-by-Step Stitching Sequence
    draw.rectangle([100, 1240, width - 100, 2400], outline="#94a3b8", width=2)
    draw.text((140, 1280), "3. STEP-BY-STEP STITCHING BLUEPRINT", fill="#0a231b", font=font_header)
    
    steps = [
        "Step 1: Transfer all darts, notches, and alignment dots using tailor's chalk.",
        "Step 2: Sew all shaping darts, pressing them toward the center back/front.",
        "Step 3: Stitch inner leg seams (in-seams) with a 1.5 cm standard seam allowance.",
        "Step 4: Join crotch seam continuously from front waist to back waist.",
        "Step 5: Attach waistband facing, finish edges with a clean serged or bound edge."
    ]
    y_offset = 1360
    for step in steps:
        draw.text((140, y_offset), step, fill="#1e293b", font=font_header)
        y_offset += 80

    # Save output
    output_filename = f"Velsci_{garment_type}_Instruction_Sheet.png"
    sheet.save(output_filename)
    print(f"Instruction sheet successfully generated and saved as '{output_filename}'.")

# Execute generator
generate_sewing_instruction_sheet(garment_type="Pants", size_label="L", height=172, waist=82, hips=98)
