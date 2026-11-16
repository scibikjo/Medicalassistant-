
import io
import os
import re
import html
import logging

import numpy as np
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

# =====================================================
# 1. KONFIGURATION
# =====================================================

st.set_page_config(
    page_title="MedicalAssistant Pro",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MedicalAssistant")

MAX_IMAGE_SIZE_MB = 8
MAX_IMAGE_PIXELS = 20_000_000
HF_TIMEOUT = 25

DEFAULT_HF_MODEL = "Salesforce/blip-image-captioning-base"


def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, None)
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(name, default).strip()


HF_TOKEN = get_secret("HF_TOKEN")
HF_MODEL = get_secret("HF_MODEL", DEFAULT_HF_MODEL)

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


# =====================================================
# 2. DESIGN
# =====================================================

st.markdown("""
<style>
@import url(
'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap'
);

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

#MainMenu, footer {
    visibility: hidden !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
    max-width: 1100px !important;
}

.hero-banner {
    background: linear-gradient(
        135deg, #0284c7 0%, #0369a1 50%, #0f766e 100%
    );
    border-radius: 20px;
    padding: 28px 36px;
    color: white;
    margin-bottom: 20px;
}

.hero-banner h1 {
    font-weight: 800;
    font-size: 2.2rem;
    color: white !important;
    margin: 0;
}

.hero-banner p {
    color: #e0f2fe;
    margin-top: 6px;
}

.disclaimer-box {
    background: #fef3c7;
    border-left: 5px solid #d97706;
    padding: 14px 18px;
    border-radius: 10px;
    color: #92400e;
    margin-bottom: 20px;
}

.card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0,0,0,.03);
    margin-bottom: 18px;
}

.befund-box {
    background: #e0f2fe;
    padding: 14px;
    border-radius: 10px;
    color: #0369a1;
    border-left: 4px solid #0284c7;
    margin-bottom: 12px;
}

.emergency-btn {
    display: inline-block;
    background: #dc2626;
    color: white !important;
    font-weight: 700;
    padding: 12px 20px;
    border-radius: 10px;
    text-decoration: none;
    margin-top: 8px;
}

.bereitschaft-btn {
    display: inline-block;
    background: #0284c7;
    color: white !important;
    font-weight: 700;
    padding: 12px 20px;
    border-radius: 10px;
    text-decoration: none;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. KONSTANTEN
# =====================================================

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

DAUER_OPTIONEN = [
    "Wenige Minuten / Akut",
    "Wenige Stunden",
    "1 bis 2 Tage",
    "3 bis 5 Tage",
    "Länger als eine Woche",
]

SCHWERE_OPTIONEN = [
    "Leicht (1-3)",
    "Mäßig (4-7)",
    "Sehr stark / Unerträglich (8-10)",
]

MODUS_AUTO = "Automatische KI-Bildbeschreibung"
MODUS_OK = "Manuell: Unauffällige Struktur"
MODUS_AUFFAELLIG = "Manuell: Auffällige Struktur"
MODUS_OFFEN = "Manuell: Akute offene Verletzung"

MODUS_OPTIONEN = [
    MODUS_AUTO,
    MODUS_OK,
    MODUS_AUFFAELLIG,
    MODUS_OFFEN,
]

NOTFALL_KEYWORDS = [
    "bewusstlos", "ohnmacht", "atemnot", "luftnot",
    "brustschmerz", "brustenge", "schlaganfall",
    "lähmung", "sprachstörung", "krampfanfall",
    "starke blutung", "herzinfarkt", "anaphylax",
    "erstick",
]

AUFFAELLIG_KEYWORDS = [
    "blauer fleck", "hämatom", "prellung",
    "wunde", "schnitt", "schwellung",
    "geschwollen", "blutverdünner",
    "marcumar", "xarelto", "eliquis",
    "sturz", "gestürzt", "eiter",
    "überwärmt", "fieber", "bluterguss",
    "umgeknickt", "verbrenn",
]


# =====================================================
# 4. HILFSFUNKTIONEN
# =====================================================

def esc(value):
    return html.escape(str(value or ""), quote=True)


def normalize_text(value):
    value = (value or "").lower()
    value = value.replace("ä", "ae")
    value = value.replace("ö", "oe")
    value = value.replace("ü", "ue")
    value = value.replace("ß", "ss")
    return re.sub(r"\s+", " ", value).strip()


def hat_keyword(text, keyword):
    text = normalize_text(text)
    keyword = normalize_text(keyword)

    for match in re.finditer(re.escape(keyword), text):
        davor = text[max(0, match.start() - 35):match.start()]

        if re.search(
            r"\b(kein|keine|keinen|keiner|keinem|ohne|nicht|nie)\b"
            r"(?:\s+\w+){0,3}\s*$",
            davor,
        ):
            continue

        return True

    return False


def finde_keywords(text, keywords):
    return [
        keyword
        for keyword in keywords
        if hat_keyword(text, keyword)
    ]


# =====================================================
# 5. BILDVALIDIERUNG
# =====================================================

def validiere_bild(datei_bytes):

    if not datei_bytes:
        return False, "Die Bilddatei ist leer."

    if len(datei_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        return False, "Das Bild überschreitet 8 MB."

    try:
        with Image.open(io.BytesIO(datei_bytes)) as img:
            img.verify()

        with Image.open(io.BytesIO(datei_bytes)) as img:
            width, height = img.size

            if width < 32 or height < 32:
                return False, "Das Bild ist zu klein."

            if width * height > MAX_IMAGE_PIXELS:
                return False, "Zu viele Bildpixel."

            if img.format not in ("JPEG", "PNG"):
                return False, "Nur JPG und PNG sind erlaubt."

        return True, "Bild erfolgreich validiert."

    except Exception:
        return False, "Bild beschädigt oder nicht lesbar."


def bereite_bild_vor(datei_bytes):

    with Image.open(io.BytesIO(datei_bytes)) as original:
        img = ImageOps.exif_transpose(original)
        img = img.convert("RGB")
        img.thumbnail((1024, 1024))

        output = io.BytesIO()

        img.save(
            output,
            format="JPEG",
            quality=88,
            optimize=True,
        )

        return output.getvalue()


# =====================================================
# 6. HUGGING FACE API
# =====================================================

@st.cache_resource(show_spinner=False)
def lade_hf_client(token, timeout):

    if not token:
        return None

    from huggingface_hub import InferenceClient

    return InferenceClient(
        provider="auto",
        api_key=token,
        timeout=timeout,
    )


def hf_bildanalyse(datei_bytes):

    result = {
        "success": False,
        "text": "",
        "error": "",
    }

    if not HF_TOKEN:
        result["error"] = "Kein HF Token konfiguriert."
        return result

    try:
        client = lade_hf_client(HF_TOKEN, HF_TIMEOUT)

        if client is None:
            result["error"] = "Client nicht verfügbar."
            return result

        response = client.image_to_text(
            datei_bytes,
            model=HF_MODEL,
        )

        description = getattr(
            response,
            "generated_text",
            None,
        )

        if not description and isinstance(response, dict):
            description = response.get("generated_text", "")

        if not description and isinstance(response, str):
            description = response

        description = str(description or "").strip()

        if not description:
            result["error"] = "Keine Beschreibung erhalten."
            return result

        result["success"] = True
        result["text"] = description[:3000]

        return result

    except Exception as exc:
        logger.warning(
            "HF API Fehler: %s",
            type(exc).__name__,
        )

        result["error"] = (
            "Hugging Face nicht erreichbar: "
            + type(exc).__name__
        )

        return result

# =====================================================
# 7. LOKALER BILDANALYSE-FALLBACK
# =====================================================

def lokaler_bild_fallback(datei_bytes):

    result = {
        "success": False,
        "source": "Lokaler Fallback",
        "text": "",
        "error": "",
    }

    try:
        with Image.open(io.BytesIO(datei_bytes)) as original:

            img = ImageOps.exif_transpose(original)
            img = img.convert("RGB")
            img.thumbnail((320, 320))

            arr = np.asarray(img, dtype=np.float32)

        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError("Ungültige Bilddimensionen")

        gray = (
            0.299 * arr[:, :, 0]
            + 0.587 * arr[:, :, 1]
            + 0.114 * arr[:, :, 2]
        )

        brightness = float(np.mean(gray))

        sharpness = float(
            np.var(np.diff(gray, axis=0))
            + np.var(np.diff(gray, axis=1))
        )

        if brightness < 30:
            quality = "Sehr dunkel"

        elif brightness > 225:
            quality = "Stark überbelichtet"

        elif sharpness < 15:
            quality = "Möglicherweise unscharf"

        else:
            quality = "Technisch grundsätzlich lesbar"

        result["success"] = True

        result["text"] = (
            "Lokale technische Bildprüfung abgeschlossen. "
            f"Helligkeit: {brightness:.1f}/255. "
            f"Schärfemaß: {sharpness:.1f}. "
            f"Qualität: {quality}. "
            "Eine medizinische Beurteilung ist nicht möglich."
        )

        return result

    except Exception as exc:

        logger.warning(
            "Fallback fehlgeschlagen: %s",
            type(exc).__name__,
        )

        result["error"] = type(exc).__name__

        result["text"] = (
            "Das Bild konnte lokal nicht verarbeitet werden."
        )

        return result


# =====================================================
# 8. ZENTRALE BILDANALYSE
# =====================================================

def analysiere_bild(datei_bytes):

    result = {
        "success": False,
        "unsicher": True,
        "auffaellig": False,
        "text": "",
        "details": "",
        "source": "",
        "error": "",
    }

    valid, message = validiere_bild(datei_bytes)

    if not valid:
        result["text"] = message
        result["error"] = message
        return result

    try:
        prepared = bereite_bild_vor(datei_bytes)

    except Exception:
        logger.exception("Bildvorbereitung fehlgeschlagen")

        result["text"] = (
            "Das Bild konnte nicht vorbereitet werden."
        )

        return result

    # Zuerst Hugging Face versuchen

    api_result = hf_bildanalyse(prepared)

    if api_result["success"]:

        result["success"] = True
        result["source"] = "Hugging Face Inference API"

        result["text"] = (
            "KI-generierte Bildbeschreibung: "
            + api_result["text"]
        )

        result["details"] = (
            "Verwendetes Modell: " + HF_MODEL
        )

        # Keine medizinische Diagnose aus der KI ableiten.
        result["unsicher"] = True
        result["auffaellig"] = False

        return result

    # Bei API-Ausfall lokalen Fallback verwenden

    fallback = lokaler_bild_fallback(prepared)

    result["source"] = fallback["source"]
    result["success"] = fallback["success"]

    result["text"] = (
        "Hugging Face war nicht verfügbar. "
        + fallback["text"]
    )

    result["details"] = (
        "API-Status: " + api_result["error"]
    )

    result["error"] = api_result["error"]

    # Der Fallback kann keine Entwarnung geben.
    result["unsicher"] = True
    result["auffaellig"] = False

    return result


# =====================================================
# 9. KLINISCHE DEMONSTRATIONS-TRIAGE
# =====================================================

def berechne_triage(eingaben):

    kategorie = eingaben["kategorie"]
    schwere = eingaben["schwere"]
    dauer = eingaben["dauer"]
    modus = eingaben["modus"]

    text = " ".join([
        kategorie,
        eingaben["hergang"],
        eingaben["notizen"],
    ])

    stufe = 0
    gruende = []
    hinweise = []

    # -------------------------------------------------
    # NOTFALLHINWEISE
    # -------------------------------------------------

    treffer_notfall = finde_keywords(
        text,
        NOTFALL_KEYWORDS,
    )

    if kategorie in KATEGORIEN_NOTFALL:

        stufe = 2

        gruende.append(
            "Die ausgewählte Hauptbeschwerde kann "
            "auf einen medizinischen Notfall hinweisen."
        )

    if treffer_notfall:

        stufe = 2

        gruende.append(
            "Mögliche Notfall-Schlüsselwörter: "
            + ", ".join(treffer_notfall)
        )

    if modus == MODUS_OFFEN:

        stufe = 2

        gruende.append(
            "Manuell wurde eine akute offene Verletzung ausgewählt."
        )

    # -------------------------------------------------
    # BILDANALYSE
    # -------------------------------------------------

    bild_log = "Kein Bild hochgeladen."
    bild_details = ""
    bild_unsicher = False

    if modus == MODUS_OK:

        bild_log = (
            "Manuelle Demonstrationsauswahl: "
            "Struktur als unauffällig markiert. "
            "Keine medizinische Validierung."
        )

    elif modus == MODUS_AUFFAELLIG:

        bild_log = (
            "Manuelle Demonstrationsauswahl: "
            "Auffällige Struktur markiert."
        )

        stufe = max(stufe, 1)

        gruende.append(
            "Manuell wurde eine auffällige Struktur angegeben."
        )

    elif modus == MODUS_OFFEN:

        bild_log = (
            "Manuelle Demonstrationsauswahl: "
            "Akute offene Verletzung."
        )

    elif eingaben["bild_bytes"] is not None:

        bild_result = analysiere_bild(
            eingaben["bild_bytes"]
        )

        bild_log = bild_result["text"]

        bild_details = bild_result["details"]

        bild_unsicher = bild_result["unsicher"]

        if not bild_result["success"]:

            hinweise.append(
                "Das Bild konnte nicht vollständig ausgewertet werden."
            )

    # -------------------------------------------------
    # WEITERE AUFFÄLLIGKEITEN
    # -------------------------------------------------

    treffer = finde_keywords(
        text,
        AUFFAELLIG_KEYWORDS,
    )

    if treffer:

        stufe = max(stufe, 1)

        gruende.append(
            "Weitere Hinweise in der Beschreibung: "
            + ", ".join(treffer)
        )

    if schwere == SCHWERE_OPTIONEN[2]:

        stufe = max(stufe, 1)

        gruende.append(
            "Sehr starke Schmerzen wurden angegeben."
        )

    if kategorie in {
        "Schnittwunde / Verbrennung / Äußere Verletzung"
    }:

        stufe = max(stufe, 1)

        gruende.append(
            "Die gewählte Verletzungskategorie sollte "
            "ärztlich beurteilt werden."
        )

    if (
        dauer == DAUER_OPTIONEN[4]
        and kategorie != "Sonstiges / Allgemeine Beschwerden"
    ):

        stufe = max(stufe, 1)

        gruende.append(
            "Die Beschwerden bestehen länger als eine Woche."
        )

    normalized = normalize_text(text)

    if (
        any(
            name in normalized
            for name in [
                "blutverdunner",
                "marcumar",
                "xarelto",
                "eliquis",
            ]
        )
        and (
            kategorie in KATEGORIEN_VERLETZUNG
            or "sturz" in normalized
            or "gesturzt" in normalized
        )
    ):

        stufe = max(stufe, 1)

        gruende.append(
            "Blutverdünner in Verbindung mit einer Verletzung "
            "erfordern besondere Aufmerksamkeit."
        )

    # -------------------------------------------------
    # UNSICHERE BILDER
    # -------------------------------------------------

    if (
        eingaben["bild_bytes"] is not None
        and bild_unsicher
        and stufe == 0
    ):

        stufe = 1

        gruende.append(
            "Die Bildanalyse ermöglicht keine medizinische "
            "Entwarnung. Bei entsprechenden Beschwerden "
            "ist eine ärztliche Einschätzung erforderlich."
        )

    # -------------------------------------------------
    # ERGEBNIS
    # -------------------------------------------------

    if stufe == 0:

        gruende.append(
            "Die implementierten Demonstrationsregeln "
            "haben keine entsprechenden Warnhinweise erkannt. "
            "Dies ist keine medizinische Entwarnung."
        )

    return {
        "stufe": stufe,
        "gruende": gruende,
        "bild_log": bild_log,
        "bild_details": bild_details,
        "hinweise": hinweise,
        "hergang": eingaben["hergang"],
    }


# =====================================================
# 10. ERGEBNISDARSTELLUNG
# =====================================================

def render_ergebnis(res):

    stufe = res["stufe"]

    st.markdown("#### 🩺 Strukturierte Auswertung")

    st.markdown(
        f"""
        <div class="befund-box">
            <b>Bildverarbeitung:</b><br>
            {esc(res["bild_log"])}
            <br><br>
            <b>Hergang:</b><br>
            {esc(res["hergang"]) or "Keine Angaben"}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------
    # STUFE 2
    # -------------------------------------------------

    if stufe == 2:

        st.error(
            "🚨 Möglicher Notfall – sofortige Notfallversorgung."
        )

        st.markdown(
            "Bei akuter Lebensgefahr sofort 112 wählen."
        )

        st.markdown(
            '<a class="emergency-btn" href="tel:112">'
            '📞 112 anrufen</a>',
            unsafe_allow_html=True,
        )

    # -------------------------------------------------
    # STUFE 1
    # -------------------------------------------------

    elif stufe == 1:

        st.warning(
            "🟡 Ärztliche Abklärung empfohlen."
        )

        st.write(
            "Bei dringenden, nicht lebensbedrohlichen "
            "Beschwerden kann 116117 kontaktiert werden."
        )

        st.markdown(
            '<a class="bereitschaft-btn" href="tel:116117">'
            '📞 116 117 anrufen</a>',
            unsafe_allow_html=True,
        )

    # -------------------------------------------------
    # STUFE 0
    # -------------------------------------------------

    else:

        st.info(
            "ℹ️ Keine entsprechenden Warnhinweise in den "
            "implementierten Demonstrationsregeln erkannt."
        )

        st.write(
            "Dies schließt eine Erkrankung oder Verletzung "
            "nicht aus."
        )

    # -------------------------------------------------
    # BEGRÜNDUNG
    # -------------------------------------------------

    st.markdown("#### Begründung der Einstufung")

    for grund in res["gruende"]:
        st.markdown(f"- {grund}")

    for hinweis in res["hinweise"]:
        st.warning(hinweis)

    if res["bild_details"]:

        with st.expander("Technische Details der Bildanalyse"):
            st.write(res["bild_details"])

# =====================================================
# 11. SESSION STATE
# =====================================================

if "triage_ergebnis" not in st.session_state:
    st.session_state.triage_ergebnis = None


# =====================================================
# 12. HEADER
# =====================================================

st.markdown(
    """
    <div class="hero-banner">
        <h1>🩺 MedicalAssistant Pro</h1>
        <p>
            Erweiterte klinische Demonstration,
            strukturierte Anamnese und KI-gestützte
            Bildbeschreibung.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        <b>⚠️ Medizinischer Sicherheitshinweis</b><br>
        Diese Anwendung ist ein technischer
        Demonstrationsprototyp. Sie ersetzt keine
        ärztliche Untersuchung, Diagnose oder Behandlung.
        Die KI-Bildbeschreibung ist kein medizinischer Befund.
        Bei akuter Lebensgefahr sofort 112 wählen.
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# 13. API STATUS
# =====================================================

col_api1, col_api2 = st.columns(2)

with col_api1:

    if HF_TOKEN:
        st.success(
            "🟢 Hugging Face Token konfiguriert"
        )

    else:
        st.warning(
            "🟡 Kein HF Token – lokaler Fallback verfügbar"
        )

with col_api2:

    st.info(
        f"KI-Modell: {HF_MODEL}"
    )


# =====================================================
# 14. TABS
# =====================================================

tab1, tab2, tab3 = st.tabs([
    "🩺 1. Anamnese & Befund",
    "💡 2. Klinische Auswertung",
    "🗺️ 3. Notdienst- & Praxensuche",
])


# =====================================================
# 15. TAB 1 – ANAMNESE
# =====================================================

with tab1:

    st.markdown(
        "### 🔍 Schritt 1: Beschwerden, Vorfall und Bild erfassen"
    )

    col_haupt, col_foto = st.columns(
        [1, 1],
        gap="medium",
    )

    # -------------------------------------------------
    # LINKER BEREICH
    # -------------------------------------------------

    with col_haupt:

        hauptsymptom = st.selectbox(
            "Hauptbeschwerde / Symptomkategorie:",
            SYMPTOM_OPTIONEN,
            key="hauptsymptom",
        )

        col1, col2 = st.columns(2)

        with col1:

            dauer = st.selectbox(
                "Dauer der Beschwerden:",
                DAUER_OPTIONEN,
                key="dauer",
            )

        with col2:

            schweregrad = st.selectbox(
                "Intensität / Schmerzlevel:",
                SCHWERE_OPTIONEN,
                key="schweregrad",
            )

        unfallhergang = st.text_area(
            "📝 Wie ist es passiert?",
            placeholder=(
                "z.B. Stark gestoßen, gestürzt, "
                "beim Sport umgeknickt oder seit gestern "
                "großflächig verfärbt..."
            ),
            max_chars=3000,
            key="unfallhergang",
        )

    # -------------------------------------------------
    # RECHTER BEREICH
    # -------------------------------------------------

    with col_foto:

        uploaded_file = st.file_uploader(
            "📸 Medizinische Fotodokumentation",
            type=["jpg", "jpeg", "png"],
            key="uploaded_file",
            help=(
                "Optional. Maximal 8 MB. "
                "Die KI erstellt eine Bildbeschreibung, "
                "keine medizinische Diagnose."
            ),
        )

        bild_bytes = None

        if uploaded_file is not None:

            try:

                bild_bytes = uploaded_file.getvalue()

                valid, message = validiere_bild(
                    bild_bytes
                )

                if valid:

                    st.image(
                        bild_bytes,
                        caption="Hochgeladenes Untersuchungsbild",
                        width=280,
                    )

                    st.success(message)

                else:

                    st.error(message)
                    bild_bytes = None

            except Exception:

                logger.exception(
                    "Fehler bei der Bildvorschau"
                )

                st.error(
                    "Das Bild konnte nicht geladen werden."
                )

                bild_bytes = None

        visueller_eindruck = st.selectbox(
            "🔬 Bildbewertung / Analysemodus:",
            MODUS_OPTIONEN,
            key="visueller_eindruck",
            help=(
                "Automatisch: Hugging Face Bildbeschreibung "
                "mit lokalem Fallback. Manuell: "
                "Präsentationsmodus. Keine medizinische "
                "Diagnose."
            ),
        )

    # -------------------------------------------------
    # ZUSÄTZLICHE NOTIZEN
    # -------------------------------------------------

    st.markdown("#### 📝 Weitere Informationen")

    zusaetzliche_notizen = st.text_area(
        "Zusätzliche Beobachtungen:",
        placeholder=(
            "z.B. Vorerkrankungen, Blutverdünner, "
            "Allergien oder weitere Beschwerden..."
        ),
        max_chars=3000,
        key="zusaetzliche_notizen",
    )

    st.divider()

    # -------------------------------------------------
    # AUSWERTUNG STARTEN
    # -------------------------------------------------

    if st.button(
        "🚀 Klinische Auswertung starten",
        type="primary",
        use_container_width=True,
    ):

        if hauptsymptom == "Bitte wählen...":

            st.error(
                "Bitte wähle zuerst eine Hauptbeschwerde aus."
            )

        elif uploaded_file is not None and bild_bytes is None:

            st.error(
                "Das hochgeladene Bild ist ungültig. "
                "Bitte lade eine gültige JPG- oder PNG-Datei hoch."
            )

        else:

            try:

                with st.spinner(
                    "Anamnese und Bilddaten werden verarbeitet..."
                ):

                    inputs = {
                        "kategorie": hauptsymptom,
                        "dauer": dauer,
                        "schwere": schweregrad,
                        "hergang": unfallhergang,
                        "notizen": zusaetzliche_notizen,
                        "modus": visueller_eindruck,
                        "bild_bytes": bild_bytes,
                    }

                    result = berechne_triage(inputs)

                    st.session_state.triage_ergebnis = result

                st.success(
                    "✅ Auswertung abgeschlossen! "
                    "Bitte öffne jetzt Tab 2."
                )

            except Exception:

                logger.exception(
                    "Fehler bei der Auswertung"
                )

                st.session_state.triage_ergebnis = None

                st.error(
                    "Die Auswertung konnte nicht abgeschlossen "
                    "werden. Bitte überprüfe deine Eingaben."
                )


# =====================================================
# 16. TAB 2 – AUSWERTUNG
# =====================================================

with tab2:

    st.markdown(
        "### 💡 Strukturierte Ersteinschätzung und Auswertung"
    )

    ergebnis = st.session_state.triage_ergebnis

    if ergebnis is None:

        st.info(
            "ℹ️ Bitte fülle zuerst die Anamnese in Tab 1 aus "
            "und starte die klinische Auswertung."
        )

    else:

        render_ergebnis(ergebnis)

        st.divider()

        st.caption(
            "Die dargestellte Einstufung basiert auf "
            "vereinfachten Demonstrationsregeln und ist "
            "keine klinisch validierte Triage."
        )

        if st.button(
            "🔄 Neue Auswertung starten",
            use_container_width=True,
        ):

            st.session_state.triage_ergebnis = None

            st.rerun()


# =====================================================
# 17. TAB 3 – NOTDIENST- UND PRAXENSUCHE
# =====================================================

with tab3:

    st.markdown(
        "### 🗺️ Ärztlicher Bereitschaftsdienst"
    )

    st.write(
        "Geben Sie Ihre Postleitzahl ein, um die "
        "Informationen zum ärztlichen Bereitschaftsdienst "
        "aufzurufen."
    )

    plz_eingabe = st.text_input(
        "Postleitzahl eingeben:",
        placeholder="z.B. 23552",
        max_chars=5,
        key="plz",
    )

    plz = plz_eingabe.strip()

    if plz:

        if not re.fullmatch(r"\d{5}", plz):

            st.warning(
                "Bitte eine gültige fünfstellige "
                "deutsche Postleitzahl eingeben."
            )

        else:

            st.success(
                f"📍 Angegebene Postleitzahl: {plz}"
            )

            st.markdown(
                f"""
                <div class="card">

                    <h3>
                        🏥 Ärztlicher Bereitschaftsdienst
                    </h3>

                    <p>
                        <b>Ihre Postleitzahl:</b> {esc(plz)}
                    </p>

                    <p>
                        Außerhalb der regulären Praxiszeiten
                        erreichen Sie den ärztlichen
                        Bereitschaftsdienst unter
                        <b>116 117</b>.
                    </p>

                    <p>
                        Dort erfahren Sie, welche
                        Bereitschaftspraxis zuständig ist
                        und welche Einrichtung aktuell
                        geöffnet hat.
                    </p>

                    <p>
                        <b>Bei akuter Lebensgefahr:</b>
                        112 wählen.
                    </p>

                    <a
                        href="tel:116117"
                        class="bereitschaft-btn"
                    >
                        📞 116 117 anrufen
                    </a>

                    <a
                        href="tel:112"
                        class="emergency-btn"
                    >
                        🚨 112 Notruf
                    </a>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.link_button(
                "🔎 Offizielle Bereitschaftspraxissuche öffnen",
                "https://www.116117.de",
                use_container_width=True,
            )

    else:

        st.info(
            "💡 Bitte gib deine Postleitzahl ein, "
            "um die Notdienstinformationen anzuzeigen."
        )


# =====================================================
# 18. FOOTER
# =====================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#64748b;
        padding:15px;
        font-size:0.85rem;
    ">
        <b>🩺 MedicalAssistant Pro</b><br>
        Professional Demonstration Edition<br>
        KI-Bildbeschreibung und strukturierte
        Symptomerfassung<br><br>
        Keine medizinische Diagnose oder Therapieempfehlung.
    </div>
    """,
    unsafe_allow_html=True,
)
