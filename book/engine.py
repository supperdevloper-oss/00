# -*- coding: utf-8 -*-
"""
محرك بناء كتاب «مشروعي الأول فالمغرب»
يحوّل ملفات نصية بسيطة (صيغة mdown) إلى PDF بالعربية من اليمين إلى اليسار.

يعتمد على: fpdf2 + uharfbuzz (تشكيل الحروف العربية) + خطي Amiri و Cairo.
"""
from __future__ import annotations

import os
import re
import sys

from fpdf import FPDF
from fpdf.enums import XPos, YPos

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# ----------------------------------------------------------------------------- ألوان
INK = (26, 26, 26)
GREY = (110, 110, 110)
ACCENT = (163, 73, 24)          # بني مغربي
ACCENT_SOFT = (247, 239, 230)
BOX_LINE = (205, 187, 160)
BOX_FILL = (250, 246, 240)
BOX_FILL2 = (238, 244, 240)
TABLE_HEAD_FILL = (60, 60, 60)
TABLE_HEAD_TEXT = (255, 255, 255)
TABLE_ALT = (246, 244, 241)
RULE = (190, 178, 160)

PAGE_W, PAGE_H = 148, 210      # A5
MARGIN = 15
BODY_SIZE = 9.2
LINE_H = 5.0


# ============================================================================ PDF
class Book(FPDF):
    def __init__(self, title, author):
        super().__init__(orientation="P", unit="mm", format=(PAGE_W, PAGE_H))
        self.book_title = title
        self.book_author = author
        self.running_head = ""
        self.show_furniture = False
        self._cover_mode = False
        self._skip_break = False
        self.toc: list = []
        self.toc_entries: list = []
        self.set_margins(MARGIN, 18, MARGIN)
        self.set_auto_page_break(True, margin=16)

        self.add_font("Amiri", "", os.path.join(FONT_DIR, "Amiri-Regular.ttf"))
        self.add_font("Amiri", "B", os.path.join(FONT_DIR, "Amiri-Bold.ttf"))
        self.add_font("Cairo", "", os.path.join(FONT_DIR, "Cairo-Regular.ttf"))
        self.add_font("Cairo", "B", os.path.join(FONT_DIR, "Cairo-Bold.ttf"))
        self.set_font("Amiri", "", BODY_SIZE)

        self.set_title(title)
        self.set_author(author)
        self.set_lang("ar")

    # ------------------------------------------------------------------ furniture
    def header(self):
        if not self.show_furniture:
            return
        self.set_y(8)
        self.set_font("Cairo", "", 6.6)
        self.set_text_color(*GREY)
        self.set_x(MARGIN)
        self.cell(PAGE_W - 2 * MARGIN, 4, self.book_title, align="L")
        self.set_xy(MARGIN, 8)
        self.cell(PAGE_W - 2 * MARGIN, 4, self.running_head, align="R")
        self.set_draw_color(*RULE)
        self.set_line_width(0.2)
        self.line(MARGIN, 13.2, PAGE_W - MARGIN, 13.2)
        self.set_y(18)

    def footer(self):
        if not self.show_furniture:
            return
        self.set_y(-13)
        self.set_draw_color(*RULE)
        self.set_line_width(0.2)
        self.line(MARGIN, -13, PAGE_W - MARGIN, -13)
        self.set_font("Cairo", "", 7.4)
        self.set_text_color(*GREY)
        self.set_xy(MARGIN, -11.5)
        self.cell(PAGE_W - 2 * MARGIN, 5, str(self.page_no()), align="C")

    # ------------------------------------------------------------------ helpers
    def render_cover(self, title, subtitle, footer=""):
        """صفحة الغلاف."""
        self.add_page()
        self.set_fill_color(*ACCENT)
        self.rect(0, 0, PAGE_W, 7, style="F")
        self.rect(0, PAGE_H - 7, PAGE_W, 7, style="F")
        # إطار داخلي
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.4)
        self.rect(10, 14, PAGE_W - 20, PAGE_H - 28)

        self.set_y(48)
        self.set_font("Cairo", "B", 10)
        self.set_text_color(*GREY)
        self.multi_cell(PAGE_W - 40, 6, "دليل عملي للمبتدئين في المغرب",
                        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)
        self.set_font("Cairo", "B", 26)
        self.set_text_color(*ACCENT)
        self.multi_cell(PAGE_W - 36, 13, title, align="C",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(PAGE_W / 2 - 18, y, PAGE_W / 2 + 18, y)
        self.ln(6)
        self.set_font("Amiri", "", 11)
        self.set_text_color(*INK)
        self.multi_cell(PAGE_W - 44, 6.4, subtitle, align="C",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(10)
        # شارة المبلغ
        self.set_fill_color(*ACCENT_SOFT)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.35)
        bw, bh = 74, 13
        x0 = (PAGE_W - bw) / 2
        y0 = self.get_y()
        self.rect(x0, y0, bw, bh, style="DF")
        self.set_xy(x0, y0 + 3.2)
        self.set_font("Cairo", "B", 9.5)
        self.set_text_color(*ACCENT)
        self.cell(bw, 6, "من 2,000 درهم إلى أول اختبار", align="C")
        self.set_y(PAGE_H - 46)
        self.set_font("Amiri", "", 9)
        self.set_text_color(*GREY)
        self.multi_cell(PAGE_W - 40, 5.4,
                        "كتاب + أمثلة + حالات عملية + تجارب مغربية موثقة + دفتر عمل",
                        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if footer:
            self.set_y(PAGE_H - 30)
            self.set_font("Cairo", "", 8)
            self.multi_cell(PAGE_W - 40, 5, footer, align="C",
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.add_page()

    def _body(self):
        self.set_font("Amiri", "", BODY_SIZE)
        self.set_text_color(*INK)

    def para(self, text, size=BODY_SIZE, bold=False, align="R", space_after=2.2,
             color=INK, font="Amiri", indent=0):
        self.set_font(font, "B" if bold else "", size)
        self.set_text_color(*color)
        if indent:
            self.set_x(MARGIN + indent)
        self.multi_cell(
            PAGE_W - 2 * MARGIN - indent,
            size * 0.52 if font == "Amiri" else size * 0.6,
            text,
            align=align,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(space_after)

    def h1(self, text):
        self.set_font("Cairo", "B", 15)
        self.set_text_color(*ACCENT)
        self.multi_cell(PAGE_W - 2 * MARGIN, 8.5, text, align="R",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        y = self.get_y() + 1
        self.line(PAGE_W - MARGIN - 34, y, PAGE_W - MARGIN, y)
        self.ln(4.5)

    def h2(self, text):
        self.ensure_space(16)
        self.set_font("Cairo", "B", 11.6)
        self.set_text_color(*ACCENT)
        self.multi_cell(PAGE_W - 2 * MARGIN, 7, text, align="R",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.6)

    def h3(self, text):
        self.ensure_space(13)
        self.set_font("Cairo", "B", 9.8)
        self.set_text_color(*INK)
        self.multi_cell(PAGE_W - 2 * MARGIN, 6, text, align="R",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.0)

    def bullet(self, text, level=0, marker="—"):
        self.set_font("Amiri", "", BODY_SIZE)
        marker_w = 5.0 + level * 4
        text_w = PAGE_W - 2 * MARGIN - marker_w
        lines = self.multi_cell(text_w, LINE_H, text, align="R", markdown=True,
                                dry_run=True, output="LINES")
        h = max(1, len(lines)) * LINE_H
        if self.get_y() + h > PAGE_H - 18:
            self.add_page()
        y0 = self.get_y()
        self.set_font("Amiri", "", BODY_SIZE)
        self.set_text_color(*ACCENT)
        self.set_xy(PAGE_W - MARGIN - marker_w, y0 + 0.35)
        self.cell(marker_w, LINE_H, marker, align="R")
        self.set_text_color(*INK)
        self.set_xy(MARGIN, y0)
        self.multi_cell(text_w, LINE_H, text, align="R", markdown=True,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(y0 + h)
        self.ln(0.9)

    def numbered(self, n, text):
        self.set_font("Amiri", "", BODY_SIZE)
        marker_w = 7.0
        text_w = PAGE_W - 2 * MARGIN - marker_w
        lines = self.multi_cell(text_w, LINE_H, text, align="R", markdown=True,
                                dry_run=True, output="LINES")
        h = max(1, len(lines)) * LINE_H
        if self.get_y() + h > PAGE_H - 18:
            self.add_page()
        y0 = self.get_y()
        self.set_font("Cairo", "B", 8.6)
        self.set_text_color(*ACCENT)
        self.set_xy(PAGE_W - MARGIN - marker_w, y0 + 0.4)
        self.cell(marker_w, LINE_H, "%d." % n, align="R")
        self.set_text_color(*INK)
        self.set_font("Amiri", "", BODY_SIZE)
        self.set_xy(MARGIN, y0)
        self.multi_cell(text_w, LINE_H, text, align="R", markdown=True,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(y0 + h)
        self.ln(0.9)

    def rule(self, gap=2.0):
        self.ln(gap)
        self.set_draw_color(*RULE)
        self.set_line_width(0.25)
        y = self.get_y()
        self.line(MARGIN, y, PAGE_W - MARGIN, y)
        self.ln(gap + 1.2)

    def ensure_space(self, needed):
        if self.get_y() + needed > PAGE_H - 18:
            self.add_page()

    # ------------------------------------------------------------------ boxes
    def box(self, title, lines, fill=BOX_FILL, edge=BOX_LINE, title_color=ACCENT,
            title_font="Cairo"):
        """صندوق بعنوان وداخله أسطر (نصوص / نقاط)."""
        self.ensure_space(24)
        x, w = MARGIN, PAGE_W - 2 * MARGIN
        pad = 3.0
        # تقدير الارتفاع
        heights = 6.0
        for ln in lines:
            t = ln.lstrip("-• ").strip()
            if not t:
                heights += 2
                continue
            self.set_font("Amiri", "", BODY_SIZE - 0.4)
            n = max(1, int(self.get_string_width(t) / (w - 2 * pad - 3)) + 1)
            heights += n * 4.6 + 0.9
        h = min(heights + 2, PAGE_H - 40)

        y0 = self.get_y()
        if y0 + h > PAGE_H - 18:
            self.add_page()
            y0 = self.get_y()
        self.set_fill_color(*fill)
        self.set_draw_color(*edge)
        self.set_line_width(0.3)
        self.rect(x, y0, w, h, style="DF")
        self.set_fill_color(*title_color)
        self.rect(x, y0, 2.0, h, style="F")
        if title:
            self.set_xy(x + pad + 1, y0 + 2.0)
            self.set_font(title_font, "B", 8.6)
            self.set_text_color(*title_color)
            self.multi_cell(w - 2 * pad - 1, 5.0, title, align="R",
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            yy = self.get_y() + 0.6
        else:
            yy = y0 + 2.4
        for ln in lines:
            t = ln.strip()
            if not t:
                yy += 1.4
                continue
            is_bullet = t.startswith("- ") or t.startswith("• ")
            if is_bullet:
                t = t[2:].strip()
            self.set_xy(x + pad + 1, yy)
            self.set_font("Amiri", "", BODY_SIZE - 0.4)
            self.set_text_color(*INK)
            self.multi_cell(w - 2 * pad - 4, 4.6, t, align="R", markdown=True,
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            yy = self.get_y() + 0.6
        self.set_y(max(y0 + h, self.get_y()) + 3.0)

    def table(self, headers, rows, widths=None, font_size=7.6, head_size=7.4):
        """جدول من اليمين إلى اليسار: أول عمود في البيانات يظهر أقصى اليمين."""
        n = len(headers)
        total = PAGE_W - 2 * MARGIN
        if widths is None:
            widths = [total / n] * n
        else:
            s = sum(widths)
            widths = [w * total / s for w in widths]
        xs = []
        xr = PAGE_W - MARGIN
        for w in widths:
            xs.append(xr - w)
            xr -= w
        # رأس الجدول
        self.ensure_space(14)
        self.set_fill_color(*TABLE_HEAD_FILL)
        self.set_text_color(*TABLE_HEAD_TEXT)
        self.set_font("Cairo", "B", head_size)
        y = self.get_y()
        maxh = 5.2
        cell_texts = []
        for i, htxt in enumerate(headers):
            self.set_font("Cairo", "B", head_size)
            lines = self.multi_cell(widths[i] - 1.6, 4.4, htxt, align="C",
                                    dry_run=True, output="LINES")
            cell_texts.append(lines)
            maxh = max(maxh, len(lines) * 4.4 + 1.2)
        if y + maxh > PAGE_H - 18:
            self.add_page()
            y = self.get_y()
        self.set_fill_color(*TABLE_HEAD_FILL)
        self.rect(MARGIN, y, total, maxh, style="F")
        for i, lines in enumerate(cell_texts):
            self.set_xy(xs[i] + 0.8, y + (maxh - len(lines) * 4.4) / 2)
            for ln in lines:
                self.set_x(xs[i] + 0.8)
                self.cell(widths[i] - 1.6, 4.4, ln, align="C")
                self.ln(4.4)
        self.set_y(y + maxh)

        # الصفوف
        for r, row in enumerate(rows):
            self.set_font("Amiri", "", font_size)
            cells = [str(c) for c in row]
            heights = []
            wrapped = []
            for i, c in enumerate(cells):
                self.set_font("Amiri", "", font_size)
                lines = self.multi_cell(widths[i] - 1.6, 4.4, c, align="R",
                                        dry_run=True, output="LINES")
                wrapped.append(lines)
                heights.append(len(lines) * 4.4 + 1.2)
            h = max(heights + [5.2])
            if self.get_y() + h > PAGE_H - 18:
                self.add_page()
                # إعادة رأس الجدول
                self.set_fill_color(*TABLE_HEAD_FILL)
                self.set_text_color(*TABLE_HEAD_TEXT)
                self.set_font("Cairo", "B", head_size)
                yhead = self.get_y()
                mh = 5.2
                for i, htxt in enumerate(headers):
                    self.set_font("Cairo", "B", head_size)
                    lines = self.multi_cell(widths[i] - 1.6, 4.4, htxt,
                                            align="C", dry_run=True, output="LINES")
                    mh = max(mh, len(lines) * 4.4 + 1.2)
                self.rect(MARGIN, yhead, total, mh, style="F")
                for i, htxt in enumerate(headers):
                    self.set_font("Cairo", "B", head_size)
                    lines = self.multi_cell(widths[i] - 1.6, 4.4, htxt,
                                            align="C", dry_run=True, output="LINES")
                    self.set_xy(xs[i] + 0.8, yhead + (mh - len(lines) * 4.4) / 2)
                    for ln in lines:
                        self.set_x(xs[i] + 0.8)
                        self.cell(widths[i] - 1.6, 4.4, ln, align="C")
                        self.ln(4.4)
                self.set_y(yhead + mh)
            y0 = self.get_y()
            if r % 2 == 1:
                self.set_fill_color(*TABLE_ALT)
                self.rect(MARGIN, y0, total, h, style="F")
            self.set_draw_color(*RULE)
            self.set_line_width(0.15)
            self.line(MARGIN, y0 + h, PAGE_W - MARGIN, y0 + h)
            self.set_text_color(*INK)
            for i, lines in enumerate(wrapped):
                self.set_xy(xs[i] + 0.8, y0 + 0.6)
                for ln in lines:
                    self.set_x(xs[i] + 0.8)
                    self.set_font("Amiri", "", font_size)
                    self.cell(widths[i] - 1.6, 4.4, ln, align="R")
                    self.ln(4.4)
            self.set_y(y0 + h)
        self.ln(3.0)

    def dialogue(self, lines, who_w=26):
        """محادثة نموذجية: سطر (الزبون: ...) / (أنت: ...)."""
        total = PAGE_W - 2 * MARGIN
        for ln in lines:
            self.ensure_space(9)
            if ":" in ln or "：" in ln:
                who, txt = re.split(r"[:：]", ln, maxsplit=1)
            else:
                who, txt = "", ln
            y0 = self.get_y()
            self.set_font("Cairo", "B", 7.8)
            self.set_text_color(*ACCENT)
            self.set_xy(PAGE_W - MARGIN - who_w, y0)
            self.cell(who_w, LINE_H, who.strip(), align="R")
            self.set_xy(MARGIN, y0)
            self.set_font("Amiri", "", BODY_SIZE - 0.3)
            self.set_text_color(*INK)
            self.multi_cell(total - who_w - 1, LINE_H, txt.strip(), align="R",
                            markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1.2)
        self.ln(2.0)

    def fill_lines(self, n=4, label=""):
        """أسطر للكتابة بالقلم (دفتر العمل)."""
        if label:
            self.ensure_space(12)
            self.set_font("Cairo", "B", 8.6)
            self.set_text_color(*ACCENT)
            self.multi_cell(PAGE_W - 2 * MARGIN, 5.4, label, align="R",
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1.0)
        self.set_draw_color(*BOX_LINE)
        self.set_line_width(0.25)
        for _ in range(n):
            self.ensure_space(9)
            y = self.get_y() + 6.5
            self.line(MARGIN, y, PAGE_W - MARGIN, y)
            self.set_y(y + 2.5)
        self.ln(2.0)

    def fill_row(self, label, n=2):
        """سطر بطاقة: عنوان + سطر كتابة."""
        self.ensure_space(12)
        self.set_font("Cairo", "B", 8.4)
        self.set_text_color(*INK)
        self.multi_cell(PAGE_W - 2 * MARGIN, 5.0, label, align="R",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BOX_LINE)
        for _ in range(n):
            self.ensure_space(9)
            y = self.get_y() + 6.0
            self.line(MARGIN, y, PAGE_W - MARGIN, y)
            self.set_y(y + 2.0)
        self.ln(2.0)


# ============================================================================ parser
LABELS = {
    "درس": ("درس التجربة", ACCENT),
    "خطأ": ("خطأ شائع", (168, 50, 40)),
    "تطبيق": ("التطبيق: شنو دير دابا", (35, 110, 70)),
    "تمرين": ("تمرين بالقلم", (35, 110, 70)),
    "مثال": ("مثال افتراضي للتوضيح", (90, 60, 150)),
    "حقيقية": ("تجربة حقيقية موثقة", (25, 90, 130)),
    "سيناريو": ("سيناريو تطبيقي", (120, 90, 20)),
    "مكانه": ("لو كنت مكانه...", (140, 60, 30)),
    "ملاحظة": ("ملاحظة", GREY),
    "قاعدة": ("قاعدة", (140, 40, 40)),
    "تحليل": ("تحليل تعليمي", (80, 80, 120)),
    "تنبيه": ("تنبيه", (168, 50, 40)),
    "خلاصة": ("خلاصة", ACCENT),
    "سوق": ("من السوق المغربي", (25, 90, 130)),
    "مصدر": ("المصدر", GREY),
    "مشروع": ("بطاقة المشروع", ACCENT),
    "ميزانية": ("الميزانية بالأرقام", (35, 110, 70)),
    "نتيجة": ("النتيجة بالأرقام", (35, 110, 70)),
    "مقارنة": ("مقارنة", GREY),
    "خطوة": ("الخطوة التالية", ACCENT),
    "يوميات": ("يوميات المشروع", (120, 90, 20)),
    "حوار": ("", ACCENT),
}


def render_toc(pdf: Book, entries):
    """entries: list of (level, title, page)."""
    pdf.add_page()
    pdf.show_furniture = True
    pdf.running_head = "المحتويات"
    pdf.set_y(24)
    pdf.set_font("Cairo", "B", 15)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(PAGE_W - 2 * MARGIN, 8.5, "المحتويات", align="R",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.5)
    y = pdf.get_y() + 1
    pdf.line(PAGE_W - MARGIN - 34, y, PAGE_W - MARGIN, y)
    pdf.ln(4)
    total = PAGE_W - 2 * MARGIN
    for lvl, title, pg in entries:
        pdf.ensure_space(8)
        if lvl == 1:
            pdf.set_font("Cairo", "B", 9.4)
            pdf.set_text_color(*ACCENT)
            h = 6.4
        else:
            pdf.set_font("Amiri", "", 8.6)
            pdf.set_text_color(*INK)
            h = 5.6
        y0 = pdf.get_y()
        pdf.set_xy(MARGIN, y0)
        pdf.multi_cell(total - 16, h, title, align="R",
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        yend = pdf.get_y()
        pdf.set_xy(MARGIN, y0)
        pdf.set_font("Cairo", "", 8.4)
        pdf.set_text_color(*GREY)
        pdf.cell(16, h, str(pg), align="L")
        pdf.set_y(yend)
        if lvl == 1:
            pdf.ln(1.2)
    pdf.ln(4)


GLYPH_FIX = str.maketrans({
    "→": "»", "⇒": "»", "←": "«",
    "☐": "[ ]", "✓": "[x]", "✔": "[x]",
    "□": "[ ]", "≈": "~", "≥": "≥ ",  # ≥ يُستبدل أدناه بنص
})


def render(pdf: Book, text: str):
    text = text.translate(GLYPH_FIX)
    text = text.replace("≥ ", "لا تقل عن ").replace("≥", "لا تقل عن ")
    lines = text.split("\n")
    i = 0
    n = len(lines)
    num_counter = 0
    while i < n:
        line = lines[i].rstrip()
        s = line.strip()
        i += 1

        if not s:
            num_counter = 0
            continue

        # ---- أوامر
        if s == "@rule":
            pdf.rule()
            continue
        if s == "@pagebreak":
            pdf.add_page()
            continue
        if s == "@toc":
            render_toc(pdf, pdf.toc_entries)
            continue
        if s.startswith("@cover"):
            cov = []
            while i < n and lines[i].strip() and not lines[i].strip().startswith(("@", "#", "::", "|")):
                cov.append(lines[i].strip())
                i += 1
            t = cov[0] if cov else pdf.book_title
            sub = cov[1] if len(cov) > 1 else ""
            ftr = cov[2] if len(cov) > 2 else ""
            pdf.render_cover(t, sub, ftr)
            pdf.show_furniture = True
            pdf.running_head = t
            pdf._skip_break = True
            continue

        # ---- ملء بالقلم (قبل المربعات حتى لا يُفسَر كمربع)
        m = re.match(r"^::fill\s+(\d+)\s*(.*)$", s)
        if m:
            pdf.fill_lines(int(m.group(1)), m.group(2).strip())
            continue
        m = re.match(r"^::row\s+(.*)$", s)
        if m:
            pdf.fill_row(m.group(1).strip())
            continue

        # ---- مربعات
        m = re.match(r"^::\s*(\S+)\s*(.*)$", s)
        if m:
            key = m.group(1)
            title = m.group(2).strip()
            body = []
            while i < n:
                t = lines[i].strip()
                if t == "::end":
                    i += 1
                    break
                if t.startswith("#") or (t.startswith("::") and not t.startswith("::end")):
                    break
                if t:
                    body.append(t)
                i += 1
            label, color = LABELS.get(key, (title or key, ACCENT))
            if title and key in LABELS:
                label = "%s — %s" % (label, title)
            elif title:
                label = title
            if key == "حوار":
                pdf.box(label, body, fill=BOX_FILL2, title_color=color)
            else:
                pdf.box(label, body, title_color=color)
            continue

        # ---- جداول
        if s.startswith("|"):
            tbl = []
            while i - 1 < n and lines[i - 1].strip().startswith("|"):
                tbl.append(lines[i - 1].strip())
                i += 1
            rows = []
            for r in tbl:
                cells = [c.strip() for c in r.strip("|").split("|")]
                if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    continue
                rows.append(cells)
            if rows:
                pdf.table(rows[0], rows[1:])
            continue

        # ---- محادثة
        if s.startswith(">>"):
            conv = []
            while i - 1 < n and lines[i - 1].strip().startswith(">>"):
                conv.append(lines[i - 1].strip()[2:].strip())
                i += 1
            pdf.dialogue(conv)
            continue

        # ---- عناوين
        if s.startswith("#### "):
            pdf.h3(s[5:].strip())
            continue
        if s.startswith("### "):
            pdf.h3(s[4:].strip())
            continue
        if s.startswith("## "):
            t = s[3:].strip()
            if not pdf.show_furniture:
                pdf.show_furniture = True
            pdf.running_head = t
            if getattr(pdf, "_skip_break", False):
                pdf._skip_break = False
                pdf.set_y(24)
            else:
                pdf.add_page()
                pdf.set_y(28)
            pdf.h1(t)
            pdf.toc.append((2, t, pdf.page_no()))
            continue
        if s.startswith("# "):
            title = s[2:].strip()
            pdf.show_furniture = True
            pdf.running_head = title
            pdf.add_page()
            pdf.set_y(34)
            pdf.h1(title)
            pdf.toc.append((1, title, pdf.page_no()))
            continue

        # ---- نقاط
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            pdf.bullet(m.group(1).strip(), level=0)
            num_counter = 0
            continue
        m = re.match(r"^>\s+[-*]\s+(.*)$", s)
        if m:
            pdf.bullet(m.group(1).strip(), level=1, marker="·")
            continue

        # ---- ترقيم
        m = re.match(r"^\d+[.)]\s+(.*)$", s)
        if m:
            num_counter += 1
            pdf.numbered(num_counter, m.group(1).strip())
            continue

        # ---- نص عادي
        num_counter = 0
        pdf.para(s)


def build(out_pdf, files, title, author):
    """يتكرر حتى تستقر أرقام صفحات الفهرس."""
    entries = []
    pdf = None
    for _ in range(6):
        pdf = Book(title, author)
        pdf.toc_entries = list(entries)
        for f in files:
            with open(f, encoding="utf-8") as fh:
                render(pdf, fh.read())
        new_entries = list(pdf.toc)
        if new_entries == entries:
            break
        entries = new_entries
    pdf.output(out_pdf)
    return pdf.page_no()


if __name__ == "__main__":
    src = sys.argv[1]
    out = sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        p = Book("اختبار", "اختبار")
        p.show_furniture = True
        render(p, fh.read())
        p.output(out)
    print("pages:", p.page_no())
