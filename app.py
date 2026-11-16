import io
import re
import html
import numpy as np
import streamlit as st
from PIL import Image, ImageFilter, ImageOps

# =========================================================
# 1. STREAMLIT CONFIG & DESIGN
# =========================================================
st.set_page_config(
    page_title="MedicalAssistant – Professional Edition",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }
        #MainMenu, footer { visibility: hidden !important; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 4rem !important; max-width: 950px !important; }
        .hero-banner {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #0f766e 100%);
            border-radius: 20px; padding: 28px 36px; color: #ffffff;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3); margin-bottom: 20px;
        }
        .hero-banner h1 { font-weight: 800; font-size: 2.2rem; margin: 0; color: #ffffff !important; }
        .hero-banner p { color: #e0f2fe; font-size: 1rem; margin-top: 6px; margin-bottom: 0; }
        .disclaimer-box {
            background-color: #fef3c7; border-left: 5px solid #d97706;
            padding: 12px 18px; border-radius: 10px; font-size: 0.88rem; color: #92400e; margin-bottom: 20px;
        }
        .card {
            background: #ffffff; border-radius: 16px; padding: 24px;
            border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); margin-bottom: 18px;
        }
        .befund-box {
            background: #e0f2fe; padding: 12px; border-radius: 10px; font-size: 0.95rem;
            color: #0369a1; border-left: 4px solid #0284c7; margin-bottom: 12px;
        }
        .emergency-btn {
            display: inline-block; background-color: #dc2626; color: white !important;
            font-weight: 700; padding: 12px 20px; border-radius: 10px; text-decoration: none; margin-right: 10px; margin-top: 8px;
        }
        .bereitschaft-btn {
            display: inline-block; background-color: #0284c7; color: white !important;
            font-weight: 700; padding: 12px 20px; border-radius: 10px; text-decoration: none; margin-top: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 2. KONSTANTEN
# =========================================================
SYMPTOM_OPTIONEN = [
    "Bitte wählen...",
    "Blauer Fleck / Hämatom / Prellung",
    "Hautausschlag / Rötung / Schwellung / Wunde",
    "Gelenk- oder Gliederschmerzen / Sportverletzung",
    "Schnittwunde / Verbrennung / Äußere Verletzung",
    "Kopfschmerzen / Migräne / Schwindel",
    "Erkältung / Halsschmerzen / Husten / Fieber",
    "Magen-Darm-Beschwerden / Übelkeit",
    "Brustschmerzen / Engegefühl (Kardial)",
    "Plötzliche Atemnot / Luftnot",
    "Sonstiges / Allgemeine Beschwerden",
]
KATEGORIEN_NOTFALL = {
    "Brustschmerzen / Engegefühl (Kardial)",
    "Plötzliche Atemnot / Luftnot",
}
KATEGORIEN_VERLETZUNG = {
    "Blauer Fleck / Hämatom / Prellung",
    "Hautausschlag / Rötung / Schwellung / Wunde",
    "Gelenk- oder Gliederschmerzen / Sportverletzung",
    "Schnittwunde / Verbrennung / Äußere Verletzung",
}
KATEGORIEN_IMMER_ABKLAEREN = {"Schnittwunde / Verbrennung / Äußere Verletzung"}

DAUER_OPTIONEN = [
    "Wenige Minuten / Akut",
    "Wenige Stunden",
    "1 bis 2 Tage",
    "3 bis 5 Tage",
    "Länger als eine Woche",
]
SCHWERE_OPTIONEN = ["Leicht (1-3)", "Mäßig (4-7)", "Sehr stark / Unerträglich (8-10)"]

MODUS_AUTO = "Automatische Bildanalyse (Standard)"
MODUS_OK = "🟢 Manuell: Unauffällige Struktur"
MODUS_AUFFAELLIG = "🟡 Manuell: Hämatom / Rötung / Schwellung"
MODUS_OFFEN = "🔴 Manuell: Akute offene Verletzung"
MODUS_OPTIONEN = [MODUS_AUTO, MODUS_OK, MODUS_AUFFAELLIG, MODUS_OFFEN]

# Notfall-Schlüsselwörter (Stammformen, damit Beugungen mitgefangen werden)
NOTFALL_KEYWORDS = [
    "bewusstlos", "ohnmacht", "atemnot", "luftnot", "atembeschwerden",
    "brustschmerz", "brustenge", "engegefühl", "schlaganfall", "lähmung",
    "sprachstörung", "krampfanfall", "stark blutend", "starke blutung",
    "blutet stark", "kollaps", "kopfverletzung", "schädel", "gehirnerschütterung",
    "herzinfarkt", "anaphyla", "zunge geschwollen", "erstick",
]
# Hinweise, die mindestens eine ärztliche Abklärung nahelegen
AUFFAELLIG_KEYWORDS = [
    "blauer fleck", "blaue flecken", "hämatom", "prellung", "wunde", "schnitt",
    "schwellung", "geschwollen", "blutverdünner", "marcumar", "xarelto",
    "eliquis", "sturz", "gestürzt", "großflächig", "verfärb", "eiter",
    "überwärmt", "fieber", "bluterguss", "umgeknickt", "verbrenn",
]
NEGATIONEN = ("kein", "keine", "keinen", "keiner", "ohne", "nicht", "nie ")

# =========================================================
# 3. HILFSFUNKTIONEN
# =========================================================
def esc(text: str) -> str:
    """Nutzereingaben für HTML maskieren (verhindert kaputtes Layout / Injection)."""
    return html.escape(text or "", quote=True)


def hat_keyword(text: str, keyword: str) -> bool:
    """Prüft ein Keyword im Text und ignoriert einfache Verneinungen ('keine Atemnot')."""
    for m in re.finditer(re.escape(keyword), text):
        davor = text[max(0, m.start() - 18): m.start()]
        if any(neg in davor for neg in NEGATIONEN):
            continue
        return True
    return False


def finde_keywords(text: str, keywords) -> list:
    return [kw for kw in keywords if hat_keyword(text, kw)]


def rgb_zu_lab(arr: np.ndarray) -> np.ndarray:
    """Wandelt ein RGB-Array (0-255, float) in den CIE-Lab-Farbraum um (D65)."""
    c = arr / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array(
        [[0.4124564, 0.3575761, 0.1804375],
         [0.2126729, 0.7151522, 0.0721750],
         [0.0193339, 0.1191920, 0.9503041]],
        dtype=np.float32,
    )
    xyz = c @ m.T
    xyz /= np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    lab_l = 116.0 * f[..., 1] - 16.0
    lab_a = 500.0 * (f[..., 0] - f[..., 1])
    lab_b = 200.0 * (f[..., 1] - f[..., 2])
    return np.stack([lab_l, lab_a, lab_b], axis=-1)


def analysiere_bild(datei_bytes: bytes) -> dict:
    """
    Beleuchtungsrobuste Bildanalyse.

    Prinzip: Statt fester Helligkeitsgrenzen wird jedes Pixel mit der Median-Hautfarbe
    des jeweiligen Fotos verglichen (Lab-Farbraum). Dadurch wirken unterschiedliche
    Belichtung und Weißabgleich deutlich weniger. Abweichende Bereiche werden nach
    Farbton in Rötung, Hämatom (dunkel/bläulich/violett bzw. gelb-grün) eingeteilt.

    Sicherheitsprinzip: Ein Bild kann NIEMALS allein ein Ergebnis "alles gut" erzeugen.
    Ist die Bildqualität schlecht, wird 'unsicher' gemeldet.

    Rückgabe: dict(auffaellig: bool, unsicher: bool, text: str, details: str)
    """
    ergebnis = {"auffaellig": False, "unsicher": True, "text": "", "details": ""}
    try:
        img = Image.open(io.BytesIO(datei_bytes))
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((320, 320))
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        arr = np.asarray(img, dtype=np.float32)

        h, w = arr.shape[:2]
        if h < 40 or w < 40:
            ergebnis["text"] = "Visueller Befund: Bild zu klein für eine Auswertung."
            return ergebnis

        # Zentralen Bereich (ca. 80 %) betrachten, Ränder oft Hintergrund
        y0, y1 = int(h * 0.1), int(h * 0.9)
        x0, x1 = int(w * 0.1), int(w * 0.9)
        zentrum = arr[y0:y1, x0:x1]

        helligkeit = zentrum.mean()
        grau = np.asarray(Image.fromarray(zentrum.astype(np.uint8)).convert("L"), dtype=np.float32)
        schaerfe = float(np.var(np.diff(grau, axis=0))) + float(np.var(np.diff(grau, axis=1)))

        lab = rgb_zu_lab(zentrum)
        l_k, a_k, b_k = lab[..., 0], lab[..., 1], lab[..., 2]

        # Glanzlichter und tiefschwarze Pixel ausblenden
        gueltig = (l_k > 12) & (l_k < 94)
        anteil_gueltig = float(gueltig.mean())
        if anteil_gueltig < 0.4 or helligkeit < 35 or helligkeit > 230:
            ergebnis["text"] = (
                "Visueller Befund: Bildqualität nicht ausreichend (zu dunkel, überbelichtet oder unscharf) "
                "– automatische Beurteilung nicht möglich."
            )
            return ergebnis

        # Referenz = Median der Hautfarbe dieses Fotos
        l0 = np.median(l_k[gueltig])
        a0 = np.median(a_k[gueltig])
        b0 = np.median(b_k[gueltig])

        d_l, d_a, d_b = l_k - l0, a_k - a0, b_k - b0
        delta_e = np.sqrt(d_l ** 2 + d_a ** 2 + d_b ** 2)
        abw = (delta_e > 12) & gueltig

        # Typen von Abweichungen
        rot = abw & (d_a > 7) & (d_l > -18)                      # Rötung / Entzündung
        dunkel_blau = abw & (d_l < -8) & (d_a < 12) & (d_b < 4)  # Hämatom: dunkel, bläulich / violett
        gelb_gruen = abw & (d_b > 11) & (d_a < 6)                # Hämatom: abklingend (gelb-grün)
        sehr_dunkel = abw & (d_l < -22)                          # starke Abdunklung

        n = float(gueltig.sum())
        f_rot = float(rot.sum()) / n
        f_blau = float((dunkel_blau | sehr_dunkel).sum()) / n
        f_gelb = float(gelb_gruen.sum()) / n
        f_gesamt = float(abw.sum()) / n

        details = (
            f"Abweichung gesamt {f_gesamt:.0%}, Rötung {f_rot:.0%}, "
            f"dunkel/bläulich {f_blau:.0%}, gelb-grün {f_gelb:.0%}, Schärfemaß {schaerfe:.0f}"
        )
        ergebnis["details"] = details

        befunde = []
        if f_blau > 0.04 or f_gelb > 0.05:
            befunde.append("Verfärbung im Sinne eines Hämatoms (blauer Fleck / Prellung)")
        if f_rot > 0.05:
            befunde.append("lokale Rötung (mögliche Entzündungs- oder Reizzeichen)")
        if not befunde and f_gesamt > 0.10:
            befunde.append("auffällige Farbabweichung im Hautbereich")

        if befunde:
            ergebnis["auffaellig"] = True
            ergebnis["unsicher"] = False
            ergebnis["text"] = "Visueller Befund: " + "; ".join(befunde) + " erkannt."
        elif schaerfe < 15:
            ergebnis["text"] = (
                "Visueller Befund: Bild sehr unscharf – keine verlässliche automatische Aussage möglich."
            )
        else:
            ergebnis["unsicher"] = False
            ergebnis["text"] = (
                "Visueller Befund: Keine eindeutige Farbauffälligkeit erkannt. "
                "Dies schließt eine Verletzung NICHT aus."
            )
        return ergebnis

    except Exception:
        ergebnis["text"] = "Visueller Befund: Bild konnte nicht ausgewertet werden."
        return ergebnis


def berechne_triage(eingaben: dict) -> dict:
    """
    Kombiniert Symptomkategorie, Freitext, Schweregrad, Dauer und Bildbefund.
    Stufen: 0 = grün, 1 = gelb (ärztliche Abklärung), 2 = rot (Notfall).

    Regeln:
    - Die höchste Stufe aus allen Quellen gewinnt.
    - Ein manueller Override kann die Stufe nur ERHÖHEN, nie unter das Ergebnis
      aus Symptomen/Freitext senken (kein widersprüchlicher "alles gut"-Befund).
    """
    kategorie = eingaben["kategorie"]
    schwere = eingaben["schwere"]
    dauer = eingaben["dauer"]
    modus = eingaben["modus"]
    text = " ".join(
        [kategorie, eingaben["hergang"], eingaben["notizen"]]
    ).lower()

    stufe = 0
    gruende = []

    # --- Stufe 2: Notfall ---
    treffer_notfall = finde_keywords(text, NOTFALL_KEYWORDS)
    if kategorie in KATEGORIEN_NOTFALL:
        stufe = 2
        gruende.append(f"Gewählte Hauptbeschwerde „{kategorie}“ gilt als potenzieller Notfall.")
    if treffer_notfall:
        stufe = 2
        gruende.append("Notfall-Hinweise im Text: " + ", ".join(sorted(set(treffer_notfall))) + ".")
    if modus == MODUS_OFFEN:
        stufe = 2
        gruende.append("Manuell gewählt: akute offene Verletzung.")

    # --- Bildbefund ---
    bild_log = "Kein Bild hochgeladen."
    bild_unsicher = False
    bild_auffaellig = False
    bild_details = ""

    if modus == MODUS_OK:
        bild_log = "Visueller Befund (manuell vom Anwender gesetzt): Gewebestruktur unauffällig."
    elif modus == MODUS_AUFFAELLIG:
        bild_auffaellig = True
        bild_log = "Visueller Befund (manuell): Deutliche Gewebeverfärbung / Hämatom / Rötung / Schwellung."
    elif modus == MODUS_OFFEN:
        bild_auffaellig = True
        bild_log = "Visueller Befund (manuell): Akute Läsion / offene Verletzung."
    else:
        if eingaben["bild_bytes"] is not None:
            res = analysiere_bild(eingaben["bild_bytes"])
            bild_log = res["text"]
            bild_details = res["details"]
            bild_auffaellig = res["auffaellig"]
            bild_unsicher = res["unsicher"]
        elif kategorie in KATEGORIEN_VERLETZUNG:
            bild_log = "Kein Bild hochgeladen – Einschätzung nur anhand der Angaben."

    if bild_auffaellig:
        stufe = max(stufe, 1)
        gruende.append("Bildbefund auffällig.")

    # --- Stufe 1: ärztliche Abklärung ---
    treffer_auffaellig = finde_keywords(text, AUFFAELLIG_KEYWORDS)
    if treffer_auffaellig:
        stufe = max(stufe, 1)
        gruende.append("Hinweise in Beschreibung/Notizen: " + ", ".join(sorted(set(treffer_auffaellig))) + ".")

    if schwere == SCHWERE_OPTIONEN[2]:
        stufe = max(stufe, 1)
        gruende.append("Sehr starke Schmerzen / Intensität (8–10).")

    if kategorie in KATEGORIEN_IMMER_ABKLAEREN:
        stufe = max(stufe, 1)
        gruende.append("Schnittwunden, Verbrennungen und äußere Verletzungen sollten ärztlich beurteilt werden.")

    if kategorie in KATEGORIEN_VERLETZUNG and schwere != SCHWERE_OPTIONEN[0]:
        stufe = max(stufe, 1)
        gruende.append("Verletzungsbedingte Beschwerden mit mindestens mäßiger Intensität.")

    if dauer == DAUER_OPTIONEN[4] and kategorie != "Sonstiges / Allgemeine Beschwerden":
        stufe = max(stufe, 1)
        gruende.append("Beschwerden bestehen seit mehr als einer Woche.")

    if "blutverdünner" in text or "marcumar" in text or "xarelto" in text or "eliquis" in text:
        if kategorie in KATEGORIEN_VERLETZUNG or "sturz" in text or "gestürzt" in text:
            stufe = max(stufe, 1)
            gruende.append("Blutverdünner + Verletzung: erhöhtes Blutungsrisiko.")

    # --- Konfliktprüfung bei manuellem "unauffällig" ---
    hinweise = []
    if modus == MODUS_OK and stufe >= 1:
        hinweise.append(
            "Hinweis: Das Bild wurde manuell als „unauffällig“ markiert, die übrigen Angaben "
            "sprechen aber für eine Abklärung. Es gilt aus Sicherheitsgründen die höhere Stufe."
        )
    if modus == MODUS_AUTO and eingaben["bild_bytes"] is not None and bild_unsicher and stufe == 0:
        # Unsicherer Bildbefund darf nicht zu einer grünen Entwarnung führen
        stufe = 1
        gruende.append("Bildbefund nicht eindeutig beurteilbar – vorsorglich ärztliche Einschätzung empfohlen.")

    if stufe == 0:
        gruende.append("Keine Alarmsignale in Angaben oder Bildbefund.")

    return {
        "stufe": stufe,
        "gruende": gruende,
        "bild_log": bild_log,
        "bild_details": bild_details,
        "hinweise": hinweise,
        "hergang": eingaben["hergang"],
    }


def render_ergebnis(res: dict) -> None:
    hergang = esc(res["hergang"].strip()) or "Keine Angaben"
    befund_html = (
        f"<div class='befund-box'>🩺 <b>Klinischer Befund:</b><br>{esc(res['bild_log'])}<br>"
        f"<b>Hergang:</b> <i>„{hergang}“</i></div>"
    )
    gruende_html = "".join(f"<li>{esc(g)}</li>" for g in res["gruende"])
    hinweise_html = "".join(
        f"<p style='color:#92400e; font-size:0.9rem;'>{esc(h)}</p>" for h in res["hinweise"]
    )
    gruende_block = (
        f"<p style='margin-bottom:4px;'><b>Begründung der Einstufung:</b></p><ul style='margin-top:0;'>{gruende_html}</ul>"
    )

    stufe = res["stufe"]
    if stufe == 2:
        st.markdown(
            f"""
            <div class="card" style="border-left: 6px solid #dc2626; background-color: #fef2f2;">
                <h3 style="color: #dc2626; margin-top:0;">🚨 HÖCHSTE DRINGLICHKEIT – MÖGLICHER NOTFALL</h3>
                {befund_html}
                {gruende_block}
                {hinweise_html}
                <p>Die Angaben weisen auf eine mögliche akute Gefährdung hin. Bitte sofort den Notruf wählen!</p>
                <a href="tel:112" class="emergency-btn">📞 Sofort 112 anrufen</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif stufe == 1:
        st.markdown(
            f"""
            <div class="card" style="border-left: 6px solid #d97706; background-color: #fffbeb;">
                <h3 style="color: #b45309; margin-top:0;">🟡 Dringende Empfehlung: Ärztliche Abklärung</h3>
                {befund_html}
                {gruende_block}
                {hinweise_html}
                <p>Es liegen Auffälligkeiten vor (z. B. Hämatom, Schwellung, Rötung oder starke Schmerzen). Eine ärztliche
                Untersuchung wird empfohlen, um tiefere Gewebe- oder Gefäßverletzungen auszuschließen.</p>
                <a href="tel:116117" class="bereitschaft-btn">📞 Ärztlicher Bereitschaftsdienst 116 117</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="card" style="border-left: 6px solid #16a34a;">
                <h3 style="color: #16a34a; margin-top:0;">🟢 Empfehlung: Milder Verlauf (Beobachtung)</h3>
                {befund_html}
                {gruende_block}
                {hinweise_html}
                <p>Keine akuten Alarmsignale erkannt. Beobachten Sie den Verlauf und suchen Sie bei Verschlechterung
                oder neuen Symptomen einen Arzt auf.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 4. SESSION STATE
# =========================================================
if "triage_ergebnis" not in st.session_state:
    st.session_state.triage_ergebnis = None

# =========================================================
# 5. HEADER
# =========================================================
st.markdown(
    """
    <div class="hero-banner">
        <h1>🩺 MedicalAssistant Pro</h1>
        <p>Erweiterte klinische Triage & intelligente Schadens- und Symptomanalyse.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        <b>⚠️ Medizinischer Hinweis:</b> Diese Plattform dient der technischen Demonstration und Voreinschätzung.
        Sie ersetzt im Ernstfall keine ärztliche Untersuchung oder Diagnose.
        Bei akuter Lebensgefahr bitte sofort die <b>112</b> wählen!
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(
    [
        "🩺 1. Anamnese & Befund",
        "💡 2. Klinische Triage & Auswertung",
        "🗺️ 3. Notdienst- & Praxensuche",
    ]
)

# =========================================================
# 6. TAB 1 – ANAMNESE
# =========================================================
with tab1:
    st.markdown("### 🔍 Schritt 1: Beschwerden, Vorfall & Bild erfassen")

    col_haupt, col_foto = st.columns([1, 1], gap="medium")

    with col_haupt:
        hauptsymptom = st.selectbox("Hauptbeschwerde / Symptomkategorie:", SYMPTOM_OPTIONEN, key="hauptsymptom")

        col1, col2 = st.columns(2)
        with col1:
            dauer = st.selectbox("Dauer der Beschwerden:", DAUER_OPTIONEN, key="dauer")
        with col2:
            schweregrad = st.selectbox("Intensität / Schmerzlevel:", SCHWERE_OPTIONEN, key="schweregrad")

        unfallhergang = st.text_area(
            "📝 Wie ist es passiert? (Hergang / Auslöser):",
            placeholder="z.B. Stark gestoßen, gestürzt, beim Sport umgeknickt, seit gestern großflächig verfärbt...",
            key="unfallhergang",
        )

    with col_foto:
        uploaded_file = st.file_uploader(
            "📸 Medizinische Foto-Dokumentation (optional)",
            type=["jpg", "jpeg", "png"],
            key="uploaded_file",
        )

        if uploaded_file is not None:
            st.image(uploaded_file, caption="Hochgeladenes Untersuchungsbild", width=240)

        visueller_eindruck = st.selectbox(
            "🔬 Bildbewertung (Analyse-Modus):",
            MODUS_OPTIONEN,
            key="visueller_eindruck",
            help="Automatisch: lokale Farbanalyse des Fotos. Manuell: Der Präsentator legt den Bildbefund selbst fest. "
                 "Ein manuelles 'unauffällig' kann Warnsignale aus den übrigen Angaben nie überstimmen.",
        )

    zusaetzliche_notizen = st.text_area(
        "Zusätzliche Beobachtungen (Vorerkrankungen, Blutverdünner, Allergien etc.):",
        placeholder="z.B. Einnahme von Blutverdünnern, starke Druckempfindlichkeit...",
        key="zusaetzliche_notizen",
    )

    st.markdown("")
    if st.button("🚀 Klinische Triage-Auswertung starten", type="primary", use_container_width=True):
        if hauptsymptom == "Bitte wählen...":
            st.error("Bitte wähle zuerst eine Hauptbeschwerde aus.")
        else:
            try:
                bild_bytes = uploaded_file.getvalue() if uploaded_file is not None else None
                st.session_state.triage_ergebnis = berechne_triage(
                    {
                        "kategorie": hauptsymptom,
                        "dauer": dauer,
                        "schwere": schweregrad,
                        "hergang": unfallhergang,
                        "notizen": zusaetzliche_notizen,
                        "modus": visueller_eindruck,
                        "bild_bytes": bild_bytes,
                    }
                )
                st.success("✅ Daten analysiert! Bitte wechsle zum Tab '💡 2. Klinische Triage & Auswertung'.")
            except Exception:
                st.session_state.triage_ergebnis = None
                st.error("Die Auswertung konnte nicht abgeschlossen werden. Bitte Eingaben prüfen und erneut starten.")

# =========================================================
# 7. TAB 2 – AUSWERTUNG
# =========================================================
with tab2:
    st.markdown("### 💡 Strukturierte Ersteinschätzung & Dringlichkeit")

    ergebnis = st.session_state.triage_ergebnis
    if ergebnis is None:
        st.info("ℹ️ Bitte fülle zuerst die Anamnese in Tab 1 aus und klicke auf 'Klinische Triage-Auswertung starten'.")
    else:
        render_ergebnis(ergebnis)
        if ergebnis["bild_details"]:
            with st.expander("Technische Details der Bildanalyse"):
                st.write(ergebnis["bild_details"])

# =========================================================
# 8. TAB 3 – NOTDIENST
# =========================================================
with tab3:
    st.markdown("### 🗺️ Lokale Notdienst- & Praxensuche")
    st.write("Finden Sie Anlaufstellen für den ärztlichen Bereitschaftsdienst über Ihre Postleitzahl.")

    plz_eingabe = st.text_input("Postleitzahl (PLZ) eingeben:", placeholder="z.B. 23552", max_chars=5, key="plz")
    plz = plz_eingabe.strip()

    if plz:
        if not (plz.isdigit() and len(plz) == 5):
            st.warning("Bitte eine gültige 5-stellige deutsche Postleitzahl eingeben.")
        else:
            st.success(f"📍 Anlaufstellen für PLZ **{plz}**")
            st.markdown(
                f"""
                <div class="card">
                    <h4>🏥 Ärztlicher Bereitschaftsdienst (bundesweit)</h4>
                    <p><b>Region (PLZ):</b> {esc(plz)}</p>
                    <p>Außerhalb der Praxiszeiten erreichen Sie den ärztlichen Bereitschaftsdienst bundesweit unter
                    <b>116 117</b> (kostenfrei). Dort wird Ihnen die zuständige Bereitschaftspraxis in Ihrer Nähe genannt.</p>
                    <p>Bei Lebensgefahr: <b>112</b>.</p>
                    <hr>
                    <a href="tel:116117" class="bereitschaft-btn">📞 116 117 anrufen</a>
                    <a href="tel:112" class="emergency-btn">🚨 112 Notruf</a>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button(
                "🔎 Bereitschaftspraxen auf 116117.de suchen",
                "https://www.116117.de",
                use_container_width=True,
            )
    else:
        st.info("💡 Bitte geben Sie Ihre PLZ ein, um die regionalen Anlaufstellen zu laden.")
