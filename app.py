import datetime
import streamlit as st
from PIL import Image

# Hugging Face für Bildanalyse (optional, falls installiert)
try:
    from transformers import BlipForConditionalGeneration, BlipProcessor
    HAS_HF = True
except ImportError:
    HAS_HF = False

# =========================================================
# 1. STREAMLIT CONFIG & DESIGN
# =========================================================
st.set_page_config(
    page_title="MedicalAssistant – Sichere Vordiagnose",
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

        #MainMenu, footer, header { visibility: hidden !important; }
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 4rem !important;
            max-width: 900px !important;
        }

        .hero-banner {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #0f766e 100%);
            border-radius: 20px;
            padding: 30px 40px;
            color: #ffffff;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
            margin-bottom: 24px;
        }
        .hero-banner h1 { font-weight: 800; font-size: 2.2rem; margin: 0; color: #ffffff !important; }
        .hero-banner p { color: #e0f2fe; font-size: 1rem; margin-top: 6px; margin-bottom: 0; }

        .disclaimer-box {
            background-color: #fef3c7;
            border-left: 5px solid #d97706;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.9rem;
            color: #92400e;
            margin-bottom: 24px;
        }

        .card {
            background: #ffffff;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
            margin-bottom: 16px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 2. HEADER & DISCLAIMER
# =========================================================
st.markdown(
    """
    <div class="hero-banner">
        <h1>🩺 MedicalAssistant</h1>
        <p>Automatische Foto-Analyse & sichere Ersteinschätzung zur Praxen-Entlastung.</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        <b>⚠️ Wichtiger medizinischer Hinweis:</b> Diese App ersetzt <b>niemals</b> den Arzt. Sie dient zur Orientierung und Vorbereitung auf das Arztgespräch. Bei akuten Notfällen wähle sofort die 112.
    </div>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 3. SYMPTOM-CHECKER & AUTOMATISCHE FOTO-ANALYSE
# =========================================================
st.markdown("### 🔍 Schritt 1: Symptom & Foto eingeben")

hauptsymptom = st.selectbox(
    "Was beschreibt dein Hauptproblem am besten?",
    [
        "Bitte wählen...",
        "Kopfschmerzen / Migräne",
        "Erkältung / Halsschmerzen / Husten",
        "Gelenk- oder Gliederschmerzen",
        "Magen-Darm-Beschwerden",
        "Hautausschlag / Rötung / Schwellung",
        "Sonstiges / Allgemeine Beschwerden",
    ],
)

uploaded_file = st.file_uploader(
    "📸 Foto hochladen (Wird bei der Empfehlung automatisch analysiert)",
    type=["jpg", "jpeg", "png"]
)

ai_bildbeschreibung = ""

if uploaded_file:
    st.image(uploaded_file, caption="Hochgeladenes Foto für die Analyse", width=250)
    
    # Automatische Analyse im Hintergrund bei Bildupload
    if HAS_HF:
        with st.spinner("🤖 KI analysiert das Bild automatisch im Hintergrund..."):
            try:
                processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                raw_image = Image.open(uploaded_file).convert("RGB")
                inputs = processor(raw_image, return_tensors="pt")
                out = model.generate(**inputs, max_new_tokens=40)
                ai_bildbeschreibung = processor.decode(out[0], skip_special_tokens=True)
            except Exception as e:
                ai_bildbeschreibung = ""
    else:
        st.info("💡 Hinweis: Lokale KI-Bibliotheken ('transformers'/'torch') sind auf diesem Server nicht aktiv.")

col1, col2 = st.columns(2)
with col1:
    dauer = st.selectbox(
        "Wie lange hast du das schon?",
        ["Wenige Stunden", "1 bis 2 Tage", "3 bis 5 Tage", "Länger als eine Woche"]
    )
with col2:
    schweregrad = st.selectbox(
        "Wie stark sind die Beschwerden?",
        ["Leicht", "Mäßig", "Sehr stark"]
    )

zusaetzliche_infos = st.text_area(
    "Zusätzliche Infos / Beschreibung (optional):",
    placeholder="z.B. Seit heute Morgen rote Flecken im Gesicht...",
)

st.markdown("")

# =========================================================
# 4. SICHERHEITS- & EMPFEHLUNGS-LOGIK (BILD HAT OBERSTE PRIORITÄT)
# =========================================================
if st.button("🚀 Spezifische Empfehlung anfordern", type="primary", use_container_width=True):
    if hauptsymptom == "Bitte wählen...":
        st.error("Bitte wähle mindestens ein Symptom aus.")
    else:
        text_analyse = (hauptsymptom + " " + zusaetzliche_infos + " " + ai_bildbeschreibung).lower()

        # Harte Notfall-Erkennung
        notfall_keywords = ["bewusstlos", "atembeschwerden", "luftnot", "brustschmerzen", "schlaganfall", "puls 300", "stark blutend"]
        ist_echter_notfall = any(kw in text_analyse for kw in notfall_keywords)

        # Visuelle Auffälligkeiten im Bild (Automatisch erkannt!)
        bild_text_lower = ai_bildbeschreibung.lower()
        visuelle_auffaeelligkeit = any(w in bild_text_lower for w in ["red", "skin", "face", "spots", "rash", "swelling", "mark", "child", "person", "redness"])

        st.markdown("---")
        st.subheader("💡 Spezifische Empfehlung & Handlung")

        # Zeige transparent, was die automatische Bildanalyse ergeben hat
        ki_feedback_html = ""
        if ai_bildbeschreibung:
            ki_feedback_html = f"<p style='background: #e0f2fe; padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #0369a1;'>🤖 <b>Automatische KI-Bildanalyse:</b> <i>'{ai_bildbeschreibung}'</i></p>"

        if ist_echter_notfall:
            st.markdown(
                f"""
                <div class="card" style="border-left: 5px solid #dc2626; background-color: #fef2f2;">
                    <h3 style="color: #dc2626; margin-top:0;">🚨 AKUTER NOTFALL DETEKTIERT</h3>
                    {ki_feedback_html}
                    <p>Deine Angaben enthalten Hinweise auf eine ernste Situation. Bitte warte nicht ab!</p>
                    <p><b>Wähle sofort den Notruf:</b> Wähle die <b>112</b>.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

        # BILD-SICHERHEITSSCHALTUNG: Wenn die KI rote Flecken/Haut erkennt, schaltet es IMMER auf Gelb!
        elif visuelle_auffaeelligkeit or hauptsymptom == "Hautausschlag / Rötung / Schwellung":
            st.markdown(
                f"""
                <div class="card" style="border-left: 5px solid #e11d48; background-color: #fff1f2;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Empfehlung: Ärztliche Abklärung (Auffälliges Hautbild erkannt)</h3>
                    {ki_feedback_html}
                    <p>Das hochgeladene Foto wurde automatisch analysiert und es wurden visuelle Auffälligkeiten (wie Rötungen oder Hautveränderungen) festgestellt. Solche Symptome sollten unabhängig vom Text zeitnah von einem Arzt (oder Kinderarzt) untersucht werden.</p>
                    <p><b>Tipp:</b> Nicht kratzen und bei Fieber oder Schmerzen sofort zum Arzt.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

        elif hauptsymptom == "Gelenk- oder Gliederschmerzen" or schweregrad == "Sehr stark":
            st.markdown(
                f"""
                <div class="card" style="border-left: 5px solid #e11d48;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Empfehlung: Arzttermin in den nächsten Tagen</h3>
                    {ki_feedback_html}
                    <p>Da die Beschwerden stark sind oder länger anhalten, empfiehlt sich eine ärztliche Abklärung beim Hausarzt.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div class="card" style="border-left: 5px solid #16a34a;">
                    <h3 style="color: #16a34a; margin-top:0;">🟢 Empfehlung: Milder Fall – Selbstbehandlung möglich</h3>
                    {ki_feedback_html}
                    <p>Nach deiner Eingabe und der automatischen Bildprüfung handelt es sich um einen milden, unkritischen Verlauf. Du kannst versuchen, dich zu Hause zu schonen.</p>
                    <br>
                    <b>Tipps zur Linderung:</b>
                    <ul>
                        <li>Ausreichend trinken und körperlich ausruhen.</li>
                        <li>Bei Bedarf Raumklima anpassen.</li>
                    </ul>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.info("📞 **Bereitsitätsdienst:** 116 117 (kostenlos bei Fragen außerhalb der Praxiszeiten)")
