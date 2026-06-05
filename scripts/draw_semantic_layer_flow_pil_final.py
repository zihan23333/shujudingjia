from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(r"D:\数据集\new\shujudingjia\figures")
OUT_PNG = OUT_DIR / "fig_target_aligned_semantic_layer_flow_final.png"
OUT_PDF = OUT_DIR / "fig_target_aligned_semantic_layer_flow_final.pdf"

FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 34)
FONT_BODY = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 24)
FONT_BOTTOM = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 28)


def draw_box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, body_lines: list[str]):
    draw.rectangle([x, y, x + w, y + h], outline="black", width=4)
    draw.text((x + 22, y + 24), title, fill="black", font=FONT_TITLE)
    yy = y + 104
    for line in body_lines:
        draw.text((x + 22, yy), line, fill="black", font=FONT_BODY)
        yy += 34


def draw_down_arrow(draw: ImageDraw.ImageDraw, x: int, y1: int, y2: int):
    draw.line((x, y1, x, y2), fill="black", width=5)
    draw.polygon([(x, y2), (x - 14, y2 - 24), (x + 14, y2 - 24)], fill="black")


def draw_right_arrow(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int):
    draw.line((x1, y, x2, y), fill="black", width=5)
    draw.polygon([(x2, y), (x2 - 24, y - 14), (x2 - 24, y + 14)], fill="black")


def main():
    img = Image.new("RGB", (2100, 1250), "white")
    draw = ImageDraw.Draw(img)

    left_x = 90
    left_w = 640
    box_h = 150
    y_positions = [60, 260, 460, 660, 860]
    items = [
        ("204 citation edges", ["semantic layer construction start"]),
        ("reference entry matching", ["match target cited paper"]),
        ("citation marker localization", ["locate target marker"]),
        ("target-aligned context extraction", ["extract aligned citation contexts"]),
        ("113 DeepSeek semantic edges", ["formal semantic layer"]),
    ]

    for (title, body), y in zip(items, y_positions):
        draw_box(draw, left_x, y, left_w, box_h, title, body)

    cx = left_x + left_w // 2
    for i in range(len(y_positions) - 1):
        draw_down_arrow(draw, cx, y_positions[i] + box_h, y_positions[i + 1] - 14)

    right_x, right_y, right_w, right_h = 1080, 250, 820, 470
    draw_box(
        draw,
        right_x,
        right_y,
        right_w,
        right_h,
        "91 default fallback edges",
        [
            "default q = 0.3; old llm_results.csv not reused.",
            "",
            "Typical reasons:",
            "• PDF / text unavailable",
            "• reference parsing failure",
            "• citation marker not found",
            "• ambiguous grouped citation",
            "• context-target mismatch risk",
        ],
    )

    draw_right_arrow(draw, left_x + left_w, y_positions[3] + box_h // 2, right_x - 18)

    draw.rectangle([90, 1110, 1910, 1185], outline="black", width=3)
    summary = "Conservative strategy: prioritize target-context alignment reliability over higher semantic coverage"
    draw.text((120, 1130), summary, fill="black", font=FONT_BOTTOM)

    img.save(OUT_PNG, dpi=(300, 300))
    img.save(OUT_PDF, resolution=300.0)


if __name__ == "__main__":
    main()
