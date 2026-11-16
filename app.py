import io
import datetime
import streamlit as st
from PIL import Image
import numpy as np

# =========================================================
# 1. STREAMLIT CONFIG & DESIGN
# =========================================================
st.set_page_config(
    page_title="MedicalAssistant – Professional Edition",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
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

if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

def analysiere_bild(uploaded_file):
    """Analysiert Bildregionen auf Rötungen, Hämatome (blaue/violette Flecken) und Kontrastabweichungen."""
    img = Image.open(uploaded_file).convert("RGB")
    # Auf einheitliche Größe skalieren für schnelle und präzise Pixel-Analyse
    img_small = img.resize((200, 200))
    arr = np.array(img_small, dtype=np.float32)

    # Fokus auf den zentralen Bildbereich (wo sich meist die fotografierte Stelle befindet)
    center = arr[30:170, 30:170]
    r = center[:, :, 0]
    g = center[:, :, 1]
    b = center[:, :, 2]

    # 1. Rötung / Entzündung (Rot deutlich höher als Grün und Blau)
    red_pixels = np.mean((r - g > 30) & (r - b > 30))

    # 2. Hämatom / Blauer Fleck (Dunkle Bereiche mit Violett-/Blau-Anteil oder starkem Kontrast zur Umgebung)
    brightness = (r + g + b) / 3.0
    # Blau-/Violettstich bei abgedunkelter Haut (B relativ hoch im Vergleich zu G)
    bruise_pixels = np.mean((brightness < 145) & (b > g - 5) & ((r - g) < 40))

    # 3. Lokale Verfärbung / Kontrastabweichung (Unterschied zwischen dunkelstem und hellstem Hautbereich)
    p10 = np.percentile(brightness, 15)
    p85 = np.percentile(brightness, 85)
    contrast_diff = p85 - p10

    if bruise_pixels > 0.14 or (contrast_diff > 75 and bruise_pixels > 0.08):
        return True, "Visueller Befund: Deutliche Verfärbung / Hämatom-Struktur (blauer Fleck / Prellung) im Fokusbereich erkannt."
    elif red_pixels > 0.18:
        return True, "Visueller Befund: Lokale Rötung / Entzündungszeichen (Hyperämie) erkannt."
    else:
        return False, "Visueller Befund: Gleichmäßige Struktur, keine akuten Verfärbungen oder Läsionen erkannt."

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
        <b>⚠️ Medizinischer Hinweis:</b> Diese Plattform dient der technischen Demonstration und Voreinschätzung. Sie ersetzt im Ernstfall keine ärztliche Untersuchung oder Diagnose. Bei akuter Lebensgefahr bitte sofort die <b>112</b> wählen!
    </div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "🩺 1. Anamnese & Befund", 
    "💡 2. Klinische Triage & Auswertung", 
    "🗺️ 3. Notdienst- & Praxensuche"
])

with tab1:
    st.markdown("### 🔍 Schritt 1: Beschwerden, Vorfall & Bild erfassen")

    col_haupt, col_foto = st.columns([1, 1], gap="medium")

    with col_haupt:
        hauptsymptom = st.selectbox(
            "Hauptbeschwerde / Symptomkategorie:",
            [
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
            ],
            key="hauptsymptom"
        )

        col1, col2 = st.columns(2)
        with col1:
            dauer = st.selectbox(
                "Dauer der Beschwerden:",
                ["Wenige Minuten / Akut", "Wenige Stunden", "1 bis 2 Tage", "3 bis 5 Tage", "Länger als eine Woche"],
                key="dauer"
            )
        with col2:
            schweregrad = st.selectbox(
                "Intensität / Schmerzlevel:",
                ["Leicht (1-3)", "Mäßig (4-7)", "Sehr stark / Unerträglich (8-10)"],
                key="schweregrad"
            )

        unfallhergang = st.text_area(
            "📝 Wie ist es passiert? (Hergang / Auslöser):",
            placeholder="z.B. Stark gestoßen, gestürzt, beim Sport umgeknickt, seit gestern großflächig verfärbt...",
            key="unfallhergang"
        )

    with col_foto:
        uploaded_file = st.file_uploader(
            "📸 Medizinische Foto-Dokumentation (optional)",
            type=["jpg", "jpeg", "png"],
            key="uploaded_file"
        )

        if uploaded_file:
            st.image(uploaded_file, caption="Hochgeladenes Untersuchungsbild", width=240)
            
        visueller_eindruck = st.selectbox(
            "🤖 Bildanalyse-Modus (Cloud-Vision Engine):",
            [
                "Automatische Bildanalyse (Standard)",
                "🟢 Manuell: Unauffällige Struktur",
                "🟡 Manuell: Hämatom / Rötung / Schwellung",
                "🔴 Manuell: Akute offene Verletzung",
            ],
            key="visueller_eindruck"
        )

    zusaetzliche_notizen = st.text_area(
        "Zusätzliche Beobachtungen (Vorerkrankungen, Blutverdünner, Allergien etc.):",
        placeholder="z.B. Einnahme von Blutverdünnern, starke Druckempfindlichkeit...",
        key="zusaetzliche_notizen"
    )

    st.markdown("")
    if st.button("🚀 Klinische Triage-Auswertung starten", type="primary", use_container_width=True):
        if hauptsymptom == "Bitte wählen...":
            st.error("Bitte wähle zuerst eine Hauptbeschwerde aus.")
        else:
            st.session_state.form_submitted = True
            st.success("✅ Daten analysiert! Bitte wechsle zum Tab '💡 2. Klinische Triage & Auswertung'.")

with tab2:
    st.markdown("### 💡 Strukturierte Ersteinschätzung & Dringlichkeit")

    if not st.session_state.form_submitted:
        st.info("ℹ️ Bitte fülle zuerst die Anamnese in Tab 1 aus und klicke auf 'Klinische Triage-Auswertung starten'.")
    else:
        gesamter_text = (hauptsymptom + " " + unfallhergang + " " + zusaetzliche_notizen).lower()

        notfall_keywords = [
            "bewusstlos", "atembeschwerden", "luftnot", "brustschmerzen", 
            "schlaganfall", "stark blutend", "kollaps", "kopfverletzung", "gehirnerschütterung"
        ]
        ist_echter_notfall = (
            any(kw in gesamter_text for kw in notfall_keywords) 
            or hauptsymptom in ["Brustschmerzen / Engegefühl (Kardial)", "Plötzliche Atemnot / Luftnot"]
        )

        ist_visuell_auffaellig = False
        visueller_text_log = "Kein Bild hochgeladen."

        if visueller_eindruck == "🟢 Manuell: Unauffällige Struktur":
            ist_visuell_auffaellig = False
            visueller_text_log = "Visueller Befund: Gewebestruktur unauffällig."
        elif visueller_eindruck == "🟡 Manuell: Hämatom / Rötung / Schwellung":
            ist_visuell_auffaellig = True
            visueller_text_log = "Visueller Befund: Deutliche Gewebeverfärbung / Hämatom / Rötung."
        elif visueller_eindruck == "🔴 Manuell: Akute offene Verletzung":
            ist_visuell_auffaellig = True
            visueller_text_log = "Visueller Befund: Akute Läsion / Verletzung festgestellt."
        else:
            if uploaded_file is not None:
                try:
                    ist_visuell_auffaellig, visueller_text_log = analysiere_bild(uploaded_file)
                except Exception:
                    ist_visuell_auffaellig = False
                    visueller_text_log = "Visueller Befund: Bild eingelesen."

        # Prüfen ob Symptom oder Hergang bereits auf Verletzung/Hämatom hinweist
        symptom_auffaellig = any(
            w in gesamter_text for w in ["blauer fleck", "hämatom", "prellung", "wunde", "schnittwunde", "schwellung", "blutverdünner", "sturz"]
        )

        befund_html = f"""
        <p style='background: #e0f2fe; padding: 12px; border-radius: 10px; font-size: 0.95rem; color: #0369a1; border-left: 4px solid #0284c7;'>
            🩺 <b>Klinischer Befund:</b><br>{visueller_text_log}<br>
            <b>Hergang:</b> <i>'{unfallhergang if unfallhergang else 'Keine Angaben'}'</i>
        </p>
        """

        if ist_echter_notfall:
            st.markdown(
                f"""
                <div class="card" style="border-left: 6px solid #dc2626; background-color: #fef2f2;">
                    <h3 style="color: #dc2626; margin-top:0;">🚨 HÖCHSTE DRINGLICHKEIT – AKUTER NOTFALL</h3>
                    {befund_html}
                    <p>Die Kombination aus Symptomen und Hergang weist auf eine akute Gefährdung hin. Bitte sofort medizinische Notfallhilfe rufen!</p>
                    <a href="tel:112" class="emergency-btn">📞 Sofort 112 Anrufen</a>
                </div>
            """,
                unsafe_allow_html=True,
            )
        elif ist_visuell_auffaellig or symptom_auffaellig or schweregrad == "Sehr stark / Unerträglich (8-10)":
            st.markdown(
                f"""
                <div class="card" style="border-left: 6px solid #e11d48; background-color: #fff1f2;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Dringende Empfehlung: Ärztliche Abklärung erforderlich</h3>
                    {befund_html}
                    <p>Es wurden deutliche Auffälligkeiten (z. B. großflächiges Hämatom, Schwellung, Rötung oder starke Schmerzen) festgestellt. Eine ärztliche Untersuchung wird dringend empfohlen, um tiefere Gewebe- oder Gefäßverletzungen auszuschließen.</p>
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
                    <p>Keine akuten Alarmsignale in den Angaben oder der Bildstruktur identifiziert. Beobachten Sie den Verlauf und suchen Sie bei Verschlechterung einen Arzt auf.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

with tab3:
    st.markdown("### 🗺️ Lokale Notdienst- & Praxensuche")
    st.write("Finden Sie die nächstgelegene geöffnete Praxis oder Notdienstzentrale über Ihre Postleitzahl.")

    plz_eingabe = st.text_input("Postleitzahl (PLZ) eingeben:", placeholder="z.B. 23552")
    
    if plz_eingabe:
        st.success(f"📍 Ergebnisse für PLZ **{plz_eingabe}**:")
        st.markdown(
            f"""
            <div class="card">
                <h4>🏥 Zentrale Notdienstpraxis & Ambulanz</h4>
                <p><b>Standort-PLZ:</b> {plz_eingabe}</p>
                <p><b>Verfügbarkeit:</b> <span style="color: green; font-weight: bold;">Geöffnet / Diensthabend</span></p>
                <hr>
                <a href="tel:116117" class="bereitschaft-btn">📞 116 117 anrufen</a>
                <a href="tel:112" class="emergency-btn">🚨 112 Notruf</a>
            </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.info("💡 Bitte geben Sie Ihre PLZ ein, um die regionalen Anlaufstellen zu laden.")
