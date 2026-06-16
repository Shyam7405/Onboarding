import json
import os
import sys
from datetime import datetime
from flask import Flask, send_file, jsonify, request
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

app = Flask(__name__)

# ─────────────────────────────────────────────
# CORE: Generate PDF from employee data dict
# ─────────────────────────────────────────────
def generate_pdf(employee_data: dict, output_path: str) -> str:
    name       = employee_data.get("name", "Unknown")
    role       = employee_data.get("role", "Unknown")
    department = employee_data.get("department", "Unknown")
    generated  = datetime.now().strftime("%B %d, %Y at %H:%M")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=inch, leftMargin=inch,
        topMargin=inch,  bottomMargin=inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitleS", parent=styles["Normal"], fontSize=22,
        textColor=colors.HexColor("#1F4E79"), alignment=TA_CENTER, spaceAfter=6, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("SubS", parent=styles["Normal"], fontSize=12,
        textColor=colors.HexColor("#2E75B6"), alignment=TA_CENTER, spaceAfter=4, fontName="Helvetica")
    body_style = ParagraphStyle("BodyS", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#333333"), fontName="Helvetica", leading=18)
    value_style = ParagraphStyle("ValS", parent=styles["Normal"], fontSize=13,
        textColor=colors.HexColor("#1A1A1A"), fontName="Helvetica-Bold", spaceAfter=6)
    footer_style = ParagraphStyle("FootS", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#AAAAAA"), alignment=TA_CENTER, fontName="Helvetica")

    story = []
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Welcome to the Team!", title_style))
    story.append(Paragraph("Employee Onboarding Summary", subtitle_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2E75B6")))
    story.append(Spacer(1, 0.3 * inch))

    detail_data = [
        ["Employee Name", name],
        ["Role",          role],
        ["Department",    department],
        ["Start Date",    datetime.now().strftime("%B %d, %Y")],
        ["Report ID",     f"ONB-{datetime.now().strftime('%Y%m%d%H%M%S')}"],
    ]
    detail_table = Table(detail_data, colWidths=[2.2 * inch, 4.3 * inch])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), colors.HexColor("#EEF4FB")),
        ("BACKGROUND",  (1, 0), (1, -1), colors.white),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR",   (1, 0), (1, -1), colors.HexColor("#1A1A1A")),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#EEF4FB"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING",     (0, 0), (-1, -1), 10),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.35 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Dear {name},", body_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        f"We are thrilled to welcome you to the <b>{department}</b> team as a <b>{role}</b>. "
        "Your onboarding process has been automatically initiated.", body_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Your next steps:", value_style))
    for step in [
        "HR will reach out within 24 hours with your IT setup details.",
        "Your team lead will schedule an orientation session for your first week.",
        "Please review and complete your onboarding checklist sent to your email.",
        "Your workspace and system access will be ready on your start date.",
    ]:
        story.append(Paragraph(f"  -  {step}", body_style))
        story.append(Spacer(1, 0.05 * inch))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2E75B6")))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        f"Generated automatically by Azure Pipelines  |  {generated}  |  Employee Onboarding Automation System",
        footer_style))
    doc.build(story)
    return output_path


def load_employee_json(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f)


@app.route("/")
def index():
    return jsonify({
        "service": "Employee Onboarding Automation System",
        "status": "running",
        "endpoints": {
            "generate": "POST /generate  — body: {name, role, department}",
            "report":   "GET  /report/<filename>"
        }
    })


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400
    missing = [f for f in ["name", "role", "department"] if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    safe_name   = data["name"].replace(" ", "_")
    output_path = os.path.join("reports", f"onboarding_{safe_name}.pdf")
    try:
        generate_pdf(data, output_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({
        "message": f"Onboarding report generated for {data['name']}",
        "report":  f"onboarding_{safe_name}.pdf"
    }), 201


@app.route("/report/<filename>")
def get_report(filename):
    path = os.path.join("reports", filename)
    if not os.path.exists(path):
        return jsonify({"error": "Report not found"}), 404
    return send_file(path, mimetype="application/pdf", as_attachment=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        employee = load_employee_json(sys.argv[1])
        safe     = employee.get("name", "output").replace(" ", "_")
        out      = os.path.join("reports", f"onboarding_{safe}.pdf")
        print(f"Report saved to: {generate_pdf(employee, out)}")
    else:
        print("Starting Flask server on http://localhost:5000")
        app.run(debug=True, host="0.0.0.0", port=5000)