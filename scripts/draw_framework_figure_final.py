from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        current = ""
        for ch in para:
            trial = current + ch
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def main():
    out_dir = Path(r"D:\数据集\new\shujudingjia\figures")
    out_png = out_dir / "fig_framework_target_aligned_valuation_final.png"
    out_pdf = out_dir / "fig_framework_target_aligned_valuation_final.pdf"

    width, height = 2200, 1500
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    font_regular = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 34)
    font_title = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 44)
    font_bottom = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 32)

    edge_color = "black"
    left_x = 90
    right_x = 1340
    box_w = 770
    box_h = 270
    y1, y2, y3 = 70, 515, 960

    boxes = [
        (
            left_x,
            y1,
            "异构学术图构建",
            "围绕 data pricing 主题收集论文、作者与机构信息，构建论文—论文 citation network 以及论文—作者—机构异构学术图。",
        ),
        (
            left_x,
            y2,
            "目标对齐引用上下文重建",
            "针对每条 citation edge 重建与目标被引论文准确对应的引用上下文，形成可靠的目标对齐语义输入。",
        ),
        (
            left_x,
            y3,
            "价值传播与应用转化",
            "融合语义质量、时间衰减和共同作者关系惩罚，计算文章级学术价值，并结合需求相似度生成价格建议。",
        ),
        (
            right_x,
            y1,
            "DeepSeek 边级语义标注",
            "对目标对齐上下文进行结构化语义标注，提取引用位置、相关性与情感等可审计的边级证据。",
        ),
        (
            right_x,
            y2,
            "融合边权与 Full model",
            "基于 q_ij × τ_ij × ρ_ij 构建加权引用边权，并在加权引用网络上进行文章级学术价值传播。",
        ),
        (
            right_x,
            y3,
            "需求感知价格建议",
            "将文章级学术价值与用户需求相似度结合，形成面向知识服务场景的个性化价格建议。",
        ),
    ]

    for x, y, title, body in boxes:
        draw.rectangle([x, y, x + box_w, y + box_h], outline=edge_color, width=5)
        draw.text((x + 26, y + 28), title, fill="black", font=font_title)
        body_lines = wrap_text(draw, body, font_regular, box_w - 52)
        yy = y + 120
        for line in body_lines:
            draw.text((x + 26, yy), line, fill="black", font=font_regular)
            yy += 48

    def arrow(x1, y1, x2, y2, width_px=6, head=24):
        draw.line((x1, y1, x2, y2), fill="black", width=width_px)
        if x2 > x1 and abs(y2 - y1) < 5:
            draw.polygon([(x2, y2), (x2 - head, y2 - head // 2), (x2 - head, y2 + head // 2)], fill="black")
        elif y2 > y1 and abs(x2 - x1) < 5:
            draw.polygon([(x2, y2), (x2 - head // 2, y2 - head), (x2 + head // 2, y2 - head)], fill="black")

    cx = left_x + box_w // 2
    arrow(cx, y1 + box_h, cx, y2 - 24)
    arrow(cx, y2 + box_h, cx, y3 - 24)
    arrow(left_x + box_w, y1 + box_h // 2, right_x - 28, y1 + box_h // 2)
    arrow(left_x + box_w, y2 + box_h // 2, right_x - 28, y2 + box_h // 2)
    arrow(left_x + box_w, y3 + box_h // 2, right_x - 28, y3 + box_h // 2)

    bottom_y = 1365
    draw.rectangle([90, bottom_y, 2110, 1440], outline="black", width=4)
    chain = "边级证据提取  →  加权引文网络传播  →  需求感知应用转化"
    bbox = draw.textbbox((0, 0), chain, font=font_bottom)
    text_w = bbox[2] - bbox[0]
    draw.text(((width - text_w) // 2, bottom_y + 18), chain, fill="black", font=font_bottom)

    image.save(out_png, dpi=(300, 300))
    image.save(out_pdf, resolution=300.0)


if __name__ == "__main__":
    main()
