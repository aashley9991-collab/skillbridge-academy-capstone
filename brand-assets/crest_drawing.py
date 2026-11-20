import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

INDIGO = "#1E1B4B"
GOLD = "#D97706"
WHITE = "#F8FAFC"
RAYS = (
    (145, 210, 8), (177, 177, 5), (214, 151, 8),
    (256, 130, 5), (310, 119, 9), (364, 130, 5),
    (406, 151, 8), (443, 177, 5), (475, 210, 8),
)
WING_LEFT = (
    (310, 83), (283, 101), (254, 98), (220, 79), (199, 53),
    (205, 91), (158, 64), (177, 104), (119, 83), (146, 121),
    (56, 101), (101, 139), (49, 148), (109, 168), (75, 190),
    (162, 185), (220, 157), (274, 137), (292, 163), (310, 176),
)
FEATHERS = (
    ((282, 115), (230, 100), (178, 76)),
    ((269, 132), (205, 122), (128, 99)),
    ((250, 148), (188, 150), (94, 137)),
    ((235, 160), (180, 174), (119, 173)),
)


def _pillow_font(size):
    candidates = (
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, max(1, size))
    return ImageFont.load_default()


def _draw_pillow_curved_name(draw, x, y, scale):
    font = _pillow_font(round(29 * scale))
    name = "SKILLBRIDGE"
    spacing = 3.5 * scale
    advances = [draw.textlength(char, font=font) + spacing for char in name]
    distance = -sum(advances) / 2
    radius = 156 * scale
    center_x, center_y = x + 310 * scale, y + 300 * scale
    for char, advance in zip(name, advances):
        distance += advance / 2
        angle = math.radians(270) + distance / radius
        cx = center_x + radius * math.cos(angle)
        cy = center_y - radius * math.sin(angle)
        tangent = math.degrees(math.atan2(-math.cos(angle), -math.sin(angle)))
        glyph = Image.new("L", (max(8, round(50 * scale)), max(8, round(54 * scale))), 0)
        ImageDraw.Draw(glyph).text(
            (glyph.width / 2, glyph.height / 2),
            char,
            font=font,
            fill=255,
            anchor="mm",
        )
        rotated = glyph.rotate(-tangent, resample=Image.Resampling.BICUBIC, expand=True)
        draw.bitmap(
            (round(cx - rotated.width / 2), round(cy - rotated.height / 2)),
            rotated,
            fill=INDIGO,
        )
        distance += advance / 2


def draw_pillow_crest(draw: ImageDraw.ImageDraw, x: float, y: float, width: float) -> None:
    scale = width / 620

    def point(px, py):
        return (round(x + px * scale), round(y + py * scale))

    def polygon(points, fill, outline=None, stroke=0):
        draw.polygon([point(px, py) for px, py in points], fill=fill)
        if outline:
            closed = [point(px, py) for px, py in points]
            closed.append(closed[0])
            draw.line(closed, fill=outline, width=max(1, round(stroke * scale)), joint="curve")

    ring_box = [point(90, 90), point(530, 530)]
    draw.ellipse(ring_box, fill=WHITE, outline=GOLD, width=max(1, round(16 * scale)))
    draw.ellipse([point(106, 106), point(514, 514)], outline=INDIGO, width=max(1, round(5 * scale)))

    for end_x, end_y, line_width in RAYS:
        draw.line(
            [point(310, 363), point(end_x, end_y)],
            fill=GOLD,
            width=max(1, round(line_width * scale)),
        )

    right_wing = tuple((620 - px, py) for px, py in reversed(WING_LEFT))
    polygon(WING_LEFT + right_wing[1:], INDIGO, GOLD, 4)

    for left, control, end in FEATHERS:
        for points in ((left, control, end), (
            (620 - left[0], left[1]),
            (620 - control[0], control[1]),
            (620 - end[0], end[1]),
        )):
            draw.line([point(*item) for item in points], fill=WHITE, width=max(1, round(4 * scale)))

    polygon(((281, 100), (310, 68), (339, 100), (329, 126), (310, 149), (291, 126)), INDIGO, GOLD, 3)
    for eye in ((294, 119), (326, 119)):
        draw.ellipse([point(eye[0] - 2, eye[1] - 2), point(eye[0] + 2, eye[1] + 2)], fill=WHITE)
    polygon(((302, 128), (310, 131), (318, 128), (310, 143)), GOLD)
    polygon(((300, 145), (310, 157), (320, 145), (316, 177), (310, 187), (304, 177)), GOLD, INDIGO, 2)

    _draw_pillow_curved_name(draw, x, y, scale)

    polygon(((111, 498), (39, 478), (57, 525), (30, 562), (127, 587), (143, 537)), INDIGO, GOLD, 5)
    polygon(((509, 498), (581, 478), (563, 525), (590, 562), (493, 587), (477, 537)), INDIGO, GOLD, 5)
    polygon(((112, 493), (310, 529), (508, 493), (491, 582), (310, 618), (129, 582)), INDIGO, GOLD, 6)
    draw.arc([point(131, 486), point(489, 545)], 5, 175, fill=WHITE, width=max(1, round(3 * scale)))
    academy_font = _pillow_font(round(36 * scale))
    draw.text(point(310, 562), "ACADEMY", font=academy_font, fill=WHITE, anchor="mm")


def draw_reportlab_crest(canvas, x: float, y: float, width: float, height: float) -> None:
    scale = min(width / 620, height / 660)
    offset_x = x + (width - 620 * scale) / 2
    offset_y = y + (height - 660 * scale) / 2

    def point(px, py):
        return (offset_x + px * scale, offset_y + (660 - py) * scale)

    def path_for(points):
        path = canvas.beginPath()
        first = point(*points[0])
        path.moveTo(*first)
        for px, py in points[1:]:
            path.lineTo(*point(px, py))
        path.close()
        return path

    def fill_poly(points, fill, stroke=None, line_width=1):
        canvas.setFillColor(HexColor(fill))
        if stroke:
            canvas.setStrokeColor(HexColor(stroke))
            canvas.setLineWidth(line_width * scale)
        canvas.drawPath(path_for(points), fill=1, stroke=1 if stroke else 0)

    center_x, center_y = point(310, 310)
    canvas.setFillColor(HexColor(WHITE))
    canvas.setStrokeColor(HexColor(GOLD))
    canvas.setLineWidth(16 * scale)
    canvas.circle(center_x, center_y, 220 * scale, fill=1, stroke=1)
    canvas.setStrokeColor(HexColor(INDIGO))
    canvas.setLineWidth(5 * scale)
    canvas.circle(center_x, center_y, 204 * scale, fill=0, stroke=1)

    canvas.setStrokeColor(HexColor(GOLD))
    for end_x, end_y, line_width in RAYS:
        canvas.setLineWidth(line_width * scale)
        canvas.line(*point(310, 363), *point(end_x, end_y))

    right_wing = tuple((620 - px, py) for px, py in reversed(WING_LEFT))
    fill_poly(WING_LEFT + right_wing[1:], INDIGO, GOLD, 4)
    canvas.setStrokeColor(HexColor(WHITE))
    for left, control, end in FEATHERS:
        canvas.setLineWidth(4 * scale)
        canvas.line(*point(*left), *point(*control))
        canvas.line(*point(*control), *point(*end))
        canvas.line(*point(620 - left[0], left[1]), *point(620 - control[0], control[1]))
        canvas.line(*point(620 - control[0], control[1]), *point(620 - end[0], end[1]))

    fill_poly(((281, 100), (310, 68), (339, 100), (329, 126), (310, 149), (291, 126)), INDIGO, GOLD, 3)
    fill_poly(((302, 128), (310, 131), (318, 128), (310, 143)), GOLD)
    fill_poly(((300, 145), (310, 157), (320, 145), (316, 177), (310, 187), (304, 177)), GOLD, INDIGO, 2)

    font_size = max(4, 29 * scale)
    spacing = 3.5 * scale
    name = "SKILLBRIDGE"
    advances = [stringWidth(char, "Helvetica-Bold", font_size) + spacing for char in name]
    distance = -sum(advances) / 2
    radius = 156
    canvas.setFillColor(HexColor(INDIGO))
    canvas.setFont("Helvetica-Bold", font_size)
    for char, advance in zip(name, advances):
        distance += advance / 2
        angle = math.radians(270) + distance / radius
        px = 310 + radius * math.cos(angle)
        py = 300 - radius * math.sin(angle)
        tangent = math.degrees(math.atan2(math.cos(angle), -math.sin(angle)))
        canvas.saveState()
        canvas.translate(*point(px, py))
        canvas.rotate(tangent)
        canvas.drawCentredString(0, 0, char)
        canvas.restoreState()
        distance += advance / 2

    fill_poly(((111, 498), (39, 478), (57, 525), (30, 562), (127, 587), (143, 537)), INDIGO, GOLD, 5)
    fill_poly(((509, 498), (581, 478), (563, 525), (590, 562), (493, 587), (477, 537)), INDIGO, GOLD, 5)
    fill_poly(((112, 493), (310, 529), (508, 493), (491, 582), (310, 618), (129, 582)), INDIGO, GOLD, 6)
    canvas.setFillColor(HexColor(WHITE))
    canvas.setFont("Helvetica-Bold", max(5, 36 * scale))
    canvas.drawCentredString(*point(310, 562), "ACADEMY")
