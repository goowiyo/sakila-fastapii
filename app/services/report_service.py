import io
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib import colors
from app.services import data_pipeline_service as dps


COLOR_PRIMARY = HexColor("#1a237e")
COLOR_SECONDARY = HexColor("#283593")
COLOR_ACCENT = HexColor("#3949ab")
COLOR_LIGHT = HexColor("#e8eaf6")
COLOR_WHITE = colors.white


def _build_header_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=COLOR_PRIMARY,
        spaceAfter=4,
        alignment=0
    ))
    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        fontName='Helvetica',
        fontSize=11,
        textColor=HexColor("#5c6bc0"),
        spaceAfter=16,
        alignment=0
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLOR_SECONDARY,
        spaceBefore=18,
        spaceAfter=8,
        borderPadding=(0, 0, 4, 0)
    ))
    styles.add(ParagraphStyle(
        name='MetricValue',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=COLOR_PRIMARY,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        name='MetricLabel',
        fontName='Helvetica',
        fontSize=9,
        textColor=HexColor("#666666"),
        alignment=1,
        spaceBefore=2
    ))
    return styles


def _build_quality_section(styles, quality: Dict[str, Any]) -> List:
    elements = []
    elements.append(Paragraph("Pipeline Quality Metrics", styles['SectionTitle']))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_ACCENT))
    elements.append(Spacer(1, 10))

    data = [
        ["Total Ingested", "Total Processed", "Total Failed"],
        [
            str(quality.get("total_ingested", 0)),
            str(quality.get("total_processed", 0)),
            str(quality.get("total_failed", 0))
        ]
    ]
    t = Table(data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 1), (-1, -1), COLOR_LIGHT),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 16),
        ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_ACCENT),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 14))

    by_source = quality.get("records_by_source", {})
    if by_source:
        elements.append(Paragraph("<b>Records by Source</b>", styles['Normal']))
        elements.append(Spacer(1, 4))
        src_data = [["Source", "Count"]]
        for src, cnt in by_source.items():
            src_data.append([src, str(cnt)])
        src_table = Table(src_data, colWidths=[3*inch, 3*inch])
        src_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f5f5f5")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#c5cae9")),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        elements.append(src_table)

    by_status = quality.get("records_by_status", {})
    if by_status:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>Records by Status</b>", styles['Normal']))
        elements.append(Spacer(1, 4))
        st_data = [["Status", "Count"]]
        for st, cnt in by_status.items():
            st_data.append([st, str(cnt)])
        st_table = Table(st_data, colWidths=[3*inch, 3*inch])
        st_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f5f5f5")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#c5cae9")),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        elements.append(st_table)

    return elements


def _build_metrics_section(styles, metrics: List[Dict[str, Any]]) -> List:
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("Computed Metrics Report", styles['SectionTitle']))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_ACCENT))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"Total metrics computed: <b>{len(metrics)}</b>", styles['Normal']))
    elements.append(Spacer(1, 10))

    if not metrics:
        elements.append(Paragraph("No metrics available.", styles['Normal']))
        return elements

    header = ["ID", "Metric", "Value", "Dimension", "Dim. Value", "Date"]
    col_widths = [0.5*inch, 1.3*inch, 1*inch, 1*inch, 1.2*inch, 1.2*inch]
    data = [header]

    for m in metrics[:50]:
        data.append([
            str(m.get("id", "")),
            m.get("metric_name", ""),
            str(m.get("metric_value", "")),
            m.get("dimension") or "-",
            m.get("dimension_value") or "-",
            str(m.get("created_at", ""))[:19]
        ])

    remaining = max(0, len(metrics) - 50)
    if remaining > 0:
        data.append(["", f"... and {remaining} more", "", "", "", ""])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#fafafa")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#c5cae9")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    return elements


def _build_metric_summary_cards(styles, metrics: List[Dict[str, Any]]) -> List:
    elements = []
    elements.append(Paragraph("Metric Summary", styles['SectionTitle']))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_ACCENT))
    elements.append(Spacer(1, 10))

    metric_counts = {}
    for m in metrics:
        name = m.get("metric_name", "unknown")
        metric_counts[name] = metric_counts.get(name, 0) + 1

    sorted_metrics = sorted(metric_counts.items(), key=lambda x: -x[1])

    data = [["Metric Type", "Count"]]
    for name, count in sorted_metrics:
        data.append([name, str(count)])

    table = Table(data, colWidths=[3*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f5f5f5")),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#c5cae9")),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    elements.append(table)
    return elements


def generate_report(db: Session) -> io.BytesIO:
    quality = dps.get_quality_metrics(db)
    raw_metrics, total_count = dps.get_metrics(db, limit=1000)

    metrics_list = []
    for m in raw_metrics:
        metrics_list.append({
            "id": m.id,
            "metric_name": m.metric_name,
            "metric_value": m.metric_value,
            "dimension": m.dimension,
            "dimension_value": m.dimension_value,
            "created_at": m.created_at.isoformat() if m.created_at else ""
        })

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=0.6*inch,
        bottomMargin=0.6*inch,
        leftMargin=0.7*inch,
        rightMargin=0.7*inch
    )

    styles = _build_header_styles()
    elements = []

    elements.append(Paragraph("Data Pipeline Report", styles['ReportTitle']))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Total metrics: {total_count}",
        styles['ReportSubtitle']
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARY))
    elements.append(Spacer(1, 12))

    elements.extend(_build_quality_section(styles, quality))
    elements.extend(_build_metric_summary_cards(styles, metrics_list))
    elements.extend(_build_metrics_section(styles, metrics_list))

    doc.build(elements)
    buf.seek(0)
    return buf
