"""PDF-Zusammenfassung der aktuellen Einstellungen und Befunde (fpdf2, Kernschrift Helvetica: nur Zeichen aus Latin-1)."""

from fpdf import FPDF

ERSATZ = {"½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4", "⅕": "1/5", "⅙": "1/6", "≤": "<=", "≥": ">=", "₂": "2",
          "⌈": "aufgerundet(", "⌉": ")", "⌊": "abgerundet(", "⌋": ")", "−": "-", "–": "-", "—": "-", "„": '"', "“": '"', "”": '"',
          "’": "'", "×": "x", "→": "->", "…": "...", "√": "Wurzel", "α": "alpha", "β": "beta", "**": ""}


def latin1(text: str) -> str:
    """Zeichen ersetzen, die Helvetica nicht darstellen kann; was dann noch fehlt, meldet die Funktion als Fehler."""
    for alt, neu in ERSATZ.items():
        text = text.replace(alt, neu)
    text.encode("latin-1")
    return text


def erzeuge_pdf(abschnitte) -> bytes:
    """abschnitte: [(Überschrift, [Absätze])]."""
    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()

    def zeile(text, groesse=11, stil="", hoehe=6):
        pdf.set_font("Helvetica", stil, groesse)
        pdf.multi_cell(0, hoehe, latin1(text), new_x="LMARGIN", new_y="NEXT")

    zeile("Chvátal-Gomory: fehlende Ungleichungen durch Abrunden", 15, "B", 9)
    for titel, absaetze in abschnitte:
        pdf.ln(2)
        zeile(titel, 12, "B", 7)
        for a in absaetze:
            zeile(a, 10, "", 5)
    pdf.ln(3)
    zeile("Schnitte mit Brüchen nachgerechnet; LP und Suche mit HiGHS (scipy). Ausgedachte Beispielgraphen, keine echten Daten.",
          9, "I", 5)
    return bytes(pdf.output())
