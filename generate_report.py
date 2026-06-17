import json
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER

app = Flask(__name__)
CORS(app)

# ── PUT YOUR GMAIL DETAILS HERE ──────────────────

GMAIL_ADDRESS  = "howrushyamsundhar@gmail.com"       # your Gmail
GMAIL_APP_PASS = "nbkx yuvy odbd uzdh" 
# ─────────────────────────────────────────────────

def generate_pdf(employee_data, output_path):
    name       = employee_data.get("name", "Unknown")
    role       = employee_data.get("role", "Unknown")
    department = employee_data.get("department", "Unknown")
    manager    = employee_data.get("manager", "Your Manager")
    start_date = employee_data.get("start_date", datetime.now().strftime("%B %d, %Y"))
    note       = employee_data.get("note", "")
    generated  = datetime.now().strftime("%B %d, %Y at %H:%M")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        rightMargin=inch, leftMargin=inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("T", parent=styles["Normal"], fontSize=24,
        textColor=colors.HexColor("#1F4E79"), alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=4)
    sub_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=13,
        textColor=colors.HexColor("#2E75B6"), alignment=TA_CENTER,
        fontName="Helvetica", spaceAfter=4)
    section_style = ParagraphStyle("SEC", parent=styles["Normal"], fontSize=12,
        textColor=colors.HexColor("#1F4E79"), fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("B", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#333333"), fontName="Helvetica", leading=18)
    note_style = ParagraphStyle("N", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#1F4E79"), fontName="Helvetica-Oblique",
        leading=18, leftIndent=12)
    footer_style = ParagraphStyle("F", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#AAAAAA"), alignment=TA_CENTER,
        fontName="Helvetica")
    check_style = ParagraphStyle("C", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#333333"), fontName="Helvetica",
        leading=20, leftIndent=8)

    story = []

    # ── Header ──
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("Welcome to the Team!", title_style))
    story.append(Paragraph("Employee Onboarding Summary Report", sub_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor("#1F4E79")))
    story.append(Spacer(1, 0.2*inch))

    # ── Employee Details Table ──
    story.append(Paragraph("Employee Information", section_style))
    detail_data = [
        ["Full Name",       name],
        ["Role / Title",    role],
        ["Department",      department],
        ["Reporting To",    manager],
        ["Start Date",      start_date],
        ["Report ID",       f"ONB-{datetime.now().strftime('%Y%m%d%H%M%S')}"],
        ["Generated On",    generated],
    ]
    detail_table = Table(detail_data, colWidths=[2.2*inch, 4.3*inch])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND",      (0,0),(0,-1), colors.HexColor("#EEF4FB")),
        ("BACKGROUND",      (1,0),(1,-1), colors.white),
        ("TEXTCOLOR",       (0,0),(0,-1), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR",       (1,0),(1,-1), colors.HexColor("#1A1A1A")),
        ("FONTNAME",        (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTNAME",        (1,0),(1,-1), "Helvetica"),
        ("FONTSIZE",        (0,0),(-1,-1), 11),
        ("ROWBACKGROUNDS",  (0,0),(-1,-1), [colors.HexColor("#EEF4FB"), colors.HexColor("#F8FAFC")]),
        ("GRID",            (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING",         (0,0),(-1,-1), 10),
        ("VALIGN",          (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.2*inch))

    # ── Welcome Message ──
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Paragraph("Welcome Message", section_style))
    story.append(Paragraph(f"Dear {name},", body_style))
    story.append(Spacer(1, 0.08*inch))
    story.append(Paragraph(
        f"We are absolutely thrilled to welcome you to the <b>{department}</b> team "
        f"as our new <b>{role}</b>. You are joining at an exciting time and we can't "
        f"wait to see the amazing contributions you'll make. Your reporting manager "
        f"<b>{manager}</b> will be in touch to schedule your first-week orientation.",
        body_style))
    if note:
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"Personal note: \"{note}\"", note_style))
    story.append(Spacer(1, 0.2*inch))

    # ── First Week Checklist ──
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Paragraph("First Week Checklist", section_style))
    checklist = [
        "Complete your ID and access card setup with the HR team",
        "Attend the company orientation session on Day 1",
        f"Meet your reporting manager {manager} for a 1:1 introduction",
        "Set up your laptop, work email, Slack, and required software",
        "Review the employee handbook sent to your email separately",
        "Complete the onboarding form in the HR portal by Day 3",
        "Join your department team meeting and introduce yourself",
        "Set up your profile on the internal company directory",
    ]
    for item in checklist:
        story.append(Paragraph(f"  [  ]   {item}", check_style))
    story.append(Spacer(1, 0.2*inch))

    # ── Key Contacts Table ──
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Paragraph("Key Contacts", section_style))
    contacts_data = [
        ["Role",            "Who to Contact",       "For What"],
        ["HR Team",         "hr@company.com",       "Documents, payroll, benefits"],
        ["IT Support",      "it@company.com",       "Laptop, software, access"],
        ["Your Manager",    manager,                "Day-to-day guidance"],
        ["Office Admin",    "admin@company.com",    "Desk, ID card, facilities"],
    ]
    contacts_table = Table(contacts_data, colWidths=[1.8*inch, 2.2*inch, 2.5*inch])
    contacts_table.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR",      (0,0),(-1,0), colors.white),
        ("FONTNAME",       (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTNAME",       (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0),(-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID",           (0,0),(-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING",        (0,0),(-1,-1), 8),
        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(contacts_table)
    story.append(Spacer(1, 0.2*inch))

    # ── Policies ──
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Paragraph("Important Policies to Review", section_style))
    for policy in [
        "Code of Conduct and Ethics Policy",
        "Data Privacy and Information Security Policy",
        "Leave and Attendance Policy",
        "Remote Work and Flexible Hours Policy",
        "Health, Safety and Wellbeing Guidelines",
    ]:
        story.append(Paragraph(f"  -  {policy}", body_style))
        story.append(Spacer(1, 0.03*inch))
    story.append(Spacer(1, 0.25*inch))

    # ── Footer ──
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1F4E79")))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        f"Generated automatically by Employee Onboarding Automation System  |  {generated}",
        footer_style))
    story.append(Paragraph(
        "Powered by Python · Flask · ReportLab · Azure DevOps",
        footer_style))

    doc.build(story)
    return output_path


def send_email(to_email, employee_data, pdf_path):
    name       = employee_data.get("name")
    role       = employee_data.get("role")
    department = employee_data.get("department")
    manager    = employee_data.get("manager", "Your Manager")
    note       = employee_data.get("note", "")
    start_date = employee_data.get("start_date", "Your start date")

    msg = MIMEMultipart("alternative")
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = to_email
    msg["Subject"] = f"Welcome to the Team, {name}! Your Onboarding Pack is Here"

    html_body = f"""
<html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
<div style="max-width:600px;margin:40px auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

  <div style="background:#1F4E79;padding:40px 40px 30px;text-align:center;">
    <div style="font-size:48px;margin-bottom:12px;">🎉</div>
    <h1 style="color:white;margin:0;font-size:26px;">Welcome to the Team, {name}!</h1>
    <p style="color:#B3D1F0;margin:8px 0 0;font-size:15px;">Your onboarding journey begins today</p>
  </div>

  <div style="padding:32px 40px;">
    <p style="font-size:16px;color:#333;line-height:1.6;">Dear <b>{name}</b>,</p>
    <p style="font-size:15px;color:#555;line-height:1.7;">
      We are absolutely thrilled to welcome you to the
      <b style="color:#1F4E79">{department}</b> team as our new
      <b style="color:#1F4E79">{role}</b>. You are joining at an exciting time
      and we can't wait to see the amazing contributions you'll make.
    </p>
    {"<p style='font-size:14px;color:#1F4E79;font-style:italic;background:#EEF4FB;padding:12px 16px;border-left:4px solid #2E75B6;border-radius:4px;'>" + note + "</p>" if note else ""}

    <div style="background:#F8FAFC;border-radius:8px;padding:20px 24px;margin:24px 0;border:1px solid #E0E8F0;">
      <h3 style="color:#1F4E79;margin:0 0 16px;font-size:15px;">Your Onboarding Details</h3>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <tr><td style="padding:9px 0;color:#888;width:40%;border-bottom:1px solid #EEE;">Full Name</td><td style="color:#333;font-weight:bold;border-bottom:1px solid #EEE;">{name}</td></tr>
        <tr><td style="padding:9px 0;color:#888;border-bottom:1px solid #EEE;">Role</td><td style="color:#333;font-weight:bold;border-bottom:1px solid #EEE;">{role}</td></tr>
        <tr><td style="padding:9px 0;color:#888;border-bottom:1px solid #EEE;">Department</td><td style="color:#333;font-weight:bold;border-bottom:1px solid #EEE;">{department}</td></tr>
        <tr><td style="padding:9px 0;color:#888;border-bottom:1px solid #EEE;">Start Date</td><td style="color:#333;font-weight:bold;border-bottom:1px solid #EEE;">{start_date}</td></tr>
        <tr><td style="padding:9px 0;color:#888;">Reporting Manager</td><td style="color:#333;font-weight:bold;">{manager}</td></tr>
      </table>
    </div>

    <h3 style="color:#1F4E79;font-size:15px;margin:24px 0 12px;">Your First Week Checklist</h3>
    <table style="width:100%;font-size:14px;color:#555;">
      <tr><td style="padding:8px 0;">✅&nbsp; Complete ID and access card setup with HR</td></tr>
      <tr><td style="padding:8px 0;border-top:1px solid #F0F0F0;">✅&nbsp; Attend company orientation session on Day 1</td></tr>
      <tr><td style="padding:8px 0;border-top:1px solid #F0F0F0;">✅&nbsp; Meet <b>{manager}</b> for your 1:1 introduction</td></tr>
      <tr><td style="padding:8px 0;border-top:1px solid #F0F0F0;">✅&nbsp; Set up laptop, email, Slack and required tools</td></tr>
      <tr><td style="padding:8px 0;border-top:1px solid #F0F0F0;">✅&nbsp; Review the employee handbook</td></tr>
      <tr><td style="padding:8px 0;border-top:1px solid #F0F0F0;">✅&nbsp; Complete onboarding form in HR portal by Day 3</td></tr>
      <tr><td style="padding:8px 0;border-top:1px solid #F0F0F0;">✅&nbsp; Join department meeting and introduce yourself</td></tr>
    </table>

    <h3 style="color:#1F4E79;font-size:15px;margin:24px 0 12px;">Key Contacts</h3>
    <table style="width:100%;font-size:13px;border-collapse:collapse;">
      <tr style="background:#1F4E79;color:white;">
        <td style="padding:8px 12px;font-weight:bold;">Team</td>
        <td style="padding:8px 12px;font-weight:bold;">Contact</td>
        <td style="padding:8px 12px;font-weight:bold;">For</td>
      </tr>
      <tr style="background:#F8FAFC;"><td style="padding:8px 12px;color:#555;">HR Team</td><td style="padding:8px 12px;">hr@company.com</td><td style="padding:8px 12px;color:#555;">Docs, payroll</td></tr>
      <tr><td style="padding:8px 12px;color:#555;">IT Support</td><td style="padding:8px 12px;">it@company.com</td><td style="padding:8px 12px;color:#555;">Laptop, access</td></tr>
      <tr style="background:#F8FAFC;"><td style="padding:8px 12px;color:#555;">Your Manager</td><td style="padding:8px 12px;">{manager}</td><td style="padding:8px 12px;color:#555;">Day-to-day</td></tr>
    </table>

    <div style="background:#1F4E79;border-radius:8px;padding:20px 24px;margin:28px 0;text-align:center;">
      <p style="color:#B3D1F0;margin:0 0 6px;font-size:13px;">Your personalised onboarding report is attached as a PDF</p>
      <p style="color:white;margin:0;font-size:15px;font-weight:bold;">Open the attachment for your complete onboarding summary</p>
    </div>

    <p style="font-size:15px;color:#555;line-height:1.7;">
      If you have any questions before your start date, please don't hesitate to
      reach out to the HR team. We're here to make your transition as smooth as possible.
    </p>
    <p style="font-size:15px;color:#333;margin-top:24px;">
      Warm regards,<br>
      <b style="color:#1F4E79;">HR Team</b><br>
      <span style="font-size:13px;color:#888;">Employee Onboarding Automation System</span>
    </p>
  </div>

  <div style="background:#F8FAFC;padding:20px 40px;border-top:1px solid #EEE;text-align:center;">
    <p style="font-size:12px;color:#AAA;margin:0;">
      This email was generated automatically by the Employee Onboarding Automation System<br>
      Powered by Python &middot; Flask &middot; ReportLab &middot; Gmail SMTP
    </p>
  </div>
</div>
</body></html>
"""
    msg.attach(MIMEText(html_body, "html"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition",
        f"attachment; filename=onboarding_{name.replace(' ','_')}.pdf")
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())


def load_employee_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


@app.route("/")
def index():
    return jsonify({
        "service": "Employee Onboarding Automation System",
        "status":  "running",
        "endpoints": {
            "onboard": "POST /onboard — body: {name, role, department, email, manager, note, start_date}",
            "report":  "GET  /report/<filename>"
        }
    })


@app.route("/onboard", methods=["POST"])
def onboard():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    missing = [f for f in ["name", "role", "department", "email"] if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    safe_name = data["name"].replace(" ", "_")
    pdf_path  = os.path.join("reports", f"onboarding_{safe_name}.pdf")

    generate_pdf(data, pdf_path)

    try:
        send_email(data["email"], data, pdf_path)
        return jsonify({
            "success": True,
            "message": f"Onboarding email sent to {data['email']}!",
            "report":  f"onboarding_{safe_name}.pdf"
        }), 200
    except Exception as e:
        return jsonify({"error": f"PDF generated but email failed: {str(e)}"}), 500


@app.route("/report/<filename>")
def get_report(filename):
    path = os.path.join("reports", filename)
    if not os.path.exists(path):
        return jsonify({"error": "Report not found"}), 404
    return send_file(path, mimetype="application/pdf", as_attachment=True)


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    if len(sys.argv) > 1:
        employee = load_employee_json(sys.argv[1])
        safe     = employee.get("name", "output").replace(" ", "_")
        out      = os.path.join("reports", f"onboarding_{safe}.pdf")
        print(f"Report saved to: {generate_pdf(employee, out)}")
    else:
        print("Starting Flask server on http://localhost:5000")
        app.run(debug=True, host="0.0.0.0", port=5000)