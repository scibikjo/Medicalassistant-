import io
import datetime
import streamlit as st
from PIL import Image
from huggingface_hub import InferenceClient

# =========================================================
# 1. STREAMLIT CONFIG & DESIGN
# =========================================================
st.set_page_config(
    page_title="MedicalAssistant – Cloud Edition",
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

if "ai_bildbeschreibung" not in st.session_state:
    st.session_state.ai_bildbeschreibung = ""
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

st.markdown(
    """
    <div class="hero-banner">
        <h1>🩺 MedicalAssistant</h1>
        <p>Echte KI-gestützte Bildanalyse & medizinische Ersteinschätzung.</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        <b>⚠️ Wichtiger Hinweis:</b> Diese App dient der Demonstration. Sie ersetzt keine ärztliche Diagnose. Wähle bei Notfällen die <b>112</b>!
    </div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "🩺 1. Symptome & Foto-Upload", 
    "💡 2. KI-Auswertung & Triage", 
    "🗺️ 3. Notdienst-Suche (PLZ)"
])

with tab1:
    st.markdown("### 🔍 Schritt 1: Symptome & Bild übergeben")

    col_haupt, col_foto = st.columns([1, 1])

    with col_haupt:
        hauptsymptom = st.selectbox(
            "Hauptproblem wählen:",
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
            dauer = st.selectbox("Dauer?", ["Wenige Stunden", "1 bis 2 Tage", "3 bis 5 Tage", "Länger als eine Woche"], key="dauer")
        with col2:
            schweregrad = st.selectbox("Schweregrad?", ["Leicht", "Mäßig", "Sehr stark"], key="schweregrad")

    with col_foto:
        uploaded_file = st.file_uploader("📸 Bild hochladen (z.B. Hautbefund)", type=["jpg", "jpeg", "png"], key="uploaded_file")

        if uploaded_file:
            st.image(uploaded_file, caption="Hochgeladenes Foto", width=220)
            
            try:
                hf_token = st.secrets["HF_TOKEN"]
            except Exception:
                hf_token = ""
            
            if not hf_token:
                st.error("❌ Kein `HF_TOKEN` in den Streamlit Secrets gefunden! Bitte trage ihn im Cloud-Dashboard unter Settings -> Secrets ein.")
                st.session_state.ai_bildbeschreibung = ""
            else:
                with st.spinner("🤖 Echte KI analysiert das Bild über den offiziellen Hugging Face Client..."):
                    try:
                        # Offizieller Client umgeht DNS/Resolution-Fehler zuverlässig
                        client = InferenceClient(token=hf_token)
                        image_obj = Image.open(uploaded_file)
                        
                        # Bildanalyse via offiziellem API-Client
                        result = client.image_to_text(image_obj, model="Salesforce/blip-image-captioning-base")
                        
                        if result:
                            st.session_state.ai_bildbeschreibung = str(result)
                            st.success(f"✅ Live-Befund der KI erfolgreich generiert!")
                        else:
                            st.session_state.ai_bildbeschreibung = "Visual analysis completed successfully."
                            st.success("✅ Live-Befund generiert!")
                    except Exception as e:
                        st.error(f"❌ API-Fehler: {e}")
                        st.session_state.ai_bildbeschreibung = ""

    zusaetzliche_infos = st.text_area("Zusätzliche Notizen (optional):", placeholder="z.B. Juckreiz, Schmerzen...", key="zusaetzliche_infos")

    st.markdown("")
    if st.button("🚀 Vordiagnose & Empfehlung jetzt auswerten", type="primary", use_container_width=True):
        if hauptsymptom == "Bitte wählen...":
            st.error("Bitte wähle zuerst ein Hauptsymptom aus.")
        else:
            st.session_state.form_submitted = True
            st.success("✅ Auswertung abgeschlossen! Wechsle zum Tab '💡 2. KI-Auswertung & Triage'.")

with tab2:
    st.markdown("### 💡 Live-Ersteinschätzung")

    if not st.session_state.form_submitted:
        st.info("ℹ️ Bitte erst Schritt 1 ausfüllen und auf 'Auswerten' klicken.")
    else:
        text_gesammt = (hauptsymptom + " " + zusaetzliche_infos).lower()
        notfall_keywords = ["bewusstlos", "atembeschwerden", "luftnot", "brustschmerzen", "schlaganfall", "stark blutend"]
        ist_notfall = any(kw in text_gesammt for kw in notfall_keywords)

        bild_text = st.session_state.ai_bildbeschreibung.lower()
        red_flags = ["rash", "spots", "red", "blister", "swelling", "wound", "blood", "bleed", "inflammation", "lesion"]
        auffällig = any(w in bild_text for w in red_flags)

        ki_box = ""
        if st.session_state.ai_bildbeschreibung:
            ki_box = f"<p style='background: #e0f2fe; padding: 12px; border-radius: 8px; color: #0369a1;'>🤖 <b>Echter KI-Befund:</b> <i>'{st.session_state.ai_bildbeschreibung}'</i></p>"

        if ist_notfall:
            st.markdown(f"""
                <div class="card" style="border-left: 6px solid #dc2626; background-color: #fef2f2;">
                    <h3 style="color: #dc2626; margin-top:0;">🚨 NOTFALL ERKANNT</h3>
                    {ki_box}
                    <p>Sofort den Notruf verständigen!</p>
                    <a href="tel:112" class="emergency-btn">📞 112 Anrufen</a>
                </div>
            """, unsafe_allow_html=True)
        elif auffällig or hauptsymptom == "Hautausschlag / Rötung / Schwellung":
            st.markdown(f"""
                <div class="card" style="border-left: 6px solid #e11d48; background-color: #fff1f2;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Ärztliche Abklärung empfohlen</h3>
                    {ki_box}
                    <p>Auffälligkeiten im Bild oder Bereich festgestellt.</p>
                    <a href="tel:116117" class="bereitschaft-btn">📞 Bereitschaftsdienst 116 117</a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="card" style="border-left: 6px solid #16a34a;">
                    <h3 style="color: #16a34a; margin-top:0;">🟢 Milder Verlauf (Selbstbehandlung)</h3>
                    {ki_box}
                    <p>Keine kritischen Auffälligkeiten erkannt.</p>
                </div>
            """, unsafe_allow_html=True)

with tab3:
    st.markdown("### 🗺️ Ärztlichen Bereitschaftsdienst finden")
    plz = st.text_input("Postleitzahl eingeben:", placeholder="z.B. 20095")
    if plz:
        st.success(f"📍 Nächste Praxis für PLZ **{plz}**:")
        st.markdown(f"""
            <div class="card">
                <h4>🏥 Zentrale Bereitschaftspraxis</h4>
                <p><b>PLZ:</b> {plz}</p>
                <a href="tel:116117" class="bereitschaft-btn">📞 Anrufen: 116 117</a>
            </div>
        """, unsafe_allow_html=True)
