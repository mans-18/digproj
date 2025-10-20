import datetime
import io
import os
from typing import Iterable, Optional, List, Tuple
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import localtime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage

from core.models import EventReport, TemporaryImage

def _pt(v_mm: float) -> float:
    return v_mm * mm

def _fmt_date(dt) -> str:
    if not dt:
        return ""
    # dd/MM/yyyy
    dt = localtime(dt)
    return dt.strftime("<b>%d/%m/%Y %H:%M</b>")+' '+'<b>h</b>'

def _clean(text: Optional[str]) -> str:
    return (text or "").strip()

def _upper(text: Optional[str]) -> str:
    return _clean(text).upper()

############# A dedicated gallery..docx ###################
def _image_from_path_or_field(local_path: str = None, storage_field = None, max_w=200, max_h=150) -> Optional[RLImage]:
    """
    Creates a ReportLab Image from a Django FileField stored on S3/local.
    Works without relying on .path (which S3 doesn't provide).
    """
    try:
        if local_path and os.path.exists(local_path):
            pil = PILImage.open(local_path).convert("RGB")
        elif storage_field:
            with storage_field.open("rb") as f:
                pil = PILImage.open(f).convert("RGB")
        else:
            return None

        pil.thumbnail((max_w, max_h), PILImage.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        img = RLImage(buf, width=pil.width, height=pil.height)
        img.hAlign = 'CENTER'
        return img
    except Exception:
        return None
############################

def _image_from_storage_field_ORI(storage_field, max_w=200, max_h=150) -> Optional[RLImage]:
    """
    Creates a ReportLab Image from a Django FileField stored on S3/local.
    Works without relying on .path (which S3 doesn't provide).
    """
    if not storage_field:
        return None
    try:
        with storage_field.open("rb") as f:
            pil = PILImage.open(f).convert("RGB")
            pil.thumbnail((max_w, max_h), PILImage.LANCZOS)
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=92)
            buf.seek(0)
            img = RLImage(buf, width=pil.width, height=pil.height)
            img.hAlign = 'CENTER'
            return img
    except Exception:
        return None

def _horizontal_rule(width=A4[0]-_pt(18)) -> Table:
    t = Table([[ " " ]], colWidths=[width])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING',(0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    return t

def _horizontal_rule_for_signature(width=A4[0]-_pt(140)) -> Table:
    t = Table([[ " " ]], colWidths=[width])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING',(0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    return t

def _signature_block(doctor_name: str, crm: str, signed_by: Optional[str]=None, signature_image=None) -> List:
    story = []
    story.append(_horizontal_rule_for_signature())
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1))
    if signature_image:
        sig = _image_from_storage_field(signature_image, max_w=180, max_h=60)
        if sig: story.append(sig)
    story.append(Paragraph(f"<b>{_clean(doctor_name)} - CRM {_clean(crm)}</b>", styles["Center"]))
    if signed_by:
        story.append(Paragraph(f"Liberado por: {_clean(signed_by)}", styles["Center"]))
    return story




def _static_logo(path="static/logo_circle.png", max_w=65, max_h=65):
    """
    Load logo from Django static folder for ReportLab.
    """
    # Build absolute path to file inside STATICFILES_DIRS/STATIC_ROOT
    logo_path = os.path.join(settings.BASE_DIR, path)

    try:
        img = RLImage(logo_path, width=max_w, height=max_h)
        img.hAlign = "LEFT"
        return img
    except Exception as e:
        print("Logo not found:", e)
        return ""


def _header_block(title: str, dt, address: str, phone: str, logo_image=None, doc_width=None) -> List:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleCenter', parent=styles['Title'], alignment=1, fontSize=18, spaceAfter=6
    )
    normal_center = ParagraphStyle('NormalCenter', parent=styles['Normal'], alignment=1)
    minor_center = ParagraphStyle('MinorCenter', parent=styles['Normal'], alignment=1, fontSize=8, leading=1.5*mm)
    minor_right = ParagraphStyle('MinorRight', parent=styles['Normal'], alignment=2, fontSize=8, leading=10)
    # Sets the spsce between lines
    #minor_center.leading = 1.5 * mm
    print("💥", doc_width)
    if doc_width is None:
            # fallback: full page width minus some default margins
            doc_width = A4[0] - _pt(25) - _pt(15)  # left 25mm, right 15mm

    # Left: logo
    #left = _image_from_storage_field(logo_image, max_w=90, max_h=80) if logo_image else ""
    left = _static_logo("static/logo_circle.png", max_w=65, max_h=65)
    # Center: title
    #center = Paragraph(title, title_style)


    center = Paragraph(title, title_style)#ParagraphStyle('TitleCenter', alignment=1, fontSize=18))
    right = Paragraph(
        f"<b>Data:</b> {_fmt_date(dt)}<br/>"
        f"{address}<br/>"
        f"{phone}",
        minor_right#ParagraphStyle('RightInfo', alignment=2, fontSize=8)
    )

    center = Paragraph(title, title_style)
    right_content = [
    Paragraph(f"<b>Data:</b> {_fmt_date(dt)}", normal_center),
    Paragraph(address, minor_center),
    Paragraph(phone, minor_center),
    ]

    # Column widths
    left_col_w = 70
    right_col_w = 140
    center_col_w = doc_width - left_col_w - right_col_w

    right = Table([[c] for c in right_content], hAlign='RIGHT')

    table = Table([[left, center, right]],
                  colWidths=[left_col_w, center_col_w, right_col_w])

    '''
    # Right: stack info into a single Paragraph
    right_text = (
        f"<b>Data:</b> {_fmt_date(dt)}<br/>"
        f"{address}<br/>"
        f"{phone}"
    )
    right = Paragraph(right_text, minor_right)

    # Header table
    table = Table(
        [[left, center, right]],
        colWidths=[_pt(30), A4[0] - _pt(90), _pt(50)]
    )
    '''
    
    table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),   # vertical center ALL cells
        ('ALIGN', (0,0), (0,0), 'LEFT'),        # logo left
        ('ALIGN', (1,0), (1,0), 'CENTER'),      # title center
        ('ALIGN', (2,0), (2,0), 'RIGHT'),       # right block right
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING',(0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))

    # Return header + line + spacing
    return [table, _horizontal_rule(), Spacer(1, 8)]


def _block_heading(text: str) -> Paragraph:
    styles = getSampleStyleSheet()
    heading = ParagraphStyle('BlockHeading', parent=styles['Heading3'], spaceBefore=10, spaceAfter=6)
    return Paragraph(f"<b>{text}</b>", heading)

def _paragraph(text: str) -> Paragraph:
    return Paragraph(_clean(text).replace("\n", "<br/>") or "&nbsp;", getSampleStyleSheet()['Normal'])

def _images_row(images: Iterable, per_row=3, max_w=200, max_h=150) -> List:
    row: List[List] = []
    buf: List = []
    for img_field in images:
        pic = _image_from_path_or_field(img_field, max_w=max_w, max_h=max_h)
        #pic = _image_from_storage_field(img_field, max_w=max_w, max_h=max_h)
        buf.append(pic or "")
        if len(buf) == per_row:
            row.append(buf)
            buf = []
    if buf:
        # pad to keep grid consistent
        while len(buf) < per_row: buf.append("")
        row.append(buf)
    if not row:
        return []
    t = Table(row, colWidths=[(A4[0]-_pt(30))/per_row]*per_row, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    return [t]
# testing
def download_report(request, report_id):
    '''
    event_report = EventReport.objects.get(pk=report_id)
    print('event##########report',event_report.esop)
    pdf_bytes = build_pdf_for_eventreport(event_report)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=report.pdf"
    return response
    '''
    event_report = EventReport.objects.get(pk=report_id)
    pdf_bytes = build_pdf_for_eventreport(event_report)
    return HttpResponse(
        pdf_bytes,
        content_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="event_{event_report.pk}_report.pdf"'}
)


import os, io
import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.html import escape
from reportlab.lib.utils import ImageReader


def _image_from_path_or_field(local_path: str = None, storage_field=None, max_w=250, max_h=200):
    """
    Create a ReportLab Image from a local file or a Django FileField.
    Local file takes priority.
    """
    print('local_path in _image from', local_path)
    try:
        if local_path and os.path.exists(local_path):
            pil = PILImage.open(local_path).convert("RGB")
            print('local_path in _image from inside try', local_path)
            print('pil in _image from', pil)
        elif storage_field:
            print('storage_field in ' \
            '_image from', storage_field)
            with storage_field.open("rb") as f:
                pil = PILImage.open(f).convert("RGB")
        else:
            return None

        pil.thumbnail((max_w, max_h), PILImage.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        img = RLImage(buf, width=pil.width, height=pil.height)
        img.hAlign = 'CENTER'
        return img
    except Exception:
        return None




from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.pagesizes import A4

def _images_grid_with_captions(images_qs, per_row=2, max_w=250, max_h=200):
    """
    Build a list of Flowables for a grid of images with captions and comments.
    images_qs: queryset of TemporaryImage
    per_row: images per row
    """

    story: List = []
    buf_row: List = []
    caption_row: List = []

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    # 🆕 Style for the comment text
    comment_style = ParagraphStyle(
        'Comment',
        parent=normal_style,
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=colors.grey,
        spaceBefore=2,
    )

    for temp_img in images_qs:
        #print('images_qs in _images_grid_with_captions', images_qs, images_qs[0])
        img = _image_from_path_or_field(
            local_path=temp_img.local_path,
            storage_field=temp_img.image_file,
            max_w=max_w,
            max_h=max_h
        )
        #print('temp_img.local_path at _images_grid_with_captions', temp_img.local_path)
        if not img:
            continue

        # Build caption paragraph
        caption_para = Paragraph(_clean(temp_img.caption), normal_style) if temp_img.caption else Paragraph("&nbsp;", normal_style)

        # 🆕 Build comment paragraph (below caption)
        comment_para = Paragraph(_clean(temp_img.comment), comment_style) if getattr(temp_img, 'comment', None) else Paragraph("&nbsp;", comment_style)

        # 🆕 Combine caption and comment vertically in one cell
        combined_text = [caption_para, comment_para]

        buf_row.append(img)
        caption_row.append(combined_text)

        if len(buf_row) == per_row:
            # Add image row + caption/comment row
            t = Table(
                [buf_row, caption_row],
                colWidths=[(A4[0] - _pt(30)) / per_row] * per_row
            )
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                # This padding allows 3 rows with caption/comments in a page.
                # The ori pad was 6; put the cap/comments of the last images of a page to the next page
                ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ]))

            story.append(t)
            story.append(Spacer(1, 12))

            buf_row = []
            caption_row = []

    # Add remaining images if any
    if buf_row:
        while len(buf_row) < per_row:
            buf_row.append("")  # empty cell
            caption_row.append([Paragraph("&nbsp;", normal_style), Paragraph("&nbsp;", comment_style)])

        t = Table(
            [buf_row, caption_row],
            colWidths=[(A4[0] - _pt(30)) / per_row] * per_row
        )
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    return story


def _images_gallery_page(images_qs):
    """
    Build a new PDF page with selected images and captions/comments in a grid.
    """
    story: List = []

    story.append(PageBreak())
    story.append(_block_heading("Galeria de Imagens"))
    story += _images_grid_with_captions(images_qs, per_row=2, max_w=250, max_h=200)

    return story



'''
def _images_grid_with_captions(images_qs, per_row=2, max_w=250, max_h=200):
    """
    Build a list of Flowables for a grid of images with captions.
    images_qs: queryset of TemporaryImage
    per_row: images per row
    """
    
    story: List = []
    buf_row: List = []
    caption_row: List = []

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    for temp_img in images_qs:
        print('images_qs in _images_grid_with_captions',images_qs, images_qs[0])
        img = _image_from_path_or_field(local_path=temp_img.local_path, storage_field=temp_img.image_file, max_w=max_w, max_h=max_h)
        print('temp_im.local_path at _images_grid_with_cap', temp_img.local_path)
        if not img:
            continue

        buf_row.append(img)
        caption_row.append(Paragraph(_clean(temp_img.caption), normal_style) if temp_img.caption else Paragraph("&nbsp;", normal_style))

        if len(buf_row) == per_row:
            # Add image row
            t = Table([buf_row, caption_row], colWidths=[(A4[0]-_pt(30))/per_row]*per_row)
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            
            story.append(t)
            story.append(Spacer(1, 12))

            buf_row = []
            caption_row = []

    # Add remaining images if any
    if buf_row:
        while len(buf_row) < per_row:
            buf_row.append("")          # empty cell
            caption_row.append(Paragraph("&nbsp;", normal_style))
        t = Table([buf_row, caption_row], colWidths=[(A4[0]-_pt(30))/per_row]*per_row)
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))
     
    return story
'''


def _images_gallery_page(images_qs):
    """
    Build a new PDF page with selected images and captions in a grid.
    """
    story: List = []

    story.append(PageBreak())
    story.append(_block_heading("Galeria de Imagens"))
    story += _images_grid_with_captions(images_qs, per_row=2, max_w=250, max_h=200)

    return story


### Not getting the selected images in the tempkate (selectedIds). Look for selectedIds in EventReports:
########## event_report.event.images.filter(pk__in=selectedIds)

def build_pdf_for_eventreport(event_report, *, selected_images=None, logo_image_field=None,
                              signature_image_field=None, current_user_name=None) -> bytes:
    """
    Generate a PDF for an EventReport and return raw bytes.
    """
    #from core.models import EventImage  # in case you need image objects

    # Decide which images to include in gallery
    #print('selected images', selected_images)
    if selected_images is None:
        # This is an EventReportImage reached from event (event_report.event) by the related-name "images"
        images_qs = event_report.event.images.all().order_by("uploaded_at")
    else:
        images_qs = event_report.event.images.filter(pk__in=selected_images).order_by("uploaded_at")
    
    '''
    if selectedIds is None:
        images_qs = event_report.event.images.all().order_by("uploaded_at")
    else:
        images_qs = event_report.event.images.filter(pk__in=selectedIds).order_by("uploaded_at")
    '''

    #################
    #images_from_local = TemporaryImage.objects.filter(id__in=[selected_images])

    #print('images_qs at build_pdf_for_evreport', images_qs)
    #print('images_qs at build_pdf_for_evreport', images_qs[0].event.persona.name)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=25, rightMargin=15,
        topMargin=15, bottomMargin=18
    )

    start = event_report.event.start

    if event_report.event.start:
        formatted_date = event_report.event.start.strftime("%d/%m/%Y %H:%M")+' '+'h'
    else:
        formatted_date = ""
    
    if event_report.event.persona.name:
        capName = event_report.event.persona.name.title()#upper()#capitalize()
    else:
        capName = ""

    styles = getSampleStyleSheet()

    # Build main story
    story = []

    desc_style = ParagraphStyle(
        'DescStyle',
        parent=styles['Normal'],
        spaceAfter=6  # 6 points of space after each paragraph
    )

    # --- Header ---
    #story.append(Paragraph(f"<b>{escape(event_report.event.title)}</b>", styles['Title']))
    #story.append(Spacer(1, 12))
    #dt=datetime.strptime(event_report.event.start.replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), '%Y-%m-%dT%H:%M:%SZ'),

    # Header
    title_map = {'eda': "Endoscopia Digestiva Alta", 'colono': "Colonoscopia"}
    title = title_map.get((_clean(event_report.event.title)).lower(), _upper(event_report.event.title))
    story += _header_block(
        title=title,
        dt=event_report.event.start,
        address="R. Ant. Augusto 1270, Fortaleza",
        phone="(85) 3224-1547 ou 99628-8800",
        logo_image=logo_image_field,
        doc_width=doc.width
    )

    # --- Patient info ---
    heading2_with_space = ParagraphStyle(
    'Heading2WithSpace',
    parent=styles['Heading2'],
    spaceAfter=1  # space in points (e.g., 12pt ≈ one line)
)
    story.append(Paragraph(f"<b>Paciente:</b> {escape(capName)}", heading2_with_space))
    story.append(Paragraph(f"Solicitante: {escape(event_report.assistant or '')}", styles['Normal']))
    story.append(Paragraph(f"Medicações: {escape(event_report.drugs or '')}", styles['Normal']))
    story.append(Paragraph(f"Indicação: {escape(event_report.indication or '')}", styles['Normal']))
    #story.append(Paragraph(f"<b>Data:</b> {escape(formatted_date or '')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # --- Description ---

    story.append(Paragraph("<b>Descrição:</b>", styles['Heading3']))
    # Pair each label with the corresponding value
    desc_items = [
        ("Faringe: ", event_report.phar),
        ("Esôfago: ", event_report.esop),
        ("Estômago: ", event_report.stom),
        ("Duodeno: ", event_report.duod),
        ("",event_report.colo),
    ]

    for label, desc in desc_items:
        if desc:
            story.append(
                Paragraph(f"<b>{label}</b> {escape(desc)}", desc_style)#styles['Normal'])
            )
    story.append(Spacer(1, 12))


    # --- Images (optional) ---
    if selected_images is None:
        images = event_report.event.images.all().order_by('-uploaded_at')
    else:
        images = event_report.event.images.filter(pk__in=selected_images).order_by('uploaded_at')

    for im in images:
        try:
            img_path = im.image_file.path  # or .url if stored in S3
            story.append(Image(img_path, width=80, height=70))
            story.append(Spacer(1, 6))
        except Exception:
            continue  # skip broken images

    # --- Conclusions ---
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Conclusões:</b>", styles['Heading2']))
    for c in [event_report.conc1, event_report.conc2, event_report.conc3,
              event_report.conc4, event_report.conc5, event_report.conc6]:
        if c:
            story.append(Paragraph(escape(c), styles['Heading3']))

    # Extra lines
    if (_clean(event_report.event.title).lower() == 'eda'):
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Teste da urease:</b> {_clean(event_report.urease)}", styles['Normal']))
    if _clean(event_report.biopsy):
        story.append(Paragraph(f"<b>Biópsias:</b> {_clean(event_report.biopsy)}", styles['Normal']))


    # --- Sign ---
    '''
    story.append(Spacer(1, 28))
    story.append(Paragraph(f"_________________________________________"))
    story.append(Paragraph(f"<b>Dr(a): </b>{event_report.event.kollege.name}", styles['Heading4']))
    story.append(Paragraph(f"<b>CRM: </b>{event_report.event.kollege.crm}", styles['Heading4']))
    '''


    # Images grid
    #imgs = [im.image_file for im in images]
    #story += _images_row(imgs, per_row=3, max_w=200, max_h=150)

    # Conclusions
    '''
    story.append(_block_heading("Conclusão(ões)"))
    for c in [event_report.conc1, event_report.conc2, event_report.conc3,
              event_report.conc4, event_report.conc5, event_report.conc6]:
        if _clean(c):
            story.append(Paragraph(_upper(c), styles['Normal']))
    '''
    # Signature
    story.append(Spacer(1, 18))
    story += _signature_block(
        doctor_name=event_report.event.kollege.name,
        crm=event_report.event.kollege.crm,
        signed_by=current_user_name,
        signature_image=signature_image_field
    )

    # Add gallery page at the end
    ############################
 #   if (images_from_local):
   #     print('images from local', images_from_local)
    #    story += _images_gallery_page(images_from_local)
  #  else:
    story += _images_gallery_page(images_qs)

    # --- Footer function ---
    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        date_s = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        canvas.drawRightString(A4[0]-15, 10, f"Emitido em {date_s}  ·  Página {doc_.page}")
        #canvas.drawRightString(A4[0]-300, 14, f"Assinado por: Dr(a): {event_report.event.kollege.name}, CRM: {event_report.event.kollege.crm}")
        canvas.drawRightString(A4[0]-15, 20, f"{event_report.event.persona.name}")        
        canvas.restoreState()

    # Build PDF
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _build_pdf_for_eventreport(event_report, *, selected_images=None, logo_image_field=None,
                              signature_image_field=None, current_user_name=None) -> bytes:
    """
    Render an A4 report resembling the Angular layouts:
    - EDA (title == 'eda'): Esôfago/Estômago/Duodeno sections + urease/biopsy
    - Colonoscopia (title == 'colono'): Descrição (colo) + biópsias
    """
    event = event_report.event
    persona = event.persona
    kollege = event.kollege

    # Decide which images to include
    if selected_images is None:
        # default: use all event images (you can change to only first 3, etc.)
        selected_qs = event.images.all().order_by("-uploaded_at")
    else:
        selected_qs = event.images.filter(pk__in=selected_images).order_by("uploaded_at")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=_pt(15), rightMargin=_pt(15),
        topMargin=_pt(15), bottomMargin=_pt(18)
    )
    styles = getSampleStyleSheet()
    story: List = []

    # Header
    title_map = {
        'eda': "Endoscopia Digestiva Alta",
        'colono': "Colonoscopia",
    }
    title = title_map.get((_clean(event.title)).lower(), _upper(event.title))
    story += _header_block(
        title=title,
        dt=event.start,
        address="R. Ant. Augusto 1270, Fortaleza",
        phone="(85) 3224-1547 ou 99628-8800",
        logo_image=logo_image_field
    )

    # Patient/meta
    story.append(_patient_meta_block(
        per_name=persona.name,
        assistant=event_report.assistant,
        anest=event_report.anest,
        drugs=event_report.drugs,
        equipment=event_report.equipment,
        indication=event_report.indication
    ))

    # Description heading
    story.append(_block_heading("Descrição"))
    if (_clean(event.title).lower() == 'eda'):
        story.append(_paragraph("Monitorização do ritmo cardíaco e oximetria de pulso"))
        story.append(_block_heading("Esôfago"))
        eso = " ".join(filter(None, [_clean(event_report.phar), _clean(event_report.esop)]))
        story.append(_paragraph(eso))
        story.append(_block_heading("Estômago"))
        story.append(_paragraph(event_report.stom))
        story.append(_block_heading("Duodeno/Jejuno"))
        story.append(_paragraph(event_report.duod))
    elif (_clean(event.title).lower() == 'colono'):
        story.append(_paragraph("Monitorização do ritmo cardíaco e oximetria de pulso"))
        story.append(_block_heading("Descrição do exame"))
        story.append(_paragraph(event_report.colo))
    else:
        # generic block if other titles appear
        story.append(_paragraph(event_report.genericDescription or ""))

    # Images grid
    imgs = [im.image_file for im in selected_qs]
    story += _images_row(imgs, per_row=2, max_w=250, max_h=200)

    # Conclusions
    story.append(_block_heading("Conclusão(ões)"))
    for c in [event_report.conc1, event_report.conc2, event_report.conc3,
              event_report.conc4, event_report.conc5, event_report.conc6]:
        if _clean(c):
            story.append(Paragraph(_upper(c), styles['Normal']))

    # Extra lines
    if (_clean(event.title).lower() == 'eda'):
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Teste da urease:</b> {_clean(event_report.urease)}", styles['Normal']))
    if _clean(event_report.biopsy):
        story.append(Paragraph(f"<b>Biópsias:</b> {_clean(event_report.biopsy)}", styles['Normal']))

    # Signature
    story.append(Spacer(1, 18))
    story += _signature_block(
        doctor_name=kollege.name,
        crm=kollege.crm,
        signed_by=current_user_name,
        signature_image=signature_image_field
    )

    # Footer / page number
    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        date_s = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        canvas.drawRightString(A4[0]-_pt(15), _pt(10), f"Emitido em {date_s}  ·  Página {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"✅ PDF generated: {event_report}")
    #buffer.seek(0)
    #return buffer.read()
    pdf_bytes = buffer.getvalue()
    print(f"PDF size: {len(pdf_bytes)} bytes")
    return pdf_bytes

# ---- Optional cryptographic signing (PKCS#12) ----
def sign_pdf_bytes_if_configured(pdf_bytes: bytes, p12_path: str, p12_password: str, name: str="Digest Report") -> bytes:
    """
    Uses 'endesive' to apply a CMS signature. Requires a real certificate (.p12).
    If you don't have one yet, skip calling this.
    """
    try:
        from endesive import pdf
        with open(p12_path, 'rb') as fp:
            p12 = fp.read()
        date = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S+00'00'")
        dct = {
            "aligned": 0,
            "sigflags": 3,
            "contact": "clinic@example.com",
            "location": "Fortaleza, BR",
            "signingdate": date,
            "reason": name,
        }
        return pdf.cms.sign(pdf_bytes, dct, p12, p12_password.encode('utf-8'))
    except Exception:
        # if signing fails, return original to avoid blocking
        return pdf_bytes
