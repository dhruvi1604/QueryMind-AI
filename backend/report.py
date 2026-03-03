import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import re
import tempfile
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, NextPageTemplate
)
from reportlab.platypus.flowables import Flowable

# ── PALETTE ───────────────────────────────────────────────
BG      = colors.HexColor("#060B14")
BG2     = colors.HexColor("#0B1120")
BG3     = colors.HexColor("#0F1729")
PANEL   = colors.HexColor("#111D30")
BORDER  = colors.HexColor("#1A2840")
AMBER   = colors.HexColor("#F59E0B")
BLUE    = colors.HexColor("#3B82F6")
GREEN   = colors.HexColor("#10B981")
RED     = colors.HexColor("#EF4444")
PURPLE  = colors.HexColor("#8B5CF6")
WHITE   = colors.HexColor("#F8FAFC")
MUTED   = colors.HexColor("#64748B")
DIM     = colors.HexColor("#334155")
TEXT    = colors.HexColor("#CBD5E1")
TEXT_DIM= colors.HexColor("#94A3B8")

W, H    = A4
MARGIN  = 1.4 * cm
CW      = W - 2 * MARGIN   # content width


# ── TEXT CLEANER ──────────────────────────────────────────
def clean(text: str) -> str:
    """Strip markdown and non-latin chars."""
    if not text:
        return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*',     r'\1', text)
    text = re.sub(r'__(.*?)__',     r'\1', text)
    text = re.sub(r'#+\s*',         '',    text)
    text = re.sub(r'`(.*?)`',       r'\1', text)
    return text.encode("latin-1", "ignore").decode("latin-1")


def format_insight(text: str) -> list[str]:
    """
    Convert raw LLM insight into max 3 clean bullet points.
    Returns list of strings — one per bullet.
    """
    text = clean(text)
    # Split on common separators
    parts = re.split(r'(?:Insight:|Recommendation:|Note:|Finding:|Result:|-|\n\n)', text)
    bullets = []
    for p in parts:
        p = p.strip()
        if len(p) > 20:
            # Truncate each bullet to ~120 chars
            if len(p) > 140:
                p = p[:137] + "..."
            bullets.append(p)
        if len(bullets) == 3:
            break
    if not bullets and text:
        bullets = [text[:200]]
    return bullets


def extract_kpi(df: pd.DataFrame) -> tuple[str, str]:
    """
    Pull the single most important number from a dataframe.
    Returns (value_string, label_string)
    """
    numeric = df.select_dtypes(include="number").columns.tolist()
    text    = df.select_dtypes(exclude="number").columns.tolist()

    if not numeric:
        return str(len(df)), "TOTAL RECORDS"

    col = numeric[0]
    total = df[col].sum()
    mx    = df[col].max()

    # If it's a revenue/amount column — show total
    col_lower = col.lower()
    if any(k in col_lower for k in ["amount","revenue","total","sales","value","price"]):
        if total >= 1_000_000:
            return f"{total/1_000_000:.1f}M", f"TOTAL {col.upper().replace('_',' ')}"
        elif total >= 1_000:
            return f"{total/1_000:.0f}K", f"TOTAL {col.upper().replace('_',' ')}"
        else:
            return f"{total:,.0f}", f"TOTAL {col.upper().replace('_',' ')}"
    # Otherwise show row count + max
    else:
        if mx >= 1_000_000:
            return f"{mx/1_000_000:.1f}M", f"PEAK {col.upper().replace('_',' ')}"
        elif mx >= 1_000:
            return f"{mx/1_000:.0f}K", f"PEAK {col.upper().replace('_',' ')}"
        else:
            return f"{mx:,.0f}", f"PEAK {col.upper().replace('_',' ')}"


def anomaly_signal(text: str) -> tuple[str, colors.HexColor]:
    """Return (signal_label, color) based on anomaly text."""
    t = text.lower()
    if any(w in t for w in ["no anomal", "looks healthy", "normal", "consistent"]):
        return "ALL CLEAR", GREEN
    elif any(w in t for w in ["significant", "unusual", "investigate", "concern"]):
        return "REVIEW NEEDED", AMBER
    elif any(w in t for w in ["critical", "fraud", "error", "anomal"]):
        return "FLAG", RED
    return "MONITOR", AMBER


# ── CUSTOM FLOWABLES ──────────────────────────────────────
class HLine(Flowable):
    def __init__(self, width, color=BORDER, thickness=0.5):
        super().__init__()
        self.width = width
        self.height = thickness
        self._color = color
        self._thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(self._color)
        self.canv.setLineWidth(self._thickness)
        self.canv.line(0, 0, self.width, 0)


class AccentBar(Flowable):
    def __init__(self, width, color=AMBER, height=2):
        super().__init__()
        self.width = width
        self.height = height
        self._color = color

    def draw(self):
        self.canv.setFillColor(self._color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


# ── STYLES ────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)


def get_styles():
    return {
        # Cover
        "brand":      S("brand",      fontSize=46, fontName="Helvetica-Bold",  textColor=WHITE,    leading=52),
        "cover_sub":  S("cover_sub",  fontSize=16, fontName="Helvetica",       textColor=TEXT,     leading=20),
        "cover_tag":  S("cover_tag",  fontSize=9,  fontName="Helvetica",       textColor=MUTED),
        "cover_meta": S("cover_meta", fontSize=7.5,fontName="Helvetica",       textColor=DIM,      alignment=TA_CENTER),

        # Sections
        "sec_lbl":    S("sec_lbl",    fontSize=7,  fontName="Helvetica-Bold",  textColor=AMBER,    letterSpacing=2,   spaceAfter=3),
        "sec_title":  S("sec_title",  fontSize=18, fontName="Helvetica-Bold",  textColor=WHITE,    leading=22,        spaceAfter=4),
        "page_desc":  S("page_desc",  fontSize=8.5,fontName="Helvetica",       textColor=TEXT_DIM, leading=13,        spaceAfter=6),

        # Query
        "q_num":      S("q_num",      fontSize=7.5,fontName="Helvetica-Bold",  textColor=AMBER,    letterSpacing=1),
        "q_title":    S("q_title",    fontSize=15, fontName="Helvetica-Bold",  textColor=WHITE,    leading=20,        spaceBefore=4, spaceAfter=4),
        "lbl":        S("lbl",        fontSize=6.5,fontName="Helvetica-Bold",  textColor=MUTED,    letterSpacing=1.5, spaceBefore=6, spaceAfter=2),

        # KPI
        "kpi_val":    S("kpi_val",    fontSize=28, fontName="Helvetica-Bold",  textColor=AMBER,    alignment=TA_CENTER, leading=32),
        "kpi_lbl":    S("kpi_lbl",    fontSize=6.5,fontName="Helvetica-Bold",  textColor=MUTED,    alignment=TA_CENTER, letterSpacing=1),
        "kpi_rows":   S("kpi_rows",   fontSize=8,  fontName="Helvetica",       textColor=TEXT_DIM, alignment=TA_CENTER),

        # SQL
        "sql":        S("sql",        fontSize=7.5,fontName="Courier",         textColor=colors.HexColor("#7DD3FC"), backColor=BG2, leading=12),

        # Table
        "th":         S("th",         fontSize=7.5,fontName="Helvetica-Bold",  textColor=WHITE,    alignment=TA_CENTER),
        "td":         S("td",         fontSize=7.5,fontName="Helvetica",       textColor=TEXT,     alignment=TA_CENTER),
        "td_l":       S("td_l",       fontSize=7.5,fontName="Helvetica",       textColor=TEXT,     alignment=TA_LEFT),

        # Bullets
        "bullet_lbl": S("bullet_lbl", fontSize=7,  fontName="Helvetica-Bold",  textColor=BLUE,     letterSpacing=1.2),
        "bullet_body":S("bullet_body",fontSize=7.8,fontName="Helvetica",       textColor=TEXT_DIM, leading=12,        spaceAfter=3),
        "ano_lbl":    S("ano_lbl",    fontSize=7,  fontName="Helvetica-Bold",  textColor=AMBER,    letterSpacing=1.2),

        # Summary
        "sum_q":      S("sum_q",      fontSize=7.5,fontName="Helvetica",       textColor=TEXT,     alignment=TA_LEFT),
        "sum_ok":     S("sum_ok",     fontSize=7.5,fontName="Helvetica-Bold",  textColor=GREEN,    alignment=TA_CENTER),
        "sum_num":    S("sum_num",    fontSize=7.5,fontName="Helvetica",       textColor=TEXT_DIM, alignment=TA_CENTER),

        # Exec metric
        "m_val":      S("m_val",      fontSize=20, fontName="Helvetica-Bold",  textColor=AMBER,    alignment=TA_CENTER, leading=24),
        "m_lbl":      S("m_lbl",      fontSize=6.5,fontName="Helvetica",       textColor=MUTED,    alignment=TA_CENTER, letterSpacing=0.5),
    }


# ── CHART — consistent amber→blue gradient always ─────────
def make_chart(df: pd.DataFrame, idx: int) -> str | None:
    numeric = df.select_dtypes(include="number").columns.tolist()
    text    = df.select_dtypes(exclude="number").columns.tolist()

    try:
        fig = None

        if numeric and text:
            x, y = text[0], numeric[0]
            df_p = df.head(12)
            vals = df_p[y].tolist()
            # Consistent amber→blue gradient
            fig = go.Figure(go.Bar(
                x=df_p[x].astype(str), y=vals,
                marker=dict(
                    color=vals,
                    colorscale=[[0,"#1E3A5F"],[0.45,"#3B82F6"],[1,"#F59E0B"]],
                    line=dict(width=0)
                ),
                text=[f"{v:,.0f}" if isinstance(v,(int,float)) and v > 999
                      else (f"{v:.1f}" if isinstance(v,float) else str(v))
                      for v in vals],
                textposition="outside",
                textfont=dict(size=8, color="#94A3B8")
            ))

        elif numeric:
            df_p = df.head(20)
            x_ax = list(range(1, len(df_p)+1))
            fig  = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_ax, y=df_p[numeric[0]],
                mode="lines+markers",
                line=dict(color="#F59E0B", width=2.5),
                marker=dict(color="#FCD34D", size=5),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.08)",
                name=numeric[0]
            ))
            if len(numeric) > 1:
                fig.add_trace(go.Scatter(
                    x=x_ax, y=df_p[numeric[1]],
                    mode="lines+markers",
                    line=dict(color="#3B82F6", width=2),
                    marker=dict(color="#93C5FD", size=5),
                    name=numeric[1]
                ))

        elif text:
            vc  = df[text[0]].value_counts().head(10)
            fig = go.Figure(go.Bar(
                x=vc.index.astype(str), y=vc.values,
                marker=dict(
                    color=list(range(len(vc))),
                    colorscale=[[0,"#1E3A5F"],[0.5,"#3B82F6"],[1,"#F59E0B"]],
                    line=dict(width=0)
                ),
                text=vc.values, textposition="outside",
                textfont=dict(size=8, color="#94A3B8")
            ))
        else:
            return None

        fig.update_layout(
            width=720, height=270,
            plot_bgcolor="#0B1120",
            paper_bgcolor="#0B1120",
            margin=dict(l=45, r=20, t=20, b=55),
            font=dict(color="#64748B", size=9, family="Helvetica"),
            xaxis=dict(
                showgrid=False, linecolor="#1A2840",
                tickfont=dict(size=8, color="#64748B"),
                tickangle=-35 if len(df) > 6 else 0
            ),
            yaxis=dict(
                showgrid=True, gridcolor="#0D1729",
                linecolor="#1A2840",
                tickfont=dict(size=8, color="#64748B")
            ),
            showlegend=len(numeric) > 1,
            legend=dict(font=dict(size=8, color="#64748B"), bgcolor="rgba(0,0,0,0)")
        )

        tmp = tempfile.NamedTemporaryFile(suffix=f"_q{idx}.png", delete=False)
        pio.write_image(fig, tmp.name, format="png", scale=2)
        return tmp.name

    except Exception as e:
        print(f"Chart error: {e}")
        return None


# ── TABLE BUILDERS ────────────────────────────────────────
def build_data_table(df: pd.DataFrame, ST: dict) -> Table:
    df_s = df.head(8)
    cols = [clean(str(c)).upper() for c in df_s.columns]
    n    = len(cols)
    cw   = CW / n

    rows = [[Paragraph(c, ST["th"]) for c in cols]]
    for _, row in df_s.iterrows():
        rows.append([
            Paragraph(clean(str(v))[:24],
                     ST["td_l"] if j == 0 else ST["td"])
            for j, v in enumerate(row)
        ])

    t = Table(rows, colWidths=[cw]*n, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  PANEL),
        ("LINEBELOW",      (0,0),(-1,0),  1.5, AMBER),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [BG2, BG3]),
        ("ALIGN",          (0,0),(-1,-1), "CENTER"),
        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("GRID",           (0,0),(-1,-1), 0.3, BORDER),
    ]))
    return t


def build_summary_table(report_data: list, ST: dict) -> Table:
    rows = [[Paragraph(h, ST["th"]) for h in ["#","QUESTION","ROWS","STATUS"]]]
    for i, item in enumerate(report_data):
        q = clean(item["question"])
        q = q[:65]+"..." if len(q) > 65 else q
        n = str(len(item["df"])) if item["df"] is not None else "0"
        rows.append([
            Paragraph(str(i+1),  ST["sum_num"]),
            Paragraph(q,         ST["sum_q"]),
            Paragraph(n,         ST["sum_num"]),
            Paragraph("SUCCESS", ST["sum_ok"]),
        ])

    t = Table(rows, colWidths=[1.0*cm, 12.2*cm, 1.8*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  PANEL),
        ("LINEBELOW",      (0,0),(-1,0),  1.5, AMBER),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [BG2, BG3]),
        ("ALIGN",          (0,0),(-1,-1), "CENTER"),
        ("ALIGN",          (1,1),(1,-1),  "LEFT"),
        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",     (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 7),
        ("LEFTPADDING",    (1,0),(1,-1),  8),
        ("GRID",           (0,0),(-1,-1), 0.3, BORDER),
    ]))
    return t


def build_kpi_strip(df: pd.DataFrame, ST: dict) -> Table:
    """
    3-cell KPI strip: [BIG NUMBER] [ROW COUNT] [STATUS]
    This is what a CFO sees first.
    """
    kpi_val, kpi_lbl = extract_kpi(df)
    row_count = f"{len(df):,}"

    cell1 = [
        Paragraph(kpi_val, ST["kpi_val"]),
        Paragraph(kpi_lbl, ST["kpi_lbl"]),
    ]
    cell2 = [
        Paragraph(row_count,
                 ParagraphStyle("rv", fontSize=22, fontName="Helvetica-Bold",
                                textColor=BLUE, alignment=TA_CENTER, leading=26)),
        Paragraph("ROWS RETURNED",
                 ParagraphStyle("rl", fontSize=6.5, fontName="Helvetica-Bold",
                                textColor=MUTED, alignment=TA_CENTER, letterSpacing=1)),
    ]
    cell3 = [
        Paragraph("LIVE",
                 ParagraphStyle("lv", fontSize=22, fontName="Helvetica-Bold",
                                textColor=GREEN, alignment=TA_CENTER, leading=26)),
        Paragraph("DATABASE",
                 ParagraphStyle("db", fontSize=6.5, fontName="Helvetica-Bold",
                                textColor=MUTED, alignment=TA_CENTER, letterSpacing=1)),
    ]

    t = Table([[cell1, cell2, cell3]], colWidths=[CW/3]*3)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), colors.HexColor("#1C1408")),
        ("BACKGROUND",    (1,0),(1,0), colors.HexColor("#0C1828")),
        ("BACKGROUND",    (2,0),(2,0), colors.HexColor("#081A12")),
        ("LINEABOVE",     (0,0),(0,0), 2.5, AMBER),
        ("LINEABOVE",     (1,0),(1,0), 2.5, BLUE),
        ("LINEABOVE",     (2,0),(2,0), 2.5, GREEN),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
    ]))
    return t


def build_insight_panel(insight: str, anomaly: str, ST: dict) -> Table:
    """
    Two-column panel:
    Left  = 3 clean bullet insights
    Right = Anomaly signal + 2 lines max
    """
    bullets = format_insight(insight)
    sig_label, sig_color = anomaly_signal(anomaly)
    ano_clean = clean(anomaly)

    # Trim anomaly to 2 sentences max
    sentences = re.split(r'(?<=[.!?])\s+', ano_clean)
    ano_short  = " ".join(sentences[:2]) if sentences else ano_clean
    if len(ano_short) > 220:
        ano_short = ano_short[:217] + "..."

    # Build left cell — bullet points
    left_content = [Paragraph("KEY INSIGHTS", ST["bullet_lbl"]), Spacer(1, 5)]
    for b in bullets:
        left_content.append(
            Paragraph(f"• {b}", ST["bullet_body"])
        )

    # Build right cell — signal + anomaly
    right_content = [
        Paragraph("ANOMALY STATUS", ST["ano_lbl"]),
        Spacer(1, 4),
        Paragraph(sig_label,
                 ParagraphStyle("sig", fontSize=14, fontName="Helvetica-Bold",
                                textColor=sig_color, alignment=TA_CENTER, leading=18)),
        Spacer(1, 6),
        HLine(CW/2 - 0.6*cm, BORDER),
        Spacer(1, 6),
        Paragraph(ano_short,
                 ParagraphStyle("ab", fontSize=7.5, fontName="Helvetica",
                                textColor=TEXT_DIM, leading=12, alignment=TA_JUSTIFY)),
    ]

    half = (CW - 0.3*cm) / 2
    t = Table([[left_content, right_content]], colWidths=[half, half])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,-1), colors.HexColor("#0C1828")),
        ("BACKGROUND", (1,0),(1,-1), colors.HexColor("#120D04")),
        ("LINEBEFORE",  (0,0),(0,-1), 2.5, BLUE),
        ("LINEBEFORE",  (1,0),(1,-1), 2.5, AMBER),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
    ]))
    return t


# ── PAGE BACKGROUNDS ──────────────────────────────────────
def cover_bg(canvas, doc):
    canvas.saveState()

    # Base
    canvas.setFillColor(BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Grid lines
    canvas.setStrokeColor(colors.HexColor("#0D1829"))
    canvas.setLineWidth(0.3)
    for y in range(0, int(H), 18):
        canvas.line(0, y, W, y)

    # Top amber stripe
    canvas.setFillColor(AMBER)
    canvas.rect(0, H-4, W, 4, fill=1, stroke=0)

    # Left amber stripe
    canvas.setFillColor(AMBER)
    canvas.rect(0, 0, 3, H, fill=1, stroke=0)

    # Decorative circles top-right
    canvas.setFillColor(colors.HexColor("#0D1829"))
    canvas.circle(W+0.5*cm, H*0.74, 5.5*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0A1422"))
    canvas.circle(W-1.5*cm, H*0.62, 3.2*cm, fill=1, stroke=0)

    # Bottom data bar
    canvas.setFillColor(colors.HexColor("#080E1A"))
    canvas.rect(0, 0, W, 1.8*cm, fill=1, stroke=0)
    canvas.setStrokeColor(AMBER)
    canvas.setLineWidth(1)
    canvas.line(0, 1.8*cm, W, 1.8*cm)

    canvas.restoreState()


def inner_bg(canvas, doc):
    canvas.saveState()

    # Base
    canvas.setFillColor(BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Top header bar
    canvas.setFillColor(BG2)
    canvas.rect(0, H-1.1*cm, W, 1.1*cm, fill=1, stroke=0)
    canvas.setStrokeColor(AMBER)
    canvas.setLineWidth(1)
    canvas.line(0, H-1.1*cm, W, H-1.1*cm)

    # Header text
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(AMBER)
    canvas.drawString(MARGIN, H-0.7*cm, "QUERYMIND")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN+2.2*cm, H-0.7*cm, "Business Intelligence Report")
    canvas.drawRightString(W-MARGIN, H-0.7*cm, f"Page {doc.page}")

    # Bottom footer bar
    canvas.setFillColor(BG2)
    canvas.rect(0, 0, W, 1*cm, fill=1, stroke=0)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0, 1*cm, W, 1*cm)

    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(DIM)
    canvas.drawString(MARGIN, 0.35*cm,
                     f"QueryMind AI  |  Groq Llama 3  |  {datetime.now().strftime('%B %d, %Y')}")
    canvas.drawRightString(W-MARGIN, 0.35*cm, "CONFIDENTIAL — FOR INTERNAL USE ONLY")

    # Left amber accent stripe
    canvas.setFillColor(AMBER)
    canvas.rect(0, 0, 3, H, fill=1, stroke=0)

    canvas.restoreState()


# ══════════════════════════════════════════════════════════
# MAIN BUILDER
# ══════════════════════════════════════════════════════════
def create_report(report_data: list) -> bytes:
    buffer = io.BytesIO()
    ST     = get_styles()
    now    = datetime.now()

    cover_frame = Frame(MARGIN, 1.8*cm, CW, H-1.8*cm-1*cm,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)
    inner_frame = Frame(MARGIN, 1.1*cm, CW, H-1.1*cm-1.1*cm,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)

    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1*cm, bottomMargin=1*cm,
        title="QueryMind Business Intelligence Report",
        author="QueryMind AI"
    )
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=cover_bg),
        PageTemplate(id="inner", frames=[inner_frame], onPage=inner_bg),
    ])

    story = []

    # ══════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ══════════════════════════════════════════════════════
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("QueryMind", ST["brand"]))
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph("Business Intelligence Report", ST["cover_sub"]))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph("AI-powered insights from your business data", ST["cover_tag"]))
    story.append(Spacer(1, 1.2*cm))
    story.append(AccentBar(CW, AMBER, 1.5))
    story.append(Spacer(1, 1*cm))

    # Stat pills
    total_rows_cover = sum(len(d["df"]) for d in report_data if d["df"] is not None)
    pill_data = [[
        Paragraph(f"<b>{len(report_data)}</b><br/>Queries",
                 ParagraphStyle("p1", fontSize=13, fontName="Helvetica-Bold",
                                textColor=WHITE, alignment=TA_CENTER, leading=18)),
        Paragraph("<b>Llama 3</b><br/>Model",
                 ParagraphStyle("p2", fontSize=13, fontName="Helvetica-Bold",
                                textColor=WHITE, alignment=TA_CENTER, leading=18)),
        Paragraph("<b>Live</b><br/>Database",
                 ParagraphStyle("p3", fontSize=13, fontName="Helvetica-Bold",
                                textColor=WHITE, alignment=TA_CENTER, leading=18)),
    ]]
    pill_t = Table(pill_data, colWidths=[CW/3]*3)
    pill_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), colors.HexColor("#1E3A5F")),
        ("BACKGROUND", (1,0),(1,0), colors.HexColor("#1A3020")),
        ("BACKGROUND", (2,0),(2,0), colors.HexColor("#2D1F0A")),
        ("LINEABOVE",  (0,0),(0,0), 2.5, BLUE),
        ("LINEABOVE",  (1,0),(1,0), 2.5, GREEN),
        ("LINEABOVE",  (2,0),(2,0), 2.5, AMBER),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 14),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story.append(pill_t)
    story.append(Spacer(1, 1*cm))

    # Cover data summary grid — fills the empty bottom half
    story.append(AccentBar(CW, DIM, 0.5))
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("REPORT SUMMARY", ST["sec_lbl"]))
    story.append(Spacer(1, 0.3*cm))

    # Mini summary table on cover
    cover_rows = [[
        Paragraph("QUERY", ParagraphStyle("ch", fontSize=7, fontName="Helvetica-Bold",
                                          textColor=MUTED, alignment=TA_LEFT)),
        Paragraph("ROWS", ParagraphStyle("ch2", fontSize=7, fontName="Helvetica-Bold",
                                         textColor=MUTED, alignment=TA_CENTER)),
    ]]
    for item in report_data:
        q = clean(item["question"])
        q = q[:70] + "..." if len(q) > 70 else q
        n = str(len(item["df"])) if item["df"] is not None else "0"
        cover_rows.append([
            Paragraph(q, ParagraphStyle("cq", fontSize=8, fontName="Helvetica",
                                        textColor=TEXT, alignment=TA_LEFT)),
            Paragraph(n, ParagraphStyle("cn", fontSize=8, fontName="Helvetica",
                                        textColor=TEXT_DIM, alignment=TA_CENTER)),
        ])

    cover_t = Table(cover_rows, colWidths=[CW*0.82, CW*0.18])
    cover_t.setStyle(TableStyle([
        ("LINEBELOW",      (0,0),(-1,0),   0.8, AMBER),
        ("ROWBACKGROUNDS", (0,1),(-1,-1),  [colors.HexColor("#0A0E1A"),
                                            colors.HexColor("#0D1320")]),
        ("TOPPADDING",     (0,0),(-1,-1),  6),
        ("BOTTOMPADDING",  (0,0),(-1,-1),  6),
        ("LEFTPADDING",    (0,0),(-1,-1),  6),
        ("GRID",           (0,0),(-1,-1),  0.3, BORDER),
    ]))
    story.append(cover_t)
    story.append(Spacer(1, 0.8*cm))

    story.append(Paragraph(
        f"Generated on {now.strftime('%B %d, %Y at %H:%M')}  |  "
        f"QueryMind AI  |  Groq Llama 3  |  {len(report_data)} Queries  |  {total_rows_cover:,} Total Rows",
        ST["cover_meta"]
    ))

    # ── Switch template ───────────────────────────────────
    story.append(NextPageTemplate("inner"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════
    # PAGE 2 — EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("EXECUTIVE SUMMARY", ST["sec_lbl"]))
    story.append(AccentBar(CW, AMBER, 1.5))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Report Overview", ST["sec_title"]))
    story.append(Paragraph(
        f"Prepared by QueryMind AI on {now.strftime('%B %d, %Y')}. "
        f"This report covers {len(report_data)} business intelligence "
        f"queries — each converted from plain English to SQL, executed on live "
        f"data, and analyzed for actionable insights and anomalies.",
        ST["page_desc"]
    ))
    story.append(Spacer(1, 0.4*cm))

    # Exec metric cards
    total_rows = sum(len(d["df"]) for d in report_data if d["df"] is not None)

    def mc(val, lbl, col):
        return [
            Paragraph(val, ParagraphStyle("mv2", fontSize=20,
                fontName="Helvetica-Bold", textColor=col,
                alignment=TA_CENTER, leading=24)),
            Paragraph(lbl, ParagraphStyle("ml2", fontSize=6.5,
                fontName="Helvetica", textColor=MUTED,
                alignment=TA_CENTER, letterSpacing=0.5)),
        ]

    m_data = [[
        mc(str(len(report_data)),  "QUERIES ANALYZED",    AMBER),
        mc(f"{total_rows:,}",      "TOTAL ROWS RETURNED", BLUE),
        mc("100%",                 "SUCCESS RATE",        GREEN),
        mc(now.strftime("%d %b"),  "REPORT DATE",         PURPLE),
    ]]
    m_t = Table(m_data, colWidths=[CW/4]*4)
    m_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), colors.HexColor("#1C1408")),
        ("BACKGROUND", (1,0),(1,0), colors.HexColor("#0C1828")),
        ("BACKGROUND", (2,0),(2,0), colors.HexColor("#081A12")),
        ("BACKGROUND", (3,0),(3,0), colors.HexColor("#140C20")),
        ("LINEABOVE",  (0,0),(0,0), 2, AMBER),
        ("LINEABOVE",  (1,0),(1,0), 2, BLUE),
        ("LINEABOVE",  (2,0),(2,0), 2, GREEN),
        ("LINEABOVE",  (3,0),(3,0), 2, PURPLE),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story.append(m_t)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("QUERIES IN THIS REPORT", ST["sec_lbl"]))
    story.append(Spacer(1, 0.2*cm))
    story.append(build_summary_table(report_data, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════
    # QUERY PAGES
    # ══════════════════════════════════════════════════════
    for i, item in enumerate(report_data):
        story.append(Spacer(1, 0.1*cm))

        # ── Header badge ─────────────────────────────────
        hdr = Table([[
            Paragraph(f"QUERY {i+1} OF {len(report_data)}", ST["q_num"]),
            Paragraph(now.strftime("%d %b %Y"),
                     ParagraphStyle("hd", fontSize=7.5, fontName="Helvetica",
                                   textColor=MUTED, alignment=TA_RIGHT)),
        ]], colWidths=[CW*0.6, CW*0.4])
        hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), PANEL),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
            ("LINEABOVE",     (0,0),(-1, 0), 1.5, AMBER),
        ]))
        story.append(KeepTogether([hdr]))
        story.append(Spacer(1, 0.2*cm))

        # Question title
        story.append(Paragraph(clean(item["question"]), ST["q_title"]))
        story.append(HLine(CW, BORDER))
        story.append(Spacer(1, 0.2*cm))

        # ── KPI STRIP — CFO sees this first ──────────────
        if item["df"] is not None and not item["df"].empty:
            story.append(Paragraph("KEY METRICS", ST["lbl"]))
            story.append(build_kpi_strip(item["df"], ST))
            story.append(Spacer(1, 0.25*cm))

        # ── SQL ───────────────────────────────────────────
        story.append(Paragraph("GENERATED SQL", ST["lbl"]))
        sql_t = Table([[Paragraph(clean(item["sql"]), ST["sql"])]],
                      colWidths=[CW])
        sql_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), BG2),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
            ("LINEBEFORE",    (0,0),(0,-1),  2.5, BLUE),
            ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
        ]))
        story.append(sql_t)
        story.append(Spacer(1, 0.25*cm))

        # ── Data table ────────────────────────────────────
        if item["df"] is not None and not item["df"].empty:
            df = item["df"]
            story.append(Paragraph(f"RESULTS — {len(df):,} ROWS RETURNED", ST["lbl"]))
            story.append(build_data_table(df, ST))
            story.append(Spacer(1, 0.25*cm))

            # ── Chart ─────────────────────────────────────
            chart_path = make_chart(df, i)
            if chart_path and os.path.exists(chart_path):
                story.append(Paragraph("VISUALIZATION", ST["lbl"]))
                img_t = Table(
                    [[Image(chart_path, width=CW, height=6.5*cm)]],
                    colWidths=[CW]
                )
                img_t.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0),(-1,-1), BG2),
                    ("BOX",           (0,0),(-1,-1), 0.5, BORDER),
                    ("TOPPADDING",    (0,0),(-1,-1), 5),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                    ("LEFTPADDING",   (0,0),(-1,-1), 5),
                    ("RIGHTPADDING",  (0,0),(-1,-1), 5),
                ]))
                story.append(img_t)
                story.append(Spacer(1, 0.25*cm))

        # ── Insight + Anomaly panel ───────────────────────
        insight = item.get("insight", "")
        anomaly = item.get("anomaly", "")
        if insight or anomaly:
            story.append(build_insight_panel(insight, anomaly, ST))

        if i < len(report_data) - 1:
            story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()