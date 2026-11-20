import asyncio
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np
import requests
from moviepy import AudioFileClip, ImageClip, concatenate_audioclips, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "promo-reel-30s.mp4"
STOCK_DIR = ROOT / "stock-assets"
W, H, FPS = 1080, 1920, 24
INDIGO = "#1E1B4B"
TEAL = "#0F766E"
COPPER = "#D97706"
OFF_WHITE = "#F8FAFC"

STOCK_URLS = [
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1080&h=1920&q=85",
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1080&h=1920&q=85",
    "https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=1080&h=1920&q=85",
    "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1080&h=1920&q=85",
    "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1080&h=1920&q=85",
]


@dataclass(frozen=True)
class Scene:
    narration: str
    captions: tuple[str, str]
    title: str
    detail: str
    kind: str
    image_path: Path | None


SCENE_COPY = [
    (
        "Pakistani university students and fresh graduates—turn your weekends into real-world freelancing and remote work skills with SkillBridge Academy!",
        ("Pakistani university students and fresh graduates—",
         "turn your weekends into real-world freelancing and remote work skills with SkillBridge Academy!"),
        "YOUR WEEKEND, WITH PURPOSE",
        "Mentor-led learning for students and fresh graduates",
        "students",
    ),
    (
        "Join our 4-week AI and Prompting Bootcamp for just PKR 8,000, and master practical AI workflows for modern clients.",
        ("Join our 4-week AI and Prompting Bootcamp for just PKR 8,000,",
         "and master practical AI workflows for modern clients."),
        "AI & PROMPTING",
        "4 weeks  •  PKR 8,000",
        "ai",
    ),
    (
        "Or enroll in Freelance Digital Marketing—a 6-week mentor-led program for PKR 12,000 to build real campaign skills.",
        ("Or enroll in Freelance Digital Marketing—",
         "a 6-week mentor-led program for PKR 12,000 to build real campaign skills."),
        "FREELANCE DIGITAL MARKETING",
        "6 weeks  •  PKR 12,000",
        "marketing",
    ),
    (
        "Attend live Zoom classes every Saturday and Sunday from 7 to 9 PM PKT, with lifetime recordings, portfolio reviews, and a verified certificate.",
        ("Attend live Zoom classes every Saturday and Sunday",
         "from 7 to 9 PM PKT, with lifetime recordings, portfolio reviews, and a verified certificate."),
        "LIVE WEEKEND CLASSES",
        "SAT + SUN  •  7–9 PM PKT  •  LIFETIME RECORDINGS",
        "schedule",
    ),
    (
        "Download your free Student Freelancing Starter Kit and apply today via WhatsApp or email at SkillBridge Academy!",
        ("Download your free Student Freelancing Starter Kit",
         "and apply today via WhatsApp or email at SkillBridge Academy!"),
        "YOUR NEXT STEP STARTS HERE",
        "Free Student Freelancing Starter Kit",
        "contact",
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def fetch_stock_images() -> list[Path | None]:
    STOCK_DIR.mkdir(parents=True, exist_ok=True)
    cached: list[Path | None] = []
    for index, url in enumerate(STOCK_URLS, start=1):
        destination = STOCK_DIR / f"scene-{index}.jpg"
        try:
            if not destination.exists() or destination.stat().st_size < 10_000:
                response = requests.get(url, timeout=(5, 25))
                response.raise_for_status()
                image = Image.open(__import__("io").BytesIO(response.content)).convert("RGB")
                image.save(destination, "JPEG", quality=90, optimize=True)
            with Image.open(destination) as image:
                image.verify()
            cached.append(destination)
            print(f"Stock photo ready: {destination.name}")
        except (requests.RequestException, OSError, ValueError) as error:
            print(f"Stock photo {index} unavailable; using designed fallback ({error})")
            cached.append(None)
    (STOCK_DIR / "SOURCES.txt").write_text(
        "Background images fetched from Unsplash image CDN (images.unsplash.com).\n"
        "Unsplash License: https://unsplash.com/license\n"
        "Image URLs are listed in generate_reel.py; verify attribution and licensing "
        "requirements before redistribution.\n",
        encoding="utf-8",
    )
    return cached


def draw_falcon_crest(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0) -> None:
    s = scale
    point = lambda x0, y0: (int(x + x0 * s), int(y + y0 * s))
    shield = [(42, 0), (78, 12), (76, 52), (60, 76), (42, 88), (24, 76), (8, 52), (6, 12)]
    draw.polygon([point(px, py) for px, py in shield], fill=INDIGO, outline=COPPER, width=max(1, int(2 * s)))
    wings = [(10, 22), (28, 29), (42, 24), (56, 29), (74, 22), (60, 41), (47, 44),
             (58, 48), (50, 53), (42, 50), (34, 53), (26, 48), (37, 44), (24, 41)]
    draw.polygon([point(px, py) for px, py in wings], fill=OFF_WHITE)
    draw.polygon([point(px, py) for px, py in [(45, 29), (70, 23), (54, 38), (45, 39)]], fill=COPPER)
    book = [(16, 56), (42, 62), (68, 56), (66, 72), (44, 82), (42, 80),
            (40, 82), (18, 72)]
    draw.polygon([point(px, py) for px, py in book], fill=TEAL, outline=OFF_WHITE, width=max(1, int(2 * s)))
    draw.line([point(42, 62), point(42, 80)], fill=OFF_WHITE, width=max(1, int(2 * s)))
    draw.polygon([point(px, py) for px, py in [(42, 5), (48, 15), (42, 24), (36, 15)]], fill=COPPER)


def font_lines(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=face)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def fallback_photo(kind: str) -> Image.Image:
    image = Image.new("RGB", (W, H), INDIGO)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((650, 140, 1320, 810), fill=(15, 118, 110, 255))
    draw.ellipse((-380, 1030, 520, 1940), fill=(217, 119, 6, 255))
    draw.rounded_rectangle((70, 320, 1010, 1460), radius=54, fill=(248, 250, 252, 22), outline=(248, 250, 252, 100), width=3)
    draw.rounded_rectangle((140, 610, 940, 1060), radius=30, fill=(248, 250, 252, 235))
    draw.rounded_rectangle((250, 700, 830, 1020), radius=18, fill=(30, 27, 75, 255))
    draw.rounded_rectangle((285, 735, 795, 980), radius=12, fill=(15, 118, 110, 255))
    draw.polygon([(200, 1070), (880, 1070), (990, 1170), (90, 1170)], fill=(248, 250, 252, 245))
    draw.rounded_rectangle((470, 1090, 610, 1112), radius=8, fill=(217, 119, 6, 220))
    if kind in {"students", "marketing"}:
        for cx, cy, color in [(330, 490, (217, 119, 6, 255)), (530, 450, (15, 118, 110, 255)), (730, 490, (217, 119, 6, 255))]:
            draw.ellipse((cx - 48, cy - 48, cx + 48, cy + 48), fill=color)
            draw.rounded_rectangle((cx - 70, cy + 55, cx + 70, cy + 235), radius=56, fill=(30, 27, 75, 240))
    else:
        draw.rounded_rectangle((170, 390, 520, 475), radius=18, fill=(248, 250, 252, 230))
        draw.rounded_rectangle((560, 390, 900, 475), radius=18, fill=(248, 250, 252, 230))
    return image


def background_image(path: Path | None, kind: str) -> Image.Image:
    if path:
        try:
            with Image.open(path) as source:
                return ImageOps.fit(source.convert("RGB"), (W, H), method=Image.Resampling.LANCZOS)
        except OSError:
            pass
    return fallback_photo(kind)


def draw_overlay(base: Image.Image, scene: Scene, caption: str, scene_number: int) -> Image.Image:
    image = base.convert("RGBA")
    shade = Image.new("RGBA", (W, H), (30, 27, 75, 0))
    alpha = Image.new("L", (1, H))
    for y in range(H):
        strength = int(145 + 105 * (y / H) ** 1.6)
        alpha.putpixel((0, y), strength)
    alpha = alpha.resize((W, H))
    shade.putalpha(alpha)
    image = Image.alpha_composite(image, shade)
    draw = ImageDraw.Draw(image, "RGBA")

    draw.rounded_rectangle((48, 48, 1032, 286), radius=40, fill=(30, 27, 75, 228), outline=(248, 250, 252, 85), width=2)
    draw_falcon_crest(draw, 76, 82, 1.25)
    draw.text((190, 96), "SKILLBRIDGE", font=font(43, True), fill=OFF_WHITE)
    draw.text((192, 154), "A C A D E M Y", font=font(22, True), fill=COPPER)
    draw.text((840, 103), f"{scene_number:02d} / 05", font=font(25, True), fill=OFF_WHITE)
    for index in range(5):
        left = 842 + index * 29
        draw.rounded_rectangle((left, 164, left + 21, 174), radius=5,
                               fill=COPPER if index == scene_number - 1 else (248, 250, 252, 90))

    draw.rounded_rectangle((58, 395, 1022, 865), radius=46, fill=(30, 27, 75, 205), outline=(248, 250, 252, 65), width=2)
    draw.rounded_rectangle((90, 430, 101, 482), radius=5, fill=COPPER)
    draw.text((128, 435), scene.title, font=font(35, True), fill=OFF_WHITE)
    title_text = scene.detail
    detail_face = font(45 if scene.kind in {"ai", "marketing", "contact"} else 35, True)
    detail_lines = font_lines(draw, title_text, detail_face, 835)
    for index, line in enumerate(detail_lines[:2]):
        draw.text((96, 555 + index * 64), line, font=detail_face, fill=COPPER if scene.kind in {"ai", "marketing", "contact"} else OFF_WHITE)

    if scene.kind in {"ai", "marketing"}:
        draw.rounded_rectangle((90, 715, 490, 808), radius=28, fill=TEAL)
        draw.text((119, 731), "MENTOR-LED  •  LIVE ZOOM", font=font(24, True), fill=OFF_WHITE)
        draw.rounded_rectangle((520, 715, 958, 808), radius=28, fill=COPPER)
        draw.text((557, 731), "WEEKEND BOOTCAMP", font=font(24, True), fill=OFF_WHITE)
    elif scene.kind == "schedule":
        draw.rounded_rectangle((90, 715, 958, 808), radius=28, fill=TEAL)
        draw.text((123, 731), "LIVE ZOOM  •  SATURDAY + SUNDAY", font=font(27, True), fill=OFF_WHITE)
    elif scene.kind == "contact":
        draw.rounded_rectangle((90, 715, 958, 808), radius=28, fill=TEAL)
        draw.text((123, 731), "+92 300 0000000  •  admissions@skillbridge.pk", font=font(25, True), fill=OFF_WHITE)
    elif scene.kind == "students":
        draw.rounded_rectangle((90, 715, 958, 808), radius=28, fill=TEAL)
        draw.text((123, 731), "PRACTICAL SKILLS  •  PORTFOLIO-FOCUSED", font=font(27, True), fill=OFF_WHITE)

    draw.rounded_rectangle((58, 1220, 1022, 1748), radius=44, fill=(248, 250, 252, 242), outline=(217, 119, 6, 240), width=4)
    draw.rounded_rectangle((88, 1252, 192, 1264), radius=6, fill=COPPER)
    caption_face = font(43, True)
    caption_lines = font_lines(draw, caption, caption_face, 865)
    caption_y = 1300 if len(caption_lines) <= 3 else 1282
    for line in caption_lines[:4]:
        draw.text((94, caption_y), line, font=caption_face, fill=INDIGO, stroke_width=0)
        caption_y += 88
    draw.text((94, 1665), "LEARN  •  PRACTICE  •  BUILD YOUR PORTFOLIO", font=font(22, True), fill=TEAL)
    draw.rounded_rectangle((58, 1800, 1022, 1864), radius=25, fill=(30, 27, 75, 220))
    draw.text((85, 1815), "SKILLBRIDGE.PK  |  WEEKENDS  •  7–9 PM PKT", font=font(25, True), fill=OFF_WHITE)
    return image.convert("RGB")


def atempo_filter(speed: float) -> str:
    filters: list[str] = []
    while speed > 2.0:
        filters.append("atempo=2.0")
        speed /= 2.0
    while speed < 0.5:
        filters.append("atempo=0.5")
        speed /= 0.5
    filters.append(f"atempo={speed:.6f}")
    return ",".join(filters)


async def synthesize_scene_audio(scene: Scene, path: Path) -> None:
    await edge_tts.Communicate(
        scene.narration,
        voice="en-US-AriaNeural",
        rate="+12%",
        volume="+0%",
    ).save(str(path))


def fit_audio_to_scene(source: Path, destination: Path) -> float:
    clip = AudioFileClip(str(source))
    try:
        original_duration = clip.duration
    finally:
        clip.close()
    speech_target = 5.78
    speed = original_duration / speech_target
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "error", "-i", str(source),
            "-af", f"{atempo_filter(speed)},apad,atrim=duration=6,asetpts=N/SR/TB",
            "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(destination),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return original_duration


def build_video(stock_paths: list[Path | None], workdir: Path) -> None:
    scenes = [
        Scene(*copy, path)
        for copy, path in zip(SCENE_COPY, stock_paths)
    ]
    image_clips = []
    audio_clips = []
    try:
        for number, scene in enumerate(scenes, start=1):
            base = background_image(scene.image_path, scene.kind)
            source_audio = workdir / f"scene-{number}.mp3"
            fitted_audio = workdir / f"scene-{number}.wav"
            fit_audio_to_scene(source_audio, fitted_audio)
            audio_clips.append(AudioFileClip(str(fitted_audio)))

            first_caption, second_caption = scene.captions
            first_words = len(first_caption.split())
            total_words = len(scene.narration.split())
            first_duration = 5.8 * first_words / total_words
            second_duration = 6.0 - first_duration
            for caption, duration in ((first_caption, first_duration), (second_caption, second_duration)):
                frame = draw_overlay(base, scene, caption, number)
                image_clips.append(ImageClip(np.asarray(frame), duration=duration))

        video = concatenate_videoclips(image_clips, method="compose")
        audio = concatenate_audioclips(audio_clips)
        video = video.with_duration(30).with_audio(audio.with_duration(30))
        video.write_videofile(
            str(OUT),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            audio_bitrate="192k",
            preset="medium",
            threads=4,
            logger=None,
        )
    finally:
        for clip in image_clips + audio_clips:
            clip.close()


async def main() -> None:
    paths = fetch_stock_images()
    scenes = [Scene(*copy, path) for copy, path in zip(SCENE_COPY, paths)]
    with tempfile.TemporaryDirectory(prefix="skillbridge-reel-") as temp:
        workdir = Path(temp)
        await asyncio.gather(*[
            synthesize_scene_audio(scene, workdir / f"scene-{index}.mp3")
            for index, scene in enumerate(scenes, start=1)
        ])
        build_video(paths, workdir)
    print(f"Generated {OUT} (1080x1920, 30 seconds, 5 scenes)")


if __name__ == "__main__":
    asyncio.run(main())
