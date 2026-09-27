"""One-page PDF report (A4) built with reportlab.

Content is shrunk to fit a single page, so any narrative length still yields one page.
DejaVu Sans (bundled with matplotlib) covers Latin, Cyrillic and Greek scripts.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import List, Tuple
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepInFrame, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import __version__
from .charts import INK, INK2, MUTED, colors_for
from .i18n import fmt_int, lang_name, pct, tr

_FONTS_READY = False


def _fonts():
    global _FONTS_READY
    if _FONTS_READY:
        return
    ttf = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    pdfmetrics.registerFont(TTFont("DejaVu", str(ttf / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(ttf / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(ttf / "DejaVuSans-Oblique.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-BoldOblique", str(ttf / "DejaVuSans-BoldOblique.ttf")))
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique",
                       boldItalic="DejaVu-BoldOblique")
    _FONTS_READY = True


def _inline(md: str) -> str:
    """Escape text for reportlab and convert **bold** / *italic*."""
    s = escape(md)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", s)
    return s


def _styles():
    base = dict(fontName="DejaVu", textColor=colors.HexColor(INK), leading=11, fontSize=8.4)
    return {
        "title": ParagraphStyle("title", **dict(base, fontName="DejaVu-Bold", fontSize=15, leading=18)),
        "sub": ParagraphStyle("sub", **dict(base, fontSize=7.2, leading=9, textColor=colors.HexColor(MUTED))),
        "answer": ParagraphStyle("answer", **dict(base, fontSize=9.6, leading=13)),
        "h": ParagraphStyle("h", **dict(base, fontName="DejaVu-Bold", fontSize=8.6, leading=11, spaceBefore=3,
                                        spaceAfter=1)),
        "body": ParagraphStyle("body", **base),
        "bullet": ParagraphStyle("bullet", **dict(base, leftIndent=8, bulletIndent=0, spaceAfter=1.5)),
        "cell": ParagraphStyle("cell", **dict(base, fontSize=6.9, leading=8.4)),
        "cellb": ParagraphStyle("cellb", **dict(base, fontName="DejaVu-Bold", fontSize=6.6, leading=8,
                                                textColor=colors.HexColor(INK2))),
        "small": ParagraphStyle("small", **dict(base, fontSize=6.4, leading=8, textColor=colors.HexColor(INK2),
                                                leftIndent=7, bulletIndent=0)),
        "foot": ParagraphStyle("foot", **dict(base, fontSize=6, leading=7.5, textColor=colors.HexColor(MUTED))),
    }


def _section_flowables(sections: List[Tuple[str, List[str]]], st) -> list:
    out = []
    for heading, lines in sections:
        if heading:
            out.append(Paragraph(_inline(heading), st["h"]))
        for line in lines:
            m = re.match(r"^([-*•]|\d+[.)])\s+(.*)$", line)
            if m:
                out.append(Paragraph(_inline(m.group(2)), st["bullet"], bulletText="•"))
            else:
                out.append(Paragraph(_inline(line), st["body"]))
    return out


def _image(path: Path, width: float) -> Image:
    iw, ih = ImageReader(str(path)).getSize()
    return Image(str(path), width=width, height=width * ih / iw)


def _metrics_table(a: dict, st, width: float, lang: str) -> Table:
    t = tr(lang)
    cmap = colors_for(a["series"])
    head = [t["col_series"], t["col_views"], t["col_ppm"], t["col_abs"], t["col_rel"], t["col_up"], t["col_conf"]]
    rows = [[Paragraph(escape(h), st["cellb"]) for h in head]]
    for s in a["series"]:
        swatch = ('<font color="%s">■</font> ' % cmap[s["id"]]) if s["id"] in cmap else ""
        if s["status"] != "ok":
            rows.append([Paragraph(swatch + escape(s["name"]), st["cell"])] +
                        [Paragraph("—", st["cell"]) for _ in range(5)] +
                        [Paragraph(escape(t["conf"]["n/a"]), st["cell"])])
            continue
        ci = pct(s.get("growth_rel"))
        if s.get("growth_rel_lo") is not None:
            ci += " [%s; %s]" % (pct(s["growth_rel_lo"]), pct(s["growth_rel_hi"]))
        grade = s["confidence"]["grade"]
        rows.append([
            Paragraph(swatch + escape(s["name"]), st["cell"]),
            Paragraph(fmt_int(s["views_recent_month_avg"], lang), st["cell"]),
            Paragraph("%.1f" % s["share_ppm_recent"] if s.get("share_ppm_recent") is not None else "—", st["cell"]),
            Paragraph(pct(s.get("growth_abs")), st["cell"]),
            Paragraph(("<b>%s</b>" % escape(ci)), st["cell"]),
            Paragraph("%d/12" % s["months_up"] if s.get("months_up") is not None else "—", st["cell"]),
            Paragraph(escape("%s · %s" % (t["conf"][grade], t["dir"][s["confidence"]["direction"]])), st["cell"]),
        ])
    fr = [0.23, 0.11, 0.12, 0.1, 0.2, 0.08, 0.16]
    tbl = Table(rows, colWidths=[f * width for f in fr], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#c3c2b7")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#e1e0d9")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tbl


def build_pdf(a: dict, title: str, sections: List[Tuple[str, List[str]]], trend_png: Path, growth_png: Path,
              out_pdf: Path, lang: str = "en") -> Path:
    _fonts()
    st = _styles()
    t = tr(lang)
    k = a["period"]["growth_window_months"]
    page_w, page_h = A4
    margin = 12 * mm
    width, height = page_w - 2 * margin, page_h - 2 * margin
    title = title or t["default_title"].format(topics=", ".join(x["label"] for x in a["topics"]))
    langs = ", ".join("%s (%s)" % (l, lang_name(l, lang)) for l in a["params"]["langs"])
    period = "%s – %s" % (a["period"]["start"][:7], a["period"]["end"][:7])
    subtitle = t["subtitle"].format(langs=langs, period=period, date=dt.date.today().isoformat())

    story = [Paragraph(_inline(title), st["title"]), Spacer(1, 1.5 * mm), Paragraph(escape(subtitle), st["sub"]),
             Spacer(1, 3 * mm)]
    if sections:
        head, lines = sections[0]
        answer = Paragraph(_inline(" ".join(re.sub(r"^([-*•])\s+", "", l) for l in lines)), st["answer"])
        box = Table([[answer]], colWidths=[width])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4fc")),
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor("#2a78d6")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story += [box, Spacer(1, 3 * mm)]
    story += [_image(trend_png, width), Spacer(1, 2.5 * mm)]

    left_w = width * 0.44
    right = _section_flowables(sections[1:], st) or [Paragraph("", st["body"])]
    row = Table([[_image(growth_png, left_w - 4), right]], colWidths=[left_w, width - left_w])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (0, 0), 6), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
    story += [row, Spacer(1, 3 * mm), _metrics_table(a, st, width, lang), Spacer(1, 3 * mm)]

    story.append(Paragraph(escape(t["method"]), st["h"]))
    for line in t["method_lines"]:
        story.append(Paragraph(escape(line.format(k=k)), st["small"], bulletText="•"))
    for note in a.get("notes", [])[:4]:
        template = t.get("notes", {}).get(note["code"])
        if template:
            story.append(Paragraph(escape(template.format(**note)), st["small"], bulletText="!"))
    story += [Spacer(1, 2 * mm), Paragraph(escape(t["footer"].format(version=__version__)), st["foot"])]

    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=margin,
                            bottomMargin=margin, title=title, author="wikipedia-interest-trends",
                            subject="Wikipedia pageview analysis")
    doc.build([KeepInFrame(width, height, story, mode="shrink")])
    return out_pdf


def page_count(pdf: Path) -> int:
    data = Path(pdf).read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?!s)", data))
