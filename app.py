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
    page_title="MedicalAssistant – Erweiterte Vordiagnose",
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
        <h1>🩺 MedicalAssistant (KI-gestützt)</h1>
        <p>Spezifische Ersteinschätzung & optionale Foto-Analyse zur Praxen-Entlastung.</p>
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
# 3. SYMPTOM-CHECKER & OPTIONALER FOTO-UPLOAD
# =========================================================
st.markdown("### 🔍 Schritt 1: Symptom & Bereich auswählen")

hauptsymptom = st.selectbox(
    "Was beschreibt dein Hauptproblem am besten?",
    [
        "Bitte wählen...",
        "Kopfschmerzen / Migräne",
        "Erkältung / Halsschmerzen / Husten",
        "Gelenk- oder Gliederschmerzen",
        "Magen-Darm-Beschwerden",
        "Hautausschlag / Rötung / Schwellung",
    ],
)

# Optionaler Foto-Upload für visuelle Symptome (z.B. Hautausschlag, Schwellung)
uploaded_file = st.file_uploader("📸 Optional: Foto hochladen (z.B. bei Hautausschlag oder Schwellung zur Analyse)", type=["jpg", "jpeg", "png"])

ai_bildbeschreibung = ""
if uploaded_file:
    st.image(uploaded_file, caption="Hochgeladenes Foto", width=250)
    if HAS_HF and st.button("🤖 Bild mit KI analysieren lassen"):
        with st.spinner("KI analysiert das Bild..."):
            try:
                processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                raw_image = Image.open(uploaded_file).convert("RGB")
                inputs = processor(raw_image, return_tensors="pt")
                out = model.generate(**inputs, max_new_tokens=40)
                ai_bildbeschreibung = processor.decode(out[0], skip_special_tokens=True)
                st.success(f"Erkannter visueller Hinweis (Englisch/KI): {ai_bildbeschreibung}")
            except Exception as e:
                st.info("Bildanalyse konnte lokal nicht geladen werden (wird für die Empfehlung ignoriert).")

col1, col2 = st.columns(2)
with col1:
    dauer = st.selectbox("Wie lange hast du das schon?", ["Wenige Stunden", "1 bis 2 Tage", "3 bis 5 Tage", "Länger als eine Woche"])
with col2:
    schweregrad = st.selectbox("Wie stark sind die Beschwerden?", ["Leicht", "Mäßig", "Sehr stark"])

st.markdown("")

# =========================================================
# 4. SPEZIFISCHE RATSCHLÄGE STATT PAuschaler "TRINK WASSER"-ANTWORTEN
# =========================================================
if st.button("🚀 Spezifische Empfehlung anfordern", type="primary", use_container_width=True):
    if hauptsymptom == "Bitte wählen...":
        st.error("Bitte wähle ein Symptom aus.")
    else:
        st.markdown("---")
        st.subheader("💡 Spezifische Empfehlung & Vorbereitung fürs Arztgespräch")

        # Hier geben wir nun spezifische Tipps je nach gewähltem Symptom!
        if hauptsymptom == "Gelenk- oder Gliederschmerzen":
            titel_ampel = "🟡 Gelenk- / Gliederschmerzen im Blick behalten"
            tipps = """
            <ul>
                <b>Spezifische Selbsthilfe-Tipps:</b>
                <li>Das betroffene Gelenk vorerst schonen und nicht überlasten.</li>
                <li>Ggf. vorsichtig kühlen (falls eine Schwellung vorliegt) oder wärmen (bei Verspannungen).</li>
                <li><b>Wann zum Arzt?</b> Wenn die Schmerzen nach 2-3 Tagen Schonung nicht besser werden oder Fieber hinzukommt.</li>
            </ul>
            """
        elif hauptsymptom == "Kopfschmerzen / Migräne":
            titel_ampel = "🟢 Meist gut durch Ruhe lösbar"
            tipps = """
            <ul>
                <b>Spezifische Selbsthilfe-Tipps:</b>
                <li>Dunklen, ruhigen Raum aufsuchen und Reize reduzieren.</li>
                <li>Viel Wasser trinken (oft ist Flüssigkeitsmangel ein Auslöser).</li>
                <li>Ein feuchtes Tuch auf die Stirn legen.</li>
            </ul>
            """
        elif hauptsymptom == "Hautausschlag / Rötung / Schwellung":
            titel_ampel = "🟡 Hauterscheinung beobachten"
            tipps = """
            <ul>
                <b>Spezifische Selbsthilfe-Tipps:</b>
                <li>Die Stelle nicht kratzen, um Entzündungen zu vermeiden.</li>
                <li>Mit einem Stift den Rand der Rötung markieren, um zu sehen, ob sie sich ausbreitet.</li>
                <li><b>Hinweis:</b> Wenn Atemnot oder Schwindel dazukommt, sofort den Notruf wählen (allergischer Schock!).</li>
            </ul>
            """
        else:
            titel_ampel = "🟢 Milder Verlauf – Allgemeine Schonung"
            tipps = """
            <ul>
                <b>Spezifische Selbsthilfe-Tipps:</b>
                <li>Körperliche Anstrengung vermeiden und ausruhen.</li>
                <li>Auf leicht verdauliche Kost und ausreichend Flüssigkeit achten.</li>
            </ul>
            """

        # Karte ausgeben
        st.markdown(f"""
            <div class="card" style="border-left: 5px solid #0284c7;">
                <h3 style="color: #0369a1; margin-top:0;">{titel_ampel}</h3>
                <p>Du hast angegeben: <b>{hauptsymptom}</b> (Dauer: {dauer}, Stärke: {schweregrad}).</p>
                {tipps}
            </div>
        """, unsafe_allow_html=True)

        st.info("📞 **Bereitsitätsdienst:** 116 117 (kostenlos bei Fragen außerhalb der Praxiszeiten)")
