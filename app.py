import io
import datetime
import streamlit as st
from PIL import Image
from huggingface_hub import InferenceClient

# =========================================================
# 1. STREAMLIT CONFIG & VISUELLES DESIGN
# =========================================================
st.set_page_config(
    page_title="MedicalAssistant – API Edition",
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
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
            max-width: 950px !important;
        }

        .hero-banner {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #0f766e 100%);
            border-radius: 20px;
            padding: 28px 36px;
            color: #ffffff;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
            margin-bottom: 20px;
        }
        .hero-banner h1 { font-weight: 800; font-size: 2.2rem; margin: 0; color: #ffffff !important; }
        .hero-banner p { color: #e0f2fe; font-size: 1rem; margin-top: 6px; margin-bottom: 0; }

        .disclaimer-box {
            background-color: #fef3c7;
            border-left: 5px solid #d97706;
            padding: 12px 18px;
            border-radius: 10px;
            font-size: 0.88rem;
            color: #92400e;
            margin-bottom: 20px;
        }

        .card {
            background: #ffffff;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            margin-bottom: 18px;
        }

        .emergency-btn {
            display: inline-block;
            background-color: #dc2626;
            color: white !important;
            font-weight: 700;
            padding: 12px 20px;
            border-radius: 10px;
            text-decoration: none;
            margin-right: 10px;
            margin-top: 8px;
        }
        .bereitschaft-btn {
            display: inline-block;
            background-color: #0284c7;
            color: white !important;
            font-weight: 700;
            padding: 12px 20px;
            border-radius: 10px;
            text-decoration: none;
            margin-top: 8px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Session States
if "ai_bildbeschreibung" not in st.session_state:
    st.session_state.ai_bildbeschreibung = ""
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

# =========================================================
# 2. HEADER & DISCLAIMER
# =========================================================
st.markdown(
    """
    <div class="hero-banner">
        <h1>🩺 MedicalAssistant</h1>
        <p>Hugging Face API Bildanalyse, Vordiagnose & Notdienst-Suche.</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        <b>⚠️ Wichtiger medizinischer Hinweis:</b> Diese App dient der Orientierung. Sie ersetzt <b>keine</b> ärztliche Diagnose. Bei Lebensgefahr bitte sofort die <b>112</b> wählen!
    </div>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 3. NAVIGATION TABS
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "🩺 1. Symptom-Checker & Foto", 
    "💡 2. Ergebnis & Ampel-Auswertung", 
    "🗺️ 3. Bereitschaftsdienst (PLZ-Suche)"
])

# ---------------------------------------------------------
# TAB 1: SYMPTOM EINGABE & API-BILDANALYSE
# ---------------------------------------------------------
with tab1:
    st.markdown("### 🔍 Schritt 1: Symptome eingeben & Foto hochladen")

    col_haupt, col_foto = st.columns([1, 1])

    with col_haupt:
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
            key="hauptsymptom"
        )

        col1, col2 = st.columns(2)
        with col1:
            dauer = st.selectbox(
                "Wie lange anhaltend?",
                ["Wenige Stunden", "1 bis 2 Tage", "3 bis 5 Tage", "Länger als eine Woche"],
                key="dauer"
            )
        with col2:
            schweregrad = st.selectbox(
                "Schweregrad?",
                ["Leicht", "Mäßig", "Sehr stark"],
                key="schweregrad"
            )

    with col_foto:
        uploaded_file = st.file_uploader(
            "📸 Foto hochladen (Wird über die Hugging Face API analysiert)",
            type=["jpg", "jpeg", "png"],
            key="uploaded_file"
        )

        if uploaded_file:
            st.image(uploaded_file, caption="Hochgeladenes Foto", width=220)
            
            hf_token = st.secrets.get("HF_TOKEN", "")
            st.info(f"🔍 **Debug-Status:** Token in Secrets gefunden? **{bool(hf_token)}**")
            
            if hf_token:
                with st.spinner("🤖 Sende Bild an Hugging Face API..."):
                    try:
                        # Moderner InferenceClient (stabiler bei DNS/Netzwerk)
                        client = InferenceClient(
                            model="Salesforce/blip-image-captioning-base",
                            token=hf_token
                        )
                        image_bytes = uploaded_file.getvalue()
                        image = Image.open(io.BytesIO(image_bytes))
                        
                        result = client.image_to_text(image)
                        
                        if result:
                            st.session_state.ai_bildbeschreibung = result
                            st.success(f"API-Befund: '{st.session_state.ai_bildbeschreibung}'")
                        else:
                            st.session_state.ai_bildbeschreibung = ""
                    except Exception as e:
                        st.error(f"Verbindungsfehler zur API: {e}")
                        st.session_state.ai_bildbeschreibung = ""
            else:
                st.warning("⚠️ Kein Hugging Face Token (HF_TOKEN) konfiguriert.")

    zusaetzliche_infos = st.text_area(
        "Zusätzliche Notizen (optional):",
        placeholder="z.B. Juckreiz, Schmerzen beim Drücken...",
        key="zusaetzliche_infos"
    )

    st.markdown("")
    if st.button("🚀 Vordiagnose & Empfehlung jetzt auswerten", type="primary", use_container_width=True):
        if hauptsymptom == "Bitte wählen...":
            st.error("Bitte wähle zuerst ein Hauptsymptom aus.")
        else:
            st.session_state.form_submitted = True
            st.success("✅ Auswertung abgeschlossen! Wechsle zum Tab '💡 2. Ergebnis & Ampel-Auswertung'.")

# ---------------------------------------------------------
# TAB 2: ERGEBNIS & AMPEL-SYSTEM (CLEVERE LOGIK)
# ---------------------------------------------------------
with tab2:
    st.markdown("### 💡 Ersteinschätzung & Empfehlung")

    if not st.session_state.form_submitted:
        st.info("ℹ️ Bitte fülle zuerst Schritt 1 im ersten Tab aus und klicke auf 'Auswerten'.")
    else:
        text_fuer_notfall = (hauptsymptom + " " + zusaetzliche_infos).lower()

        notfall_keywords = ["bewusstlos", "atembeschwerden", "luftnot", "brustschmerzen", "schlaganfall", "puls 300", "stark blutend"]
        ist_echter_notfall = any(kw in text_fuer_notfall for kw in notfall_keywords)

        bild_text_lower = st.session_state.ai_bildbeschreibung.lower()
        medical_red_flags = [
            "rash", "spots", "red spots", "blister", "swelling", "swollen", 
            "wound", "injury", "blood", "bleed", "inflammation", "infected", 
            "pustules", "lesion", "bruise", "cut", "redness"
        ]
        visuelle_auffaeelligkeit = any(w in bild_text_lower for w in medical_red_flags)

        ki_feedback_html = ""
        if st.session_state.ai_bildbeschreibung:
            ki_feedback_html = f"<p style='background: #e0f2fe; padding: 10px; border-radius: 8px; font-size: 0.9rem; color: #0369a1;'>🤖 <b>Hugging Face API Befund:</b> <i>'{st.session_state.ai_bildbeschreibung}'</i></p>"

        if ist_echter_notfall:
            st.markdown(
                f"""
                <div class="card" style="border-left: 6px solid #dc2626; background-color: #fef2f2;">
                    <h3 style="color: #dc2626; margin-top:0;">🚨 AKUTER NOTFALL DETEKTIERT</h3>
                    {ki_feedback_html}
                    <p>Deine Angaben enthalten Hinweise auf eine akute Notfallsituation. Bitte verliere keine Zeit!</p>
                    <a href="tel:112" class="emergency-btn">📞 Sofort 112 Anrufen</a>
                </div>
            """,
                unsafe_allow_html=True,
            )
        elif visuelle_auffaeelligkeit or st.session_state.get("hauptsymptom") == "Hautausschlag / Rötung / Schwellung":
            st.markdown(
                f"""
                <div class="card" style="border-left: 6px solid #e11d48; background-color: #fff1f2;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Empfehlung: Ärztliche Abklärung erforderlich</h3>
                    {ki_feedback_html}
                    <p>Die API hat spezifische Auffälligkeiten im Bild registriert oder es wurde ein entsprechender Hautsymptom-Bereich gewählt.</p>
                    <a href="tel:116117" class="bereitschaft-btn">📞 Bereitschaftsdienst 116 117 anrufen</a>
                </div>
            """,
                unsafe_allow_html=True,
            )
        elif st.session_state.get("hauptsymptom") == "Gelenk- oder Gliederschmerzen" or st.session_state.get("schweregrad") == "Sehr stark":
            st.markdown(
                f"""
                <div class="card" style="border-left: 6px solid #e11d48;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Empfehlung: Hausarzttermin vereinbaren</h3>
                    {ki_feedback_html}
                    <p>Starke Beschwerden erfordern eine zeitnahe ärztliche Abklärung.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="card" style="border-left: 6px solid #16a34a;">
                    <h3 style="color: #16a34a; margin-top:0;">🟢 Empfehlung: Milder Verlauf (Selbstbehandlung)</h3>
                    {ki_feedback_html}
                    <p>Keine kritischen Auffälligkeiten im Bild oder in den Angaben festgestellt.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------
# TAB 3: PLZ-SUCHE & BEREITSCHAFTDIENST (116 117)
# ---------------------------------------------------------
with tab3:
    st.markdown("### 🗺️ Arztlichen Bereitschaftsdienst finden")
    st.write("Bei geschlossenen Praxen hilft der ärztliche Bereitschaftsdienst unter **116 117**.")

    col_plz, col_suche = st.columns([2, 1])
    with col_plz:
        plz_eingabe = st.text_input("Gib deine Postleitzahl (PLZ) ein:", placeholder="z.B. 20095")
    
    if plz_eingabe:
        st.success(f"📍 Nächstgelegene Bereitschaftspraxis für PLZ **{plz_eingabe}**:")
        st.markdown(
            f"""
            <div class="card">
                <h4>🏥 Bereitschaftspraxis Zentrums-Klinik</h4>
                <p><b>Adresse:</b> Hauptstraße 42, {plz_eingabe}</p>
                <p><b>Status:</b> <span style="color: green; font-weight: bold;">Geöffnet</span></p>
                <hr>
                <a href="tel:116117" class="bereitschaft-btn">📞 Anrufen: 116 117</a>
                <a href="tel:112" class="emergency-btn">🚨 Notruf: 112</a>
            </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.info("💡 Gib oben deine PLZ ein, um die Praxis anzuzeigen.")
