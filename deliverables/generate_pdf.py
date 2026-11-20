from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Flowable
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "brand-assets"))
from logo_rendering import draw_reportlab_logo

OUT=Path(__file__).resolve().parent/"Student-Freelancing-Starter-Kit.pdf"

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name="Section",parent=styles["Heading1"],textColor=colors.HexColor("#1E1B4B"),fontSize=20,spaceBefore=8,spaceAfter=10))
styles.add(ParagraphStyle(name="BodyNavy",parent=styles["BodyText"],textColor=colors.HexColor("#1E1B4B"),fontSize=10.5,leading=16))
navy=colors.HexColor("#1E1B4B");teal=colors.HexColor("#0F766E");gold=colors.HexColor("#D97706");cloud=colors.HexColor("#F8FAFC")

class Crest(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width=42*mm
        self.height=44*mm
    def draw(self):
        draw_reportlab_logo(self.canv, 0, 0, self.width, self.height)

hero_style=ParagraphStyle(name="Hero",parent=styles["BodyText"],textColor=colors.HexColor("#FFFFFF"),fontSize=20,leading=26)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm,title="Student Freelancing & Remote Work Starter Kit")
story=[]
story += [Table([[Crest(),Paragraph("Student Freelancing & Remote Work Starter Kit",hero_style)]],colWidths=[48*mm,126*mm],rowHeights=[80*mm],style=TableStyle([("BACKGROUND",(0,0),(-1,-1),navy),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),6*mm)])),Spacer(1,12*mm),
Paragraph("Start with skills, evidence, and a repeatable process.",styles["Section"]),
Paragraph("This starter kit is a practical guide for Pakistani university students and fresh graduates exploring freelancing or remote work. It does not guarantee a job or income.",styles["BodyNavy"]),Spacer(1,8*mm)]

story += [Paragraph("Your 4-Week Starter Roadmap",styles["Section"])]
roadmap=[
["Week","Focus","Deliverable"],
["1","Choose a track","Define interests, target skill, and three learning goals"],
["2","Learn the fundamentals","Complete practice tasks and document what worked"],
["3","Build portfolio evidence","Create one original case study or sample project"],
["4","Package your offer","Write an updated profile, proposal template, and outreach plan"],
]
t=Table(roadmap,colWidths=[20*mm,48*mm,106*mm],repeatRows=1)
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),teal),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.5,colors.HexColor("#CAD5DE")),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,cloud]),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
story += [t,PageBreak()]

story += [Paragraph("Portfolio Checklist",styles["Section"]),
Paragraph("A useful portfolio shows process and evidence—not unsupported claims.",styles["BodyNavy"]),Spacer(1,5*mm)]
checklist=[
"□ Define who you help and which service you provide.",
"□ Publish one strong sample or case study.",
"□ Explain the problem, your process, and the outcome.",
"□ Include only work you created or have permission to show.",
"□ Add a clear, honest profile and contact method.",
"□ Include an original bio and avoid copied testimonials.",
"□ Prepare 3–5 relevant proposal examples.",
"□ Set boundaries for availability, revisions, and privacy.",
"□ Review your work for grammar, accuracy, and accessibility.",
]
for item in checklist:story.append(Paragraph(item,styles["BodyNavy"]))
story += [Spacer(1,8*mm),Paragraph("Professional Outreach Prompt",styles["Section"]),
Paragraph("<b>Subject:</b> Freelance support for [specific need]<br/><br/><b>Message:</b> Hello [name]. I am practicing [skill] and prepared a relevant sample for [need]. Here is the work. I would be happy to understand your requirements and explain how I would approach the project.",styles["BodyNavy"]),
PageBreak()]

story += [Paragraph("SkillBridge Academy Bootcamp Overview",styles["Section"])]
programs=[
["Track","Duration","Fee"],
["AI & Prompting Bootcamp","4 weeks","PKR 8,000"],
["Freelance Digital Marketing","6 weeks","PKR 12,000"],
]
t=Table(programs,colWidths=[78*mm,40*mm,56*mm])
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),navy),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.5,colors.HexColor("#CAD5DE")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
story += [t,Spacer(1,7*mm),
Paragraph("<b>Schedule:</b> Live Zoom sessions on Saturdays and Sundays, 7:00 PM–9:00 PM PKT.",styles["BodyNavy"]),
Paragraph("<b>Access:</b> Lifetime access to session recordings.",styles["BodyNavy"]),
Paragraph("<b>Support:</b> Verified completion certificate and portfolio review are included.",styles["BodyNavy"]),
Paragraph("<b>Scholarships:</b> Requests require human coordinator review.",styles["BodyNavy"]),
Spacer(1,5*mm),
Paragraph("<b>Official admissions contact</b>",styles["Section"]),
Paragraph("<b>WhatsApp:</b> +92 300 0000000 (https://wa.me/923000000000)",styles["BodyNavy"]),
Paragraph("<b>Email:</b> admissions@skillbridge.pk",styles["BodyNavy"]),
Spacer(1,8*mm),
Paragraph("Honest Next Step",styles["Section"]),
Paragraph("Choose the track that matches your goal, prepare questions for the admissions team, and build one small project. SkillBridge supports learning and practical readiness; it never promises jobs, fixed monthly dollar income, or overnight success.",styles["BodyNavy"]),
Spacer(1,12*mm),
Table([[Paragraph("AI & Prompting → practical AI workflows",styles["BodyNavy"])],[Paragraph("Digital Marketing → freelance marketing foundations",styles["BodyNavy"])],[Paragraph("Portfolio → evidence of your capability",styles["BodyNavy"])]],colWidths=[174*mm],style=TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFF4D5")),("BOX",(0,0),(-1,-1),.5,gold),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))]

doc.build(story)
print(OUT)
