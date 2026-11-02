import datetime
import streamlit as st

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
        <p>Sichere Vordiagnose & strukturierte Ersteinschätzung zur Praxen-Entlastung.</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        <b>⚠️ Wichtiger medizinischer Hinweis:</b> Diese App dient ausschließlich der ersten Orientierung und ersetzt <b>keinesfalls</b> den Gang zum Arzt. Bei unklaren oder akuten Beschwerden kontaktiere bitte den ärztlichen Bereitsitätsdienst (116 117) oder den Notruf (112).
    </div>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 3. SYMPTOM-CHECKER EINGABE
# =========================================================
st.markdown("### 🔍 Schritt 1: Symptome beschreiben")

hauptsymptom = st.selectbox(
    "Was beschreibt dein Hauptproblem am besten?",
    [
        "Bitte wählen...",
        "Kopfschmerzen / Migräne",
        "Erkältung / Halsschmerzen / Husten",
        "Magen-Darm-Beschwerden",
        "Kleine Schnittwunde / Kratzer",
        "Gelenk- oder Gliederschmerzen",
        "Fieber (leicht bis mäßig)",
        "Sonstiges / Allgemeine Beschwerden",
    ],
)

col1, col2 = st.columns(2)
with col1:
    dauer = st.selectbox(
        "Wie lange hast du die Beschwerden schon?",
        [
            "Wenige Stunden",
            "1 bis 2 Tage",
            "3 bis 5 Tage",
            "Länger als eine Woche",
        ],
    )

with col2:
    schweregrad = st.selectbox(
        "Wie stark nimmst du die Beschwerden wahr?",
        ["Leicht / Kaum störend", "Mäßig / Spürbar", "Sehr stark / Heftig"],
    )

zusaetzliche_infos = st.text_area(
    "Beschreibe deine Situation kurz mit eigenen Worten (optional):",
    placeholder="z.B. Habe mich leicht am Papier geschnitten oder Kopfschmerzen seit gestern...",
)

st.markdown("")

# =========================================================
# 4. INTELLIGENTE SICHERHEITS- & AMPEL-LOGIK
# =========================================================
if st.button("🚀 Vordiagnose & Empfehlung anfordern", type="primary", use_container_width=True):
    if hauptsymptom == "Bitte wählen...":
        st.error("Bitte wähle zuerst ein Hauptsymptom aus.")
    else:
        # Text in Kleinbuchstaben umwandeln, um präzise nach Kontext zu suchen
        text_analyse = (hauptsymptom + " " + zusaetzliche_infos).lower()

        # A) HARTE NOTFALL-INDUKATOREN (Nur bei echtem Ernstfall, keinem Kratzer!)
        notfall_keywords = ["bewusstlos", "atembeschwerden", "luftnot", "brustschmerzen", "schlaganfall", "puls 300", "stark blutend", "sturz"]
        ist_echter_notfall = any(kw in text_analyse for kw in notfall_keywords) and not any(bagatelle in text_analyse for bagatelle in ["kratzer", "klein", "leicht", "papier", "schon vorbei"])

        st.markdown("---")
        st.subheader("💡 Ergebnis & Handlungsempfehlung")

        if ist_echter_notfall:
            st.markdown(
                """
                <div class="card" style="border-left: 5px solid #dc2626; background-color: #fef2f2;">
                    <h3 style="color: #dc2626; margin-top:0;">🚨 AKUTER NOTFALL DETEKTIERT</h3>
                    <p>Deine Beschreibung enthält Hinweise auf eine ernste oder akute Situation. Bitte warte nicht ab!</p>
                    <p><b>Wähle sofort den Notruf:</b> Wähle die <b>112</b> oder lasse dir umgehend medizinische Hilfe holen.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        elif schweregrad == "Sehr stark / Heftig" or dauer == "Länger als eine Woche":
            st.markdown(
                """
                <div class="card" style="border-left: 5px solid #e11d48;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Empfehlung: Arzttermin in den nächsten Tagen vereinbaren</h3>
                    <p>Da deine Beschwerden sehr stark sind oder länger anhalten, solltest du das von einem Arzt abklären lassen. Es ist kein akuter Notfall für den Rettungsdienst, aber ein Termin beim Hausarzt ist ratsam.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="card" style="border-left: 5px solid #16a34a;">
                    <h3 style="color: #16a34a; margin-top:0;">🟢 Empfehlung: Milder Fall – Selbstbehandlung möglich</h3>
                    <p>Nach deiner Eingabe handelt es sich um einen milden, unkritischen Fall (z.B. eine kleine Verletzung oder leichte Beschwerden). Du kannst versuchen, dich zu Hause zu schonen und musst damit nicht direkt eine Praxis aufsuchen.</p>
                    <br>
                    <b>Tipps zur Linderung:</b>
                    <ul>
                        <li>Bei kleinen Wunden: Sauber halten und ggf. ein Pflaster aufkleben.</li>
                        <li>Ausreichend trinken und körperlich etwas kürzertreten.</li>
                    </ul>
                </div>
            """,
                unsafe_allow_html=True,
            )

        # Wichtige Kontakte
        st.info(
            "📞 **Hilfreiche Kontakte:**\n"
            "- **116 117**: Ärztlicher Bereitsitätsdienst (für Abends & Wochenende)\n"
            "- **112**: Notruf bei lebensbedrohlichen Notfällen"
        )
