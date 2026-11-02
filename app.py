Python

import datetime
import streamlit as st

# =========================================================
# 1. STREAMLIT CONFIG & DESIGN (MEDIZINISCHES UI)
# =========================================================
st.set_page_config(
    page_title="MedicalAssistant – Digitale Vordiagnose & Orientierung",
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
        <p>Erste Einschätzung deiner Symptome zur Orientierung und Entlastung von Arztpraxen.</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        <b>⚠️ Wichtiger medizinischer Hinweis:</b> Diese App dient ausschließlich der ersten Orientierung und ersetzt <b>keinesfalls</b> den Gang zum Arzt oder eine professionelle Diagnose. Bei starken, plötzlichen oder unklaren Beschwerden kontaktiere bitte sofort den ärztlichen Bereitsitätsdienst (116 117) oder den Notruf (112).
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
        "Magen-Darm-Beschwerden (Übelkeit, Bauchschmerzen)",
        "Gelenk- oder Gliederschmerzen",
        "Fieber (leicht bis mäßig)",
        "Sonstiges / Allgemeine Erschöpfung",
    ],
)

col1, col2 = st.columns(2)
with col1:
    dauer = st.selectbox(
        "Wie lange hast du die Symptome schon?",
        [
            "Wenige Stunden",
            "1 bis 2 Tage",
            "3 bis 5 Tage",
            "Länger als eine Woche",
        ],
    )

with col2:
    fieber_ja_nein = st.radio(
        "Hast du aktuell Fieber?",
        ["Nein", "Ja, leichtes Fieber", "Ja, hohes Fieber (> 38.5°C)"],
    )

zusaetzliche_infos = st.text_area(
    "Gibt es noch etwas Wichtiges zu erwähnen? (Optional)",
    placeholder="z.B. Schwindel, Allergien, Vorerkrankungen...",
)

st.markdown("")

# =========================================================
# 4. AUSWERTUNG & AMPEL-SYSTEM
# =========================================================
if st.button("🚀 Vordiagnose & Empfehlung anfordern", type="primary", use_container_width=True):
    if hauptsymptom == "Bitte wählen...":
        st.error("Bitte wähle zuerst ein Hauptsymptom aus.")
    else:
        st.markdown("---")
        st.subheader("💡 Ergebnis & Handlungsempfehlung")

        # Ampel-Logik zur Entlastung vs. Sicherheit
        if "hohes Fieber" in fieber_ja_nein or dauer == "Länger als eine Woche":
            st.markdown(
                """
                <div class="card" style="border-left: 5px solid #e11d48;">
                    <h3 style="color: #e11d48; margin-top:0;">🟡 Empfehlung: Arzttermin in den nächsten Tagen vereinbaren</h3>
                    <p>Da deine Symptome länger anhalten oder von höherem Fieber begleitet werden, empfiehlt sich eine ärztliche Abklärung. Dies ist kein akuter Notfall für die Notaufnahme, aber ein Termin beim Hausarzt ist ratsam.</p>
                    <p><b>Tipp zur Entlastung:</b> Rufe morgens in der Praxis an oder nutze Online-Termintools, anstatt ohne Termin hinzugehen.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="card" style="border-left: 5px solid #16a34a;">
                    <h3 style="color: #16a34a; margin-top:0;">🟢 Empfehlung: Selbstbehandlung zu Hause (Kein Arztbesuch zwingend nötig)</h3>
                    <p>Nach deiner Eingabe handelt es sich vermutlich um einen milden, nicht-akuten Verlauf. Du kannst versuchen, dich zu Hause zu schonen. Damit trägst du aktiv dazu bei, die Wartezimmer von Praxen für echte Notfälle zu entlasten.</p>
                    <br>
                    <b>Bewährte Hausmittel & Tipps:</b>
                    <ul>
                        <li>Viel trinken (stilles Wasser oder Kräutertee)</li>
                        <li>Ausreichend Körperruhe und Schlaf</li>
                        <li>Bei Bedarf Raumklima anpassen und lüften</li>
                    </ul>
                </div>
            """,
                unsafe_allow_html=True,
            )

        # Wichtige Kontakte
        st.info(
            "📞 **Wichtige Nummern:**\n"
            "- **116 117**: Ärztlicher Bereitsitätsdienst (kostenlos, abends & am Wochenende)\n"
            "- **112**: Notruf bei lebensbedrohlichen Notfällen (z.B. Brustschmerzen, Atemnot)"
        )
