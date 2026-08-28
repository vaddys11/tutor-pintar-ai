"""
export.py — Generate PDF catatan belajar dari riwayat chat Tutor Pintar AI.
"""
from datetime import datetime
from fpdf import FPDF


class CatatanBelajarPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(67, 56, 202)  # indigo-700
        self.cell(0, 10, "Catatan Belajar - Tutor Pintar AI", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, datetime.now().strftime("%d %B %Y, %H:%M"), ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Halaman {self.page_no()}", align="C")


def _clean(text: str) -> str:
    """Buang karakter yang gak kompatibel sama font Helvetica standar (latin-1)."""
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_pdf(messages: list[dict], jenjang: str, session_id: str) -> bytes:
    """Bikin PDF dari riwayat chat. Return bytes, siap dipakai st.download_button."""
    pdf = CatatanBelajarPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, _clean(f"Jenjang: {jenjang}"), ln=True)
    pdf.cell(0, 8, _clean(f"Kode Sesi: {session_id}"), ln=True)
    pdf.ln(4)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    for msg in messages:
        role = msg["role"]
        content = _clean(msg["content"])
        label = "Kamu" if role == "user" else "Tutor Pintar"
        color = (79, 70, 229) if role == "user" else (5, 150, 105)  # indigo / emerald

        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*color)
        pdf.cell(0, 6, label + ":", ln=True)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 6, content)
        pdf.ln(3)

    return bytes(pdf.output())
