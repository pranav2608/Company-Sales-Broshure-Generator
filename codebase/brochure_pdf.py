from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from fpdf import FPDF

NAVY = (18, 36, 71)
GOLD = (196, 149, 58)
CREAM = (250, 246, 238)
CHARCOAL = (36, 36, 40)
TEAL = (27, 94, 108)
MUTED = (110, 110, 118)
WHITE = (255, 255, 255)

MARGIN = 18
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "brochures"

_INLINE = re.compile(r"(\*\*[^*]+?\*\*|__[^_]+?__|\*[^*]+?\*|_[^_]+?_)")
_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")
_UL = re.compile(r"^[-*+]\s+(.*)$")
_OL = re.compile(r"^(\d+)[.)]\s+(.*)$")
_HR = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")


def _font_files() -> tuple[str, str, str]:
    regular_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    bold_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]
    italic_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Italic.ttf"),
        Path("/Library/Fonts/Arial Italic.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
        Path("C:/Windows/Fonts/ariali.ttf"),
    ]

    regular = next((p for p in regular_candidates if p.exists()), None)
    if regular is None:
        raise FileNotFoundError("No Unicode TTF font found for brochure PDFs.")

    bold = next((p for p in bold_candidates if p.exists()), regular)
    italic = next((p for p in italic_candidates if p.exists()), regular)
    return str(regular), str(bold), str(italic)


class BrochurePDF(FPDF):
    def __init__(self, company_name: str) -> None:
        super().__init__(format="A4", unit="mm")
        self.company_name = company_name
        regular, bold, italic = _font_files()
        self.add_font("Brochure", "", regular)
        self.add_font("Brochure", "B", bold)
        self.add_font("Brochure", "I", italic)
        self.set_auto_page_break(auto=True, margin=22)
        self.set_top_margin(30)
        self.set_left_margin(MARGIN)
        self.set_right_margin(MARGIN)
        self.set_fill_color(*CREAM)

    def header(self) -> None:
        self.set_fill_color(*CREAM)
        self.rect(0, 0, self.w, self.h, "F")
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 24, "F")
        self.set_fill_color(*GOLD)
        self.rect(0, 24, self.w, 2.4, "F")
        self.set_text_color(*WHITE)
        self.set_font("Brochure", "B", 12)
        self.set_xy(MARGIN, 7)
        self.cell(self.w - 2 * MARGIN - 40, 8, self.company_name.upper())
        self.set_font("Brochure", "", 8)
        self.set_xy(self.w - MARGIN - 40, 8)
        self.cell(40, 8, "SALES BROCHURE", align="R")
        self.set_y(32)
        self.set_text_color(*CHARCOAL)

    def footer(self) -> None:
        self.set_y(-16)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.45)
        self.line(MARGIN, self.get_y(), self.w - MARGIN, self.get_y())
        self.set_text_color(*MUTED)
        self.set_font("Brochure", "", 8)
        self.cell(
            0,
            10,
            f"{self.company_name}  ·  {date.today():%d %b %Y}  ·  Page {self.page_no()}",
            align="C",
        )

    def _usable_width(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def write_inline(self, text: str, size: float = 11) -> None:
        parts = _INLINE.split(text)
        for part in parts:
            if not part:
                continue
            if (part.startswith("**") and part.endswith("**")) or (
                part.startswith("__") and part.endswith("__")
            ):
                self.set_font("Brochure", "B", size)
                self.write(6.2, part[2:-2])
            elif (part.startswith("*") and part.endswith("*")) or (
                part.startswith("_") and part.endswith("_")
            ):
                self.set_font("Brochure", "I", size)
                self.write(6.2, part[1:-1])
            else:
                self.set_font("Brochure", "", size)
                self.write(6.2, part)
        self.set_font("Brochure", "", size)
        self.ln(7.2)

    def add_h1(self, text: str) -> None:
        self.set_text_color(*NAVY)
        self.set_font("Brochure", "B", 20)
        self.multi_cell(self._usable_width(), 9, text)
        self.set_draw_color(*GOLD)
        self.set_line_width(1.1)
        y = self.get_y() + 1
        self.line(self.l_margin, y, self.l_margin + 36, y)
        self.ln(8)
        self.set_text_color(*CHARCOAL)

    def add_h2(self, text: str) -> None:
        self.ln(2)
        self.set_fill_color(*TEAL)
        x, y = self.l_margin, self.get_y()
        self.rect(x, y, 3.2, 8.5, "F")
        self.set_xy(x + 6, y)
        self.set_text_color(*TEAL)
        self.set_font("Brochure", "B", 13.5)
        self.multi_cell(self._usable_width() - 6, 8.5, text.upper())
        self.ln(2)
        self.set_text_color(*CHARCOAL)

    def add_h3(self, text: str) -> None:
        self.set_text_color(*NAVY)
        self.set_font("Brochure", "B", 12)
        self.multi_cell(self._usable_width(), 7, text)
        self.ln(1)
        self.set_text_color(*CHARCOAL)

    def add_hr(self) -> None:
        self.ln(2)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(5)

    def add_bullet(self, text: str, ordered: str | None = None) -> None:
        marker = f"{ordered}." if ordered else "•"
        x = self.l_margin
        self.set_x(x)
        self.set_font("Brochure", "B", 11)
        self.set_text_color(*GOLD)
        self.cell(8, 6.2, marker)
        self.set_text_color(*CHARCOAL)
        self.set_x(x + 8)
        self.write_inline(text, size=11)


def _normalize_markdown(markdown_text: str) -> str:
    text = markdown_text.strip()
    text = re.sub(r"^```(?:markdown)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.replace("\r\n", "\n")


def render_markdown(pdf: BrochurePDF, markdown_text: str) -> None:
    first_heading = True
    for raw in _normalize_markdown(markdown_text).split("\n"):
        line = raw.strip()
        if not line:
            pdf.ln(2)
            continue

        heading = _HEADING.match(line)
        if heading:
            level, title = len(heading.group(1)), heading.group(2).strip()
            if level == 1:
                pdf.add_h1(title)
                first_heading = False
            elif level == 2:
                pdf.add_h2(title)
            else:
                pdf.add_h3(title)
            continue

        if _HR.match(line):
            pdf.add_hr()
            continue

        unordered = _UL.match(line)
        if unordered:
            pdf.add_bullet(unordered.group(1))
            continue

        ordered = _OL.match(line)
        if ordered:
            pdf.add_bullet(ordered.group(2), ordered=ordered.group(1))
            continue

        if first_heading:
            pdf.add_h1(line)
            first_heading = False
            continue

        pdf.write_inline(line, size=11)


def save_brochure_pdf(
    markdown_text: str,
    company_name: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Turn brochure markdown into a coloured PDF and save it under brochures/."""
    folder = Path(output_dir) if output_dir else OUTPUT_DIR
    folder.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", company_name).strip("-").lower() or "brochure"
    path = folder / f"{slug}-brochure.pdf"

    pdf = BrochurePDF(company_name)
    pdf.add_page()
    render_markdown(pdf, markdown_text)
    pdf.output(str(path))
    return path
