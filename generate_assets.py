import os
from PIL import Image, ImageDraw, ImageFont

def create_car_banner(filepath, title, category, color_theme, badge="DriveEase"):
    width, height = 800, 500
    img = Image.new("RGB", (width, height), color=color_theme["bg"])
    draw = ImageDraw.Draw(img)

    # Gradient-like bands
    for i in range(120):
        alpha_color = tuple(int(c * (0.8 + 0.2 * i / 120)) for c in color_theme["bg"])
        draw.line([(0, height - i), (width, height - i)], fill=alpha_color)

    # Accent top border
    draw.rectangle([0, 0, width, 8], fill=color_theme["accent"])

    # Modern abstract grid lines
    for x in range(0, width, 60):
        draw.line([(x, 0), (x, height)], fill=color_theme["grid"], width=1)
    for y in range(0, height, 60):
        draw.line([(0, y), (width, y)], fill=color_theme["grid"], width=1)

    # Sleek car silhouette / box
    cx, cy = width // 2, 270
    draw.rectangle([cx - 240, cy - 60, cx + 240, cy + 70], fill=color_theme["card_bg"], outline=color_theme["accent"], width=2)
    # Roof curve / cabin
    draw.polygon([(cx - 150, cy - 60), (cx - 70, cy - 130), (cx + 90, cy - 130), (cx + 170, cy - 60)], fill=color_theme["cabin"])

    # Wheels
    draw.ellipse([cx - 180, cy + 30, cx - 100, cy + 110], fill="#111827", outline=color_theme["accent"], width=4)
    draw.ellipse([cx - 155, cy + 55, cx - 125, cy + 85], fill="#E5E7EB")
    draw.ellipse([cx + 100, cy + 30, cx + 180, cy + 110], fill="#111827", outline=color_theme["accent"], width=4)
    draw.ellipse([cx + 125, cy + 55, cx + 155, cy + 85], fill="#E5E7EB")

    # Headlights & Taillights
    draw.polygon([(cx + 220, cy - 20), (cx + 240, cy - 10), (cx + 240, cy + 10), (cx + 210, cy + 10)], fill="#FFEA00")
    draw.polygon([(cx - 240, cy - 15), (cx - 220, cy - 15), (cx - 220, cy + 10), (cx - 240, cy + 10)], fill="#EF4444")

    # Text overlays
    draw.text((40, 40), f"⚡ {badge.upper()} VERIFIED", fill=color_theme["accent"])
    draw.text((40, 75), title, fill="#FFFFFF")
    draw.text((40, 115), f"Category: {category}  |  Insured & Sanitized", fill="#9CA3AF")

    img.save(filepath, quality=90)
    print(f"Generated {filepath}")

def generate_all():
    cars_dir = os.path.join("static", "images", "cars")
    os.makedirs(cars_dir, exist_ok=True)
    images_dir = os.path.join("static", "images")

    car_configs = [
        ("swift.jpg", "Maruti Suzuki Swift ZXi", "Hatchback", {"bg": (15, 23, 42), "card_bg": (30, 41, 59), "cabin": (51, 65, 85), "accent": (255, 199, 0), "grid": (20, 30, 50)}),
        ("city.jpg", "Honda City ZX Luxury", "Sedan", {"bg": (17, 24, 39), "card_bg": (31, 41, 55), "cabin": (55, 65, 81), "accent": (59, 130, 246), "grid": (25, 33, 48)}),
        ("thar.jpg", "Mahindra Thar 4x4 Off-Road", "SUV", {"bg": (24, 24, 27), "card_bg": (39, 39, 42), "cabin": (63, 63, 70), "accent": (239, 68, 68), "grid": (30, 30, 34)}),
        ("nexon_ev.jpg", "Tata Nexon EV Max", "Electric", {"bg": (6, 78, 59), "card_bg": (4, 120, 87), "cabin": (5, 150, 105), "accent": (52, 211, 153), "grid": (8, 90, 70)}),
        ("creta.jpg", "Hyundai Creta SX(O) Sunroof", "SUV", {"bg": (30, 27, 75), "card_bg": (49, 46, 129), "cabin": (67, 56, 202), "accent": (165, 180, 252), "grid": (38, 34, 90)}),
        ("fortuner.jpg", "Toyota Fortuner Legender 4x4", "SUV", {"bg": (28, 25, 23), "card_bg": (41, 37, 36), "cabin": (68, 64, 60), "accent": (245, 158, 11), "grid": (35, 31, 29)}),
        ("bmw.jpg", "BMW 3 Series Gran Limousine", "Luxury", {"bg": (15, 23, 42), "card_bg": (2, 132, 199), "cabin": (3, 105, 161), "accent": (56, 189, 248), "grid": (18, 28, 48)}),
        ("seltos.jpg", "Kia Seltos X-Line Edition", "SUV", {"bg": (39, 39, 42), "card_bg": (24, 24, 27), "cabin": (63, 63, 70), "accent": (244, 63, 94), "grid": (45, 45, 48)}),
    ]

    for filename, title, category, theme in car_configs:
        create_car_banner(os.path.join(cars_dir, filename), title, category, theme)

    # Default car image
    create_car_banner(
        os.path.join(images_dir, "default_car.jpg"),
        "DriveEase Verified Car", "Self-Drive Rental",
        {"bg": (15, 23, 42), "card_bg": (30, 41, 59), "cabin": (51, 65, 85), "accent": (255, 199, 0), "grid": (20, 30, 50)}
    )

    # Demo UPI QR Code
    qr_img = Image.new("RGB", (300, 300), color="#FFFFFF")
    qdraw = ImageDraw.Draw(qr_img)
    # Draw QR frame
    qdraw.rectangle([20, 20, 280, 280], outline="#111827", width=6)
    # 3 corner markers
    for ox, oy in [(40, 40), (200, 40), (40, 200)]:
        qdraw.rectangle([ox, oy, ox + 60, oy + 60], fill="#111827")
        qdraw.rectangle([ox + 12, oy + 12, ox + 48, oy + 48], fill="#FFFFFF")
        qdraw.rectangle([ox + 22, oy + 22, ox + 38, oy + 38], fill="#111827")
    # center demo pattern
    qdraw.rectangle([120, 120, 180, 180], fill="#FFC000")
    qdraw.text((128, 140), "UPI", fill="#111827")
    qdraw.text((80, 250), "SCAN TO PAY (DEMO)", fill="#4B5563")
    qr_img.save(os.path.join(images_dir, "upi_qr.png"))

    # Sample RC document
    rc_img = Image.new("RGB", (600, 350), color="#F3F4F6")
    rcdraw = ImageDraw.Draw(rc_img)
    rcdraw.rectangle([15, 15, 585, 335], outline="#1E3A8A", width=4)
    rcdraw.text((50, 40), "GOVERNMENT OF INDIA - CERTIFICATE OF REGISTRATION", fill="#1E3A8A")
    rcdraw.line([(50, 65), (550, 65)], fill="#1E3A8A", width=2)
    rcdraw.text((50, 90), "REGISTRATION NO : KA02KS5544", fill="#111827")
    rcdraw.text((50, 125), "VEHICLE CLASS   : MOTOR CAR (LMV - PRIVATE)", fill="#111827")
    rcdraw.text((50, 160), "MAKER / MODEL   : KIA MOTORS / SELTOS X-LINE", fill="#111827")
    rcdraw.text((50, 195), "FUEL TYPE       : PETROL / BS-VI COMPLIANT", fill="#111827")
    rcdraw.text((50, 230), "STATUS          : VALID (INSURANCE UP TO 2028)", fill="#059669")
    rcdraw.text((50, 280), "★ VERIFIED DOCUMENT COPY FOR DRIVE-EASE VERIFICATION ★", fill="#4B5563")
    rc_img.save(os.path.join(images_dir, "sample_rc.png"))

if __name__ == "__main__":
    generate_all()
