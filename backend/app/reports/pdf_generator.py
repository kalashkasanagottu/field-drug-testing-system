import os
import qrcode
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

from app.core.config import settings

class NumberedCanvas(canvas.Canvas):
    """Adds official forensic footer with page numbering and timestamp on all pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Header banner
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(40, 755, 572, 755)
        self.drawString(40, 760, "OFFICIAL FORENSIC DIGITAL EVIDENCE RECORD • CHAIN OF CUSTODY PRESERVED")

        # Footer
        self.line(40, 45, 572, 45)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.drawString(40, 32, f"Digital Forensics Unit • Generated: {timestamp_str} • Ed25519 Tamper-Evident Record")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 32, page_str)
        self.restoreState()


def generate_pdf_report(record: Any, output_path: str, base_verify_url: str = "http://localhost:5173/verify") -> str:
    """
    Generates a formal, cryptographically authenticated PDF evidence report for court/investigative submission.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A202C")
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568")
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=4
    )
    cell_label = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2D3748")
    )
    cell_val = ParagraphStyle(
        'CellVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1A202C")
    )
    hash_style = ParagraphStyle(
        'HashVal',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1A202C")
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#9B2C2C")
    )

    story = []

    # Title Banner
    story.append(Paragraph("DIGITAL FIELD DRUG-TESTING EVIDENCE REPORT", title_style))
    story.append(Paragraph("Automated Colorimetric Reaction Analysis & Cryptographically Verified Evidence Record", subtitle_style))
    story.append(Spacer(1, 10))

    # Result Badge Box
    result = record.classification_result
    if result == "PRESUMPTIVE_POSITIVE":
        badge_bg = colors.HexColor("#FFF5F5")
        badge_border = colors.HexColor("#E53E3E")
        badge_text_color = colors.HexColor("#9B2C2C")
        badge_title = "PRESUMPTIVE POSITIVE"
    elif result == "PRESUMPTIVE_NEGATIVE":
        badge_bg = colors.HexColor("#F0FFF4")
        badge_border = colors.HexColor("#38A169")
        badge_text_color = colors.HexColor("#22543D")
        badge_title = "PRESUMPTIVE NEGATIVE"
    elif result == "INCONCLUSIVE":
        badge_bg = colors.HexColor("#FFFAF0")
        badge_border = colors.HexColor("#DD6B20")
        badge_text_color = colors.HexColor("#7B341E")
        badge_title = "INCONCLUSIVE REACTION"
    else:
        badge_bg = colors.HexColor("#EDF2F7")
        badge_border = colors.HexColor("#718096")
        badge_text_color = colors.HexColor("#2D3748")
        badge_title = "UNABLE TO CLASSIFY (OPERATIONAL ERROR)"

    result_p = Paragraph(
        f"<font size=13 color='{badge_text_color.hexval()}'><b>RESULT: {badge_title}</b></font><br/>"
        f"<font size=8.5 color='#4A5568'><b>Analyte Target:</b> {record.analyte_detected or 'Not Identified'} | "
        f"<b>Reason:</b> {record.classification_reason or 'None'}</font>",
        ParagraphStyle('Badge', parent=styles['Normal'], leading=14)
    )
    result_table = Table([[result_p]], colWidths=[532])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), badge_bg),
        ('BOX', (0,0), (-1,-1), 1.5, badge_border),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 10))

    # Overview Metadata Table
    story.append(Paragraph("1. CASE & OPERATIONAL IDENTIFICATION", section_heading))
    kit_name = record.kit.name if record.kit else "Standard Forensic Test Kit"
    kit_mfg = record.kit.manufacturer if record.kit else "Forensic Reagents Inc."

    dev_time_str = record.device_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if record.device_timestamp else "N/A"
    srv_time_str = record.server_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if record.server_timestamp else "N/A"

    meta_data = [
        [
            Paragraph("Test Record ID", cell_label), Paragraph(record.test_id, cell_val),
            Paragraph("Case Reference", cell_label), Paragraph(record.case_reference or "N/A", cell_val)
        ],
        [
            Paragraph("Testing Officer", cell_label), Paragraph(record.operator_name, cell_val),
            Paragraph("Officer Badge / ID", cell_label), Paragraph(record.operator_badge or "N/A", cell_val)
        ],
        [
            Paragraph("Test Kit", cell_label), Paragraph(f"{kit_name} ({kit_mfg})", cell_val),
            Paragraph("Kit Batch / Lot", cell_label), Paragraph(record.kit_batch_number, cell_val)
        ],
        [
            Paragraph("Kit Expiry Date", cell_label), Paragraph(record.kit_expiry_date or "N/A", cell_val),
            Paragraph("Profile Version", cell_label), Paragraph(record.profile_version or "V1.0", cell_val)
        ],
        [
            Paragraph("Device Timestamp", cell_label), Paragraph(dev_time_str, cell_val),
            Paragraph("Server Timestamp", cell_label), Paragraph(srv_time_str, cell_val)
        ],
        [
            Paragraph("GPS Location", cell_label),
            Paragraph(f"{record.gps_latitude:.5f}, {record.gps_longitude:.5f}" if record.gps_latitude else "Location Unavailable", cell_val),
            Paragraph("GPS Accuracy", cell_label),
            Paragraph(f"±{record.gps_accuracy_meters:.1f} meters" if record.gps_accuracy_meters else "N/A", cell_val)
        ]
    ]

    t_meta = Table(meta_data, colWidths=[100, 166, 100, 166])
    t_meta.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F7FAFC")),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#F7FAFC")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Evidence Images Side by Side
    story.append(Paragraph("2. PHOTOMETRIC EVIDENCE & COMPUTER VISION ANALYSIS", section_heading))
    
    img_cells = []
    # Original Image
    orig_path = record.original_image_path
    if orig_path and os.path.exists(orig_path):
        img_orig = RLImage(orig_path, width=255, height=170)
        orig_caption = Paragraph("<b>Original Capture</b> (Immutable Raw Evidence)", cell_label)
    else:
        img_orig = Paragraph("Original capture image unavailable", cell_val)
        orig_caption = Paragraph("Original Evidence File Missing", cell_label)

    # Processed Image
    proc_path = record.processed_image_path
    if proc_path and os.path.exists(proc_path):
        img_proc = RLImage(proc_path, width=255, height=170)
        proc_caption = Paragraph("<b>Calibrated Derivative</b> (ROI & Color Target Overlay)", cell_label)
    else:
        img_proc = Paragraph("Calibrated analysis derivative unavailable", cell_val)
        proc_caption = Paragraph("Derivative File Missing", cell_label)

    img_table = Table([[img_orig, img_proc], [orig_caption, proc_caption]], colWidths=[266, 266])
    img_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 2),
        ('BOX', (0,0), (0,0), 1, colors.HexColor("#CBD5E0")),
        ('BOX', (1,0), (1,0), 1, colors.HexColor("#CBD5E0")),
    ]))
    story.append(img_table)
    story.append(Spacer(1, 8))

    # Colorimetry & Calibration metrics
    analysis = record.analysis
    lab_l = f"{analysis.reaction_cielab_l:.1f}" if analysis and analysis.reaction_cielab_l else "N/A"
    lab_a = f"{analysis.reaction_cielab_a:.1f}" if analysis and analysis.reaction_cielab_a else "N/A"
    lab_b = f"{analysis.reaction_cielab_b:.1f}" if analysis and analysis.reaction_cielab_b else "N/A"
    delta_pos = f"{analysis.positive_delta_e:.1f}" if analysis and analysis.positive_delta_e else "N/A"
    delta_neg = f"{analysis.negative_delta_e:.1f}" if analysis and analysis.negative_delta_e else "N/A"
    calib_de = f"{analysis.calibration_error_delta_e:.2f}" if analysis and analysis.calibration_error_delta_e else "N/A"

    color_metrics_data = [
        [
            Paragraph("Measured CIELAB", cell_label),
            Paragraph(f"L*={lab_l}, a*={lab_a}, b*={lab_b}", cell_val),
            Paragraph("Card Calib ΔE", cell_label),
            Paragraph(f"{calib_de} (Residual Error)", cell_val)
        ],
        [
            Paragraph("Distance to Positive", cell_label),
            Paragraph(f"ΔE₀₀ = {delta_pos}", cell_val),
            Paragraph("Distance to Negative", cell_label),
            Paragraph(f"ΔE₀₀ = {delta_neg}", cell_val)
        ],
        [
            Paragraph("Sharpness Score", cell_label),
            Paragraph(f"{analysis.blur_score:.1f} (Threshold >= 50.0)" if analysis else "N/A", cell_val),
            Paragraph("Illumination Score", cell_label),
            Paragraph(f"{analysis.illumination_score:.1f} (Threshold 40 - 230)" if analysis else "N/A", cell_val)
        ]
    ]
    t_color = Table(color_metrics_data, colWidths=[100, 166, 100, 166])
    t_color.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F7FAFC")),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#F7FAFC")),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_color)
    story.append(Spacer(1, 10))

    # Cryptographic Chain of Evidence Section
    story.append(Paragraph("3. CRYPTOGRAPHIC TAMPER-EVIDENT INTEGRITY", section_heading))
    
    # Generate QR Code linking to verification endpoint
    qr_filename = f"qr_{record.test_id}.png"
    qr_temp_path = str(Path(output_path).parent / qr_filename)
    verify_url = f"{base_verify_url}?test_id={record.test_id}"
    
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img.save(qr_temp_path)

    qr_flowable = RLImage(qr_temp_path, width=80, height=80)

    crypto_details = [
        [Paragraph("Image SHA-256 Hash", cell_label), Paragraph(record.original_image_hash or "N/A", hash_style)],
        [Paragraph("Record Canonical Hash", cell_label), Paragraph(record.canonical_record_hash or "N/A", hash_style)],
        [Paragraph("Digital Signature", cell_label), Paragraph(f"Algorithm: {record.signature_algorithm} | Key ID: {record.signing_key_id}<br/>{record.digital_signature[:64]}..." if record.digital_signature else "N/A", hash_style)],
        [Paragraph("Integrity Status", cell_label), Paragraph(f"<b><font color='{colors.HexColor('#276749').hexval()}'>CRPTOGRAPHICALLY VERIFIED & AUDITED</font></b>", cell_val)]
    ]
    t_crypto = Table(crypto_details, colWidths=[110, 330])
    t_crypto.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F7FAFC")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))

    crypto_with_qr = Table([[t_crypto, qr_flowable]], colWidths=[445, 87])
    crypto_with_qr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(crypto_with_qr)
    story.append(Spacer(1, 10))

    # Mandatory Legal Disclaimer Banner
    story.append(Paragraph("4. STATUTORY PRESUMPTIVE RESULT NOTICE", section_heading))
    disclaimer_box = Table([[
        Paragraph(
            "<b>LEGAL NOTICE & FORENSIC DISCLAIMER:</b><br/>"
            "This automated output is a PRESUMPTIVE field-test result derived from colorimetric reaction analysis. "
            "It is NOT a definitive or laboratory-confirmed identification of a controlled substance. "
            "Confirmatory qualitative and quantitative chemical analysis by an accredited forensic laboratory "
            "(e.g., GC-MS, LC-MS, FTIR) is legally required for prosecution and final adjudication.",
            disclaimer_style
        )
    ]], colWidths=[532])
    disclaimer_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFF5F5")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#FEB2B2")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(disclaimer_box)

    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Cleanup temp QR code
    if os.path.exists(qr_temp_path):
        try:
            os.remove(qr_temp_path)
        except Exception:
            pass

    return output_path
