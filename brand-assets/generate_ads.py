from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from crest_drawing import draw_pillow_crest

OUT = Path(__file__).resolve().parent
NAVY, TEAL, GOLD, WHITE = "#1E1B4B", "#0F766E", "#D97706", "#F8FAFC"

def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf"
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def rounded(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)

def ad1():
    im = Image.new("RGB", (1080, 1080), NAVY)
    d = ImageDraw.Draw(im)
    d.ellipse((760,-180,1220,280), fill=TEAL)
    d.ellipse((820,780,1280,1240), fill=GOLD)
    draw_pillow_crest(d, 58, 24, 142)
    d.text((220,112), "SKILLBRIDGE ACADEMY", font=font(36, True), fill=GOLD)
    d.text((70,250), "Weekend skills.\nReal portfolios.", font=font(82, True), fill=WHITE)
    d.text((70,500), "AI & Prompting Bootcamp", font=font(44, True), fill=WHITE)
    d.text((70,558), "4 weeks  •  PKR 8,000", font=font(34), fill="#CDEEE8")
    d.text((70,640), "Sat–Sun  •  7–9 PM PKT", font=font(34), fill=GOLD)
    rounded(d,(70,760,620,870),28,GOLD)
    d.text((124,785), "START YOUR FREE KIT", font=font(38,True), fill=NAVY)
    d.text((70,1000),"Practical learning. Portfolio review. No false promises.",font=font(24),fill=WHITE)
    im.save(OUT/"ad-creative-1.png",quality=95)

def ad2():
    im = Image.new("RGB",(1080,1080),WHITE)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,1080,230),fill=NAVY)
    draw_pillow_crest(d, 875, 20, 140)
    d.text((70,82),"BUILD YOUR REMOTE-WORK PATH",font=font(45,True),fill=WHITE)
    d.text((70,300),"Choose a focused track",font=font(58,True),fill=NAVY)
    rounded(d,(70,430,1010,650),32,"#E7F7F4")
    d.text((110,470),"AI & PROMPTING",font=font(36,True),fill=TEAL)
    d.text((110,525),"4 weeks  •  PKR 8,000",font=font(38,True),fill=NAVY)
    rounded(d,(70,700,1010,920),32,"#FFF4D5")
    d.text((110,740),"FREELANCE DIGITAL MARKETING",font=font(34,True),fill="#9A6700")
    d.text((110,795),"6 weeks  •  PKR 12,000",font=font(38,True),fill=NAVY)
    d.text((70,990),"Live weekends • Lifetime recordings • Mentor-led",font=font(27,True),fill=NAVY)
    im.save(OUT/"ad-creative-2.png",quality=95)

if __name__=="__main__":
    ad1()
    ad2()
