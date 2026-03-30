"""
create_demo_sof.py
------------------
Run this once locally to generate the demo Statement of Facts PDF.
This PDF is what you upload on the website to trigger the real pipeline.

It contains real port call events from claim_id 5118 (Chevron, ABIDJAN).
The marker string DEMURRAGE-DEMO-CLAIM-5118 tells the backend to use
the real demo claim data.

Requirements:
    pip install reportlab

Output:
    demo_sof_chevron_abidjan.pdf  — upload this on the website
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
import datetime

OUTPUT_FILE = "demo_sof_chevron_abidjan.pdf"

EVENTS = [
    ("2025-05-10 06:30", "Vessel Arrived at Anchorage",                "vessel_arrived"),
    ("2025-05-10 07:00", "Notice of Readiness Tendered",               "nor_tendered"),
    ("2025-05-10 07:15", "Vessel Anchored — Waiting for Berth",        "anchored"),
    ("2025-05-10 07:15", "Waiting for Berth Commences",                "waiting_berth"),
    ("2025-05-10 19:00", "Vessel Berthed — Mooring Completed",         "mooring_start"),
    ("2025-05-10 19:30", "Gangway Down — Inspections Begin",           "gangway_down"),
    ("2025-05-10 20:00", "Hoses Connected — Ready to Discharge",       "hoses_connected"),
    ("2025-05-10 20:30", "Cargo Discharge Commenced",                  "cargo_start"),
    ("2025-05-11 02:00", "Cargo Operations Stopped — Shore Tank Full", "cargo_stopped"),
    ("2025-05-11 04:00", "Cargo Operations Resumed",                   "cargo_resumed"),
    ("2025-05-11 18:00", "Cargo Discharge Completed",                  "cargo_end"),
]


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Title ──────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    story.append(Paragraph("STATEMENT OF FACTS", title_style))
    story.append(Paragraph("Demurrage Claim — Demo Case", ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=11, alignment=TA_CENTER, textColor=colors.grey
    )))
    story.append(Spacer(1, 0.5*cm))

    # ── Header info ────────────────────────────────────────────────────────────
    header_data = [
        ["Vessel:",          "CHIOS",                  "Claim ID:",      "5118 (Demo)"],
        ["Port:",            "ABIDJAN, CÔTE D'IVOIRE", "Operation:",     "Discharge"],
        ["Company:",         "Chevron",                "Contract:",      "Chevron GTC 2014"],
        ["CP Date:",         "2025-05-01",             "Currency:",      "USD"],
        ["Allowed Laytime:", "36 hours SHINC",         "NOR Rule:",      "NOR + 6 hours"],
        ["Demurrage Rate:",  "USD 12,500/day pro rata", "Counting Rule:", "SHINC"],
    ]

    header_table = Table(header_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    header_table.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 0), (0, -1),  "Helvetica-Bold"),
        ("FONTNAME",      (2, 0), (2, -1),  "Helvetica-Bold"),
        ("TEXTCOLOR",     (0, 0), (-1, -1), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.HexColor("#f5f7fa"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.6*cm))

    # ── Events table ───────────────────────────────────────────────────────────
    story.append(Paragraph("PORT CALL EVENTS", ParagraphStyle(
        "SectionHead", parent=styles["Heading2"], fontSize=11, spaceAfter=6
    )))

    ev_header = [["#", "Timestamp", "Event Description", "Event Key"]]
    ev_rows   = [[str(i+1), ts, desc, key] for i, (ts, desc, key) in enumerate(EVENTS)]
    ev_data   = ev_header + ev_rows

    ev_table = Table(ev_data, colWidths=[0.8*cm, 3.8*cm, 9.0*cm, 3.5*cm])
    ev_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#0d1a2b")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("TEXTCOLOR",     (3, 1), (3, -1),  colors.HexColor("#0369a1")),
        ("FONTNAME",      (3, 1), (3, -1),  "Helvetica-Oblique"),
    ]))
    story.append(ev_table)
    story.append(Spacer(1, 0.6*cm))

    # ── Summary stats ──────────────────────────────────────────────────────────
    story.append(Paragraph("LAYTIME SUMMARY", ParagraphStyle(
        "SectionHead", parent=styles["Heading2"], fontSize=11, spaceAfter=6
    )))

    summary_data = [
        ["Calculated Amount:",       "USD 1,893,472.01"],
        ["Total Port Stay:",         "35.5 hours"],
        ["Wait to Berth:",           "12.5 hours (34.7% of allowed)"],
        ["Laytime Start (NOR+6h):",  "2025-05-10 13:00"],
        ["Counted Hours:",           "29.0 hours"],
        ["Allowed Laytime:",         "36.0 hours SHINC"],
        ["Laytime Used:",            "80.6% of allowed"],
        ["Total Events Recorded:",   "11"],
        ["Long Gap Ratio:",          "0.545 (54.5% of gaps > 4 hours)"],
        ["Events per Day:",          "7.5"],
    ]

    sum_table = Table(summary_data, colWidths=[6*cm, 11*cm])
    sum_table.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (0, -1),  "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1),  "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.HexColor("#f5f7fa"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 0.8*cm))

    # ── Footer with marker ─────────────────────────────────────────────────────
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#aaaaaa"),
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Demo Case — Real data from Chevron operational dataset | "
        f"DEMURRAGE-DEMO-CLAIM-5118",
        footer_style
    ))

    doc.build(story)
    print(f"✅ Demo SoF created: {OUTPUT_FILE}")
    print(f"   Upload this file on the website to trigger the real pipeline.")


if __name__ == "__main__":
    build_pdf()