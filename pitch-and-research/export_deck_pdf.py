from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from pathlib import Path

OUT=Path(__file__).resolve().parent/"client-pitch.pdf"
slides=[
("SkillBridge Academy","Weekend, mentor-led bootcamps for Pakistani students and graduates"),
("The problem","Students need practical structure, portfolio evidence, scheduling, and credible guidance"),
("The solution","Two focused tracks, live weekend delivery, recordings, certificate, and portfolio review"),
("AI & Prompting","4 weeks • PKR 8,000"),
("Freelance Digital Marketing","6 weeks • PKR 12,000"),
("System architecture","Landing page → validated form → lead summary → JSON/API → Admin → CSV → optional Sheets webhook"),
("RAG & voice","Verified knowledge-only chatbot with Gemini enhancement and local offline fallback"),
("Human safeguards","Scholarships and human follow-up are flagged; no automated admission or income promise"),
("Compliance","Never promise guaranteed jobs, fixed monthly dollar income, or overnight success"),
("Pilot measurement","Track qualified leads, conversion, attendance, portfolio completion, feedback, and coordinator workload"),
("Official contact","WhatsApp: +92 300 0000000 | https://wa.me/923000000000 | Email: admissions@skillbridge.pk"),
]
c=canvas.Canvas(str(OUT),pagesize=landscape(A4))
for title,body in slides:
    c.setFillColorRGB(30/255,27/255,75/255);c.rect(0,0,842,595,fill=1,stroke=0)
    c.setFillColorRGB(217/255,119/255,6/255);c.setFont("Helvetica-Bold",18);c.drawString(60,520,"SKILLBRIDGE ACADEMY")
    c.setFillColorRGB(248/255,250/255,252/255);c.setFont("Helvetica-Bold",42);c.drawString(60,420,title)
    crest=c.beginPath();crest.moveTo(790,560);crest.lineTo(816,552);crest.lineTo(814,523);crest.lineTo(803,506);crest.lineTo(790,500);crest.lineTo(777,506);crest.lineTo(766,523);crest.lineTo(764,552);crest.close()
    c.setFillColorRGB(30/255,27/255,75/255);c.setStrokeColorRGB(217/255,119/255,6/255);c.drawPath(crest,fill=1,stroke=1)
    falcon=c.beginPath();falcon.moveTo(770,541);falcon.lineTo(780,545);falcon.lineTo(790,542);falcon.lineTo(800,545);falcon.lineTo(810,541);falcon.lineTo(802,551);falcon.lineTo(794,553);falcon.lineTo(801,556);falcon.lineTo(796,559);falcon.lineTo(790,557);falcon.lineTo(784,559);falcon.lineTo(779,556);falcon.lineTo(786,553);falcon.lineTo(778,551);falcon.close()
    c.setFillColorRGB(248/255,250/255,252/255);c.drawPath(falcon,fill=1,stroke=0)
    beak=c.beginPath();beak.moveTo(797,545);beak.lineTo(808,542);beak.lineTo(801,550);beak.close()
    c.setFillColorRGB(217/255,119/255,6/255);c.drawPath(beak,fill=1,stroke=0)
    c.setFillColorRGB(15/255,118/255,110/255);c.setStrokeColorRGB(248/255,250/255,252/255)
    c.rect(775,518,30,12,fill=1,stroke=1)
    c.setStrokeColorRGB(248/255,250/255,252/255);c.line(790,518,790,530)
    c.setStrokeColorRGB(15/255,118/255,110/255);c.setLineWidth(4);c.line(60,495,782,495)
    c.setFont("Helvetica",24)
    words=body.split();line="";y=340
    for word in words:
        test=(line+" "+word).strip()
        if c.stringWidth(test,"Helvetica",24)>720:c.drawString(60,y,line);y-=38;line=word
        else:line=test
    if line:c.drawString(60,y,line)
    c.showPage()
c.save()
print(OUT)
