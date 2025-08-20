# pdf_builder.py
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors, enums
from PIL import Image as PILImage

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCenter', fontSize=16, leading=20, alignment=enums.TA_CENTER))
styles.add(ParagraphStyle(name='SubTitle', fontSize=10, leading=12, alignment=enums.TA_CENTER, textColor=colors.gray))
styles.add(ParagraphStyle(name='Heading', fontSize=12, leading=14, spaceBefore=8, spaceAfter=6, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='Body', fontSize=10, leading=13))

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20 * mm
USABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN

def _scale_image(img_bytes, max_w=USABLE_WIDTH, max_h=120*mm):
    img = PILImage.open(io.BytesIO(img_bytes))
    w_px, h_px = img.size
    dpi = img.info.get('dpi', (72,72))[0] or 72
    w_pt = w_px * 72.0 / dpi
    h_pt = h_px * 72.0 / dpi
    scale = min(max_w / w_pt, max_h / h_pt, 1.0)
    return (w_pt * scale, h_pt * scale)

def _on_page(canvas, doc, header_title=None, logo_path=None):
    canvas.saveState()
    # Header title centered
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT - 20, header_title or "")
    # footer page number
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(PAGE_WIDTH/2.0, 15*mm, f"Page {doc.page}")
    canvas.restoreState()

def build_eventreport_pdf(report, event=None, images=None, header_title=None, logo_path=None):
    """
    report: EventReport instance
    event: optional Event instance (report.event is available)
    images: optional list of EventReportImage instances (otherwise read report.images.all())
    returns: bytes of PDF
    """
    if event is None:
        event = getattr(report, 'event', None)
    if images is None:
        images = list(report.images.all())

    buffer = io.BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=40, bottomMargin=30)
    frame = Frame(MARGIN, MARGIN, PAGE_WIDTH - 2*MARGIN, PAGE_HEIGHT - 2*MARGIN - 20*mm, id='normal')
    template = PageTemplate(id='report', frames=[frame], onPage=lambda c, d: _on_page(c, d, header_title=header_title or f"Report — {event.title}", logo_path=logo_path))
    doc.addPageTemplates([template])

    elements = []
    # Cover / Title
    elements.append(Paragraph(f"Event Report — {event.title}", styles['TitleCenter']))
    if hasattr(event, 'start') and event.start:
        elements.append(Paragraph(f"Date: {event.start.strftime('%Y-%m-%d %H:%M')}", styles['SubTitle']))
    elements.append(Spacer(1, 8))

    # Basic event metadata table
    meta = [
        ['Event title', event.title],
        ['Status', getattr(event, 'status', '')],
        ['Partner', getattr(event, 'partner', '')],
        ['Persona', str(getattr(event, 'persona', ''))],
        ['Kollege', str(getattr(event, 'kollege', ''))],
    ]
    table = Table(meta, colWidths=[60*mm, USABLE_WIDTH - 60*mm])
    table.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LINEBEFORE',(0,0),(0,-1),0.25,colors.gray),
        ('LINEAFTER',(0,0),(-1,0),0.5,colors.gray),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10))

    # ReportReport text fields summary (you can include selected EventReport fields)
    elements.append(Paragraph("<b>Report Details</b>", styles['Heading']))
    if getattr(report, 'genericDescription', None):
        elements.append(Paragraph(report.genericDescription, styles['Body']))
    # Add other fields as needed (conc1..conc6 etc.)
    elements.append(Spacer(1, 10))

    # Images section
    if images:
        elements.append(Paragraph("<b>Images</b>", styles['Heading']))
        for img_obj in images:
            try:
                f = img_obj.image_file
                f.open('rb')
                data = f.read()
                f.close()
                w, h = _scale_image(data)
                rl_img = RLImage(io.BytesIO(data), width=w, height=h)
                rl_img.hAlign = 'CENTER'
                caption = Paragraph(img_obj.caption or '', styles['Body'])
                elements.append(KeepTogether([rl_img, Spacer(1,4), caption, Spacer(1,8)]))
            except Exception:
                elements.append(Paragraph(f"Unable to include image {getattr(img_obj, 'pk', '')}", styles['Body']))

    # Conclusion
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>Conclusion</b>", styles['Heading']))
    elements.append(Paragraph("This report was generated automatically. Check attached images and metadata for details.", styles['Body']))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes