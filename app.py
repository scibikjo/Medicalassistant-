
# ============================================================
# MEDICALASSISTANT PRO
# TEIL 1 VON 4
# Konfiguration, Imports, Design und Konstanten
# ============================================================

import io
import os
import re
import base64
import logging
import html

from typing import Optional

import requests
import numpy as np
import streamlit as st

from PIL import Image, ImageOps, ImageFilter


# ============================================================
# 1. STREAMLIT KONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MedicalAssistant Pro",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("MedicalAssistant")


# ============================================================
# 3. HUGGING FACE KONFIGURATION
# ============================================================

APP_NAME = "MedicalAssistant Pro"

HF_MODEL = "Qwen/Qwen2.5-VL-3B-Instruct"

HF_API_URL = (
    "https://router.huggingface.co/v1/chat/completions"
)

MAX_IMAGE_SIZE = 8 * 1024 * 1024

MAX_IMAGE_DIMENSION = 1600

REQUEST_TIMEOUT = (10, 90)


# Token aus Streamlit Secrets oder Umgebungsvariable laden

try:
    HF_TOKEN = st.secrets.get("HF_TOKEN", "")
except Exception:
    HF_TOKEN = os.getenv("HF_TOKEN", "")

if not isinstance(HF_TOKEN, str):
    HF_TOKEN = ""


# ============================================================
# 4. DESIGN / CSS
# ============================================================

st.markdown(
    """
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
        max-width: 1100px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
    }

    .hero {
        background: linear-gradient(
            135deg,
            #0284c7,
            #0369a1,
            #0f766e
        );

        border-radius: 20px;
        padding: 30px;
        color: white;
        margin-bottom: 20px;

        box-shadow:
            0 10px 25px rgba(2,132,199,.2);
    }

    .hero h1 {
        color: white !important;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
    }

    .hero p {
        color: #e0f2fe;
        margin-bottom: 0;
    }

    .disclaimer {
        background: #fef3c7;
        border-left: 5px solid #d97706;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #92400e;
    }

    .card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 15px;
    }

    .footer {
        text-align: center;
        color: #64748b;
        font-size: .85rem;
        padding: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 5. SYMPTOM-KONSTANTEN
# ============================================================

SYMPTOME = [

    "Bitte wählen...",

    "Blauer Fleck / Hämatom / Prellung",

    "Hautausschlag / Rötung / Schwellung / Wunde",

    "Gelenk- oder Gliederschmerzen / Sportverletzung",

    "Schnittwunde / Verbrennung / Äußere Verletzung",

    "Kopfschmerzen / Migräne / Schwindel",

    "Erkältung / Halsschmerzen / Husten / Fieber",

    "Magen-Darm-Beschwerden / Übelkeit",

    "Brustschmerzen / Engegefühl",

    "Plötzliche Atemnot / Luftnot",

    "Sonstiges / Allgemeine Beschwerden",

]


# ============================================================
# 6. DAUER UND SCHWEREGRAD
# ============================================================

DAUER = [

    "Wenige Minuten / Akut",

    "Wenige Stunden",

    "1 bis 2 Tage",

    "3 bis 5 Tage",

    "Länger als eine Woche",

]


SCHWERE = [

    "Leicht (1-3)",

    "Mäßig (4-7)",

    "Sehr stark / Unerträglich (8-10)",

]


# ============================================================
# 7. ANALYSE-MODI
# ============================================================

MODI = [

    "Automatische Bildbeschreibung",

    "Manuelle Dokumentation",

]


# ============================================================
# 8. KATEGORIEN
# ============================================================

NOTFALL_KATEGORIEN = {

    "Brustschmerzen / Engegefühl",

    "Plötzliche Atemnot / Luftnot",

}


VERLETZUNGEN = {

    "Blauer Fleck / Hämatom / Prellung",

    "Hautausschlag / Rötung / Schwellung / Wunde",

    "Gelenk- oder Gliederschmerzen / Sportverletzung",

    "Schnittwunde / Verbrennung / Äußere Verletzung",

}


# ============================================================
# 9. NOTFALL-SCHLÜSSELWÖRTER
# ============================================================

NOTFALL_KEYWORDS = [

    "bewusstlos",

    "atemnot",

    "luftnot",

    "brustschmerz",

    "brustenge",

    "schlaganfall",

    "halbseitig gelähmt",

    "sprachstörung",

    "krampfanfall",

    "starke blutung",

    "blutet stark",

    "herzinfarkt",

    "anaphylaxie",

    "erstickung",

]


# ============================================================
# ENDE TEIL 1
# ============================================================

# ============================================================
# MEDICALASSISTANT PRO
# TEIL 2 VON 4
# Bildverarbeitung und Hugging Face API
# ============================================================


# ============================================================
# 10. HILFSFUNKTIONEN
# ============================================================

def normalisiere(text: str) -> str:
    """Normalisiert Texteingaben."""

    return (text or "").strip().lower()


def esc(text: str) -> str:
    """Sicheres Maskieren von HTML."""

    return html.escape(str(text or ""), quote=True)


# ============================================================
# 11. BILDVALIDIERUNG
# ============================================================

def validiere_bild(data: bytes):

    if not data:
        return False, "Keine Bilddaten vorhanden."

    if len(data) > MAX_IMAGE_SIZE:
        return False, "Das Bild überschreitet die maximale Größe von 8 MB."

    try:

        with Image.open(io.BytesIO(data)) as img:

            if img.format not in ("JPEG", "PNG"):
                return False, "Nur JPG- und PNG-Dateien sind erlaubt."

            img.verify()

        return True, "Bild erfolgreich validiert."

    except Exception:

        logger.exception("Bildvalidierung fehlgeschlagen")

        return False, "Die Bilddatei ist beschädigt oder ungültig."


# ============================================================
# 12. BILD VORBEREITEN
# ============================================================

def bereite_bild_vor(data: bytes) -> bytes:

    """
    Normalisiert das Bild.
    Entfernt EXIF-Metadaten.
    Konvertiert das Bild in JPEG.
    """

    with Image.open(io.BytesIO(data)) as original:

        img = ImageOps.exif_transpose(original)

        img = img.convert("RGB")

        img.thumbnail(
            (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION)
        )

        output = io.BytesIO()

        img.save(
            output,
            format="JPEG",
            quality=88,
            optimize=True,
        )

        return output.getvalue()


# ============================================================
# 13. HUGGING FACE VISION API
# ============================================================

def hf_bildanalyse(bild_bytes: bytes) -> dict:

    result = {

        "success": False,

        "text": "",

        "error": "",

        "source": "Hugging Face",

    }

    # Token prüfen

    if not HF_TOKEN:

        result["error"] = (
            "HF_TOKEN fehlt. Bitte Hugging Face Token konfigurieren."
        )

        return result

    try:

        # Bild in Base64 umwandeln

        image_base64 = base64.b64encode(
            bild_bytes
        ).decode("ascii")

        image_url = (
            "data:image/jpeg;base64,"
            + image_base64
        )

        # API Header

        headers = {

            "Authorization": f"Bearer {HF_TOKEN}",

            "Content-Type": "application/json",

        }

        # API Anfrage

        payload = {

            "model": HF_MODEL,

            "messages": [

                {

                    "role": "user",

                    "content": [

                        {

                            "type": "text",

                            "text": (

                                "Beschreibe dieses Bild objektiv auf Deutsch. "

                                "Nenne sichtbare Farben, Formen, Oberflächen "
                                "und die Bildqualität. "

                                "Stelle keine medizinische Diagnose. "

                                "Behaupte nicht, dass etwas harmlos ist. "

                                "Gib keine medizinische Entwarnung."

                            ),

                        },

                        {

                            "type": "image_url",

                            "image_url": {

                                "url": image_url

                            },

                        },

                    ],

                }

            ],

            "max_tokens": 250,

            "temperature": 0.1,

            "stream": False,

        }

        response = requests.post(

            HF_API_URL,

            headers=headers,

            json=payload,

            timeout=REQUEST_TIMEOUT,

        )

        # HTTP Status kontrollieren

        if response.status_code != 200:

            result["error"] = (

                f"HTTP {response.status_code}: "
                + response.text[:400]

            )

            logger.error(
                "Hugging Face Fehler: %s",
                result["error"]
            )

            return result

        # JSON auslesen

        data = response.json()

        choices = data.get("choices")

        if not isinstance(choices, list) or not choices:

            result["error"] = (
                "API lieferte keine gültigen Ergebnisse."
            )

            return result

        message = choices[0].get("message", {})

        content = message.get("content", "")

        # Unterschiedliche Antwortformate abfangen

        if isinstance(content, list):

            content = " ".join(

                item.get("text", "")

                for item in content

                if isinstance(item, dict)

            )

        if not isinstance(content, str) or not content.strip():

            result["error"] = (
                "Die API lieferte keinen Beschreibungstext."
            )

            return result

        result["success"] = True

        result["text"] = content.strip()

        return result

    # --------------------------------------------------------
    # FEHLERBEHANDLUNG
    # --------------------------------------------------------

    except requests.exceptions.Timeout:

        result["error"] = (
            "Zeitüberschreitung bei Hugging Face."
        )

    except requests.exceptions.ConnectionError:

        result["error"] = (
            "Keine Verbindung zu Hugging Face möglich."
        )

    except requests.exceptions.RequestException as exc:

        result["error"] = (
            f"HTTP-Anfrage fehlgeschlagen: {type(exc).__name__}"
        )

    except (ValueError, KeyError, TypeError, IndexError) as exc:

        result["error"] = (
            f"Ungültige API-Antwort: {type(exc).__name__}"
        )

    except Exception as exc:

        logger.exception(
            "Unerwarteter Hugging Face Fehler"
        )

        result["error"] = (
            f"{type(exc).__name__}: {str(exc)[:200]}"
        )

    return result


# ============================================================
# 14. LOKALER BILDFALLBACK
# ============================================================

def lokaler_fallback(bild_bytes: bytes) -> dict:

    result = {

        "success": False,

        "text": "",

        "details": "",

    }

    try:

        with Image.open(io.BytesIO(bild_bytes)) as original:

            img = ImageOps.exif_transpose(original)

            img = img.convert("RGB")

            img.thumbnail((320, 320))

            gray = np.asarray(

                img.convert("L"),

                dtype=np.float32,

            )

        # Helligkeit

        brightness = float(gray.mean())

        # Technisches Schärfemaß

        sharpness = float(

            np.var(np.diff(gray, axis=0))

            + np.var(np.diff(gray, axis=1))

        )

        # Qualität klassifizieren

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

            "Eine medizinische Beurteilung ist nicht möglich."

        )

        result["details"] = (

            f"Helligkeit: {brightness:.1f}/255 | "

            f"Schärfemaß: {sharpness:.1f} | "

            f"Qualität: {quality}"

        )

    except Exception:

        logger.exception(
            "Lokaler Bildfallback fehlgeschlagen"
        )

        result["text"] = (
            "Lokale Bildverarbeitung fehlgeschlagen."
        )

    return result


# ============================================================
# 15. ZENTRALE BILDANALYSE
# ============================================================

def analysiere_bild(bild_bytes: bytes) -> dict:

    result = {

        "success": False,

        "text": "",

        "details": "",

        "source": "",

        "error": "",

    }

    # Bild überprüfen

    valid, message = validiere_bild(bild_bytes)

    if not valid:

        result["text"] = message

        result["error"] = message

        return result

    # Bild vorbereiten

    try:

        prepared = bereite_bild_vor(bild_bytes)

    except Exception:

        logger.exception(
            "Bildvorbereitung fehlgeschlagen"
        )

        result["text"] = (
            "Bild konnte nicht vorbereitet werden."
        )

        return result

    # Zuerst Hugging Face versuchen

    api_result = hf_bildanalyse(prepared)

    if api_result["success"]:

        result["success"] = True

        result["source"] = "Hugging Face Vision API"

        result["text"] = api_result["text"]

        result["details"] = (
            f"Verwendetes Modell: {HF_MODEL}"
        )

        return result

    # Bei API-Fehler lokalen Fallback nutzen

    fallback = lokaler_fallback(prepared)

    result["success"] = fallback["success"]

    result["source"] = "Lokaler technischer Fallback"

    result["text"] = (

        "Hugging Face war nicht verfügbar.\n\n"

        + fallback["text"]

    )

    result["details"] = (

        f"API-Fehler: {api_result['error']}\n"

        + fallback["details"]

    )

    result["error"] = api_result["error"]

    return result


# ============================================================
# ENDE TEIL 2
# ============================================================

# ============================================================
# MEDICALASSISTANT PRO
# TEIL 3 VON 4
# TRIAGE UND ERGEBNISDARSTELLUNG
# ============================================================


# ============================================================
# 16. KEYWORD-ERKENNUNG
# ============================================================

def finde_notfall_keywords(text: str) -> list:

    text = normalisiere(text)

    treffer = []

    for keyword in NOTFALL_KEYWORDS:

        if keyword in text:

            treffer.append(keyword)

    return treffer


# ============================================================
# 17. TRIAGE-BERECHNUNG
# ============================================================

def berechne_triage(eingaben: dict) -> dict:

    """
    Demonstrations-Triage.

    Stufe 0 = Keine programmierte Warnregel ausgelöst.
    Stufe 1 = Ärztliche Abklärung empfohlen.
    Stufe 2 = Möglicher Notfall.

    Wichtig:
    Diese Regeln sind nicht klinisch validiert.
    Sie ersetzen keine medizinische Triage.
    """

    kategorie = eingaben["kategorie"]

    schwere = eingaben["schwere"]

    dauer = eingaben["dauer"]

    hergang = eingaben.get("hergang", "")

    notizen = eingaben.get("notizen", "")

    bild_result = eingaben.get("bild_result")

    text = normalisiere(

        " ".join([

            kategorie,

            hergang,

            notizen,

        ])

    )

    stufe = 0

    gruende = []

    # --------------------------------------------------------
    # 1. NOTFALLKATEGORIEN
    # --------------------------------------------------------

    if kategorie in NOTFALL_KATEGORIEN:

        stufe = 2

        gruende.append(

            "Die ausgewählte Hauptbeschwerde kann einen "
            "akuten medizinischen Notfall darstellen."

        )

    # --------------------------------------------------------
    # 2. NOTFALL-SCHLÜSSELWÖRTER
    # --------------------------------------------------------

    notfall_treffer = finde_notfall_keywords(text)

    if notfall_treffer:

        stufe = 2

        gruende.append(

            "Mögliche Notfallhinweise im Beschreibungstext: "

            + ", ".join(notfall_treffer)

        )

    # --------------------------------------------------------
    # 3. VERLETZUNGEN
    # --------------------------------------------------------

    if kategorie in VERLETZUNGEN:

        stufe = max(stufe, 1)

        gruende.append(

            "Verletzungsbedingte Beschwerden wurden angegeben. "
            "Eine ärztliche Beurteilung kann erforderlich sein."

        )

    # --------------------------------------------------------
    # 4. SCHMERZINTENSITÄT
    # --------------------------------------------------------

    if schwere == SCHWERE[2]:

        stufe = max(stufe, 1)

        gruende.append(

            "Sehr starke oder unerträgliche Schmerzen wurden angegeben."

        )

    # --------------------------------------------------------
    # 5. BESCHWERDEDAUER
    # --------------------------------------------------------

    if dauer == DAUER[4]:

        stufe = max(stufe, 1)

        gruende.append(

            "Die Beschwerden bestehen bereits länger als eine Woche."

        )

    # --------------------------------------------------------
    # 6. BLUTVERDÜNNER
    # --------------------------------------------------------

    blutverduenner = [

        "blutverdünner",

        "marcumar",

        "xarelto",

        "eliquis",

        "apixaban",

        "rivaroxaban",

    ]

    blutverduenner_treffer = [

        wort for wort in blutverduenner

        if wort in text

    ]

    sturz_vorhanden = (

        "sturz" in text

        or "gestürzt" in text

        or "hingefallen" in text

    )

    if blutverduenner_treffer and (

        kategorie in VERLETZUNGEN or sturz_vorhanden

    ):

        stufe = max(stufe, 1)

        gruende.append(

            "Blutverdünner in Verbindung mit einer Verletzung "
            "oder einem Sturz erfordern besondere Aufmerksamkeit."

        )

    # --------------------------------------------------------
    # 7. BILDBEFUND
    # --------------------------------------------------------

    if bild_result is not None:

        if bild_result.get("success"):

            gruende.append(

                "Eine technische Bildverarbeitung wurde durchgeführt. "
                "Das Bild liefert keine eigenständige medizinische Diagnose."

            )

        else:

            gruende.append(

                "Die Bildverarbeitung war nicht erfolgreich. "
                "Es ist keine visuelle Beurteilung möglich."

            )

    # --------------------------------------------------------
    # 8. STANDARDREGEL
    # --------------------------------------------------------

    if not gruende:

        gruende.append(

            "Keine der programmierten Warnregeln wurde ausgelöst. "
            "Das bedeutet ausdrücklich keine medizinische Entwarnung."

        )

    # --------------------------------------------------------
    # 9. ERGEBNIS
    # --------------------------------------------------------

    return {

        "stufe": stufe,

        "gruende": gruende,

        "bild": bild_result,

        "hergang": hergang,

        "kategorie": kategorie,

        "schwere": schwere,

        "dauer": dauer,

    }


# ============================================================
# 18. ERGEBNISDARSTELLUNG
# ============================================================

def render_ergebnis(result: dict):

    stufe = result.get("stufe", 0)

    st.markdown("### 🩺 Klinisches Auswertungsergebnis")

    # --------------------------------------------------------
    # NOTFALL
    # --------------------------------------------------------

    if stufe == 2:

        st.error(

            "🚨 MÖGLICHER NOTFALL – HÖCHSTE DRINGLICHKEIT"

        )

        st.markdown(

            """
            Bei akuter Lebensgefahr sofort den Notruf 112 wählen.

            Nicht auf eine weitere Auswertung durch diese Anwendung warten.
            """

        )

        st.link_button(

            "🚨 Notruf 112",

            "tel:112",

            use_container_width=True,

        )

    # --------------------------------------------------------
    # ÄRZTLICHE ABKLÄRUNG
    # --------------------------------------------------------

    elif stufe == 1:

        st.warning(

            "🟡 ÄRZTLICHE ABKLÄRUNG EMPFOHLEN"

        )

        st.markdown(

            """
            Die eingegebenen Angaben enthalten Hinweise,
            die ärztlich beurteilt werden sollten.

            Bei deutlicher Verschlechterung oder neuen
            Warnzeichen unverzüglich medizinische Hilfe suchen.
            """

        )

        st.link_button(

            "📞 Ärztlicher Bereitschaftsdienst 116117",

            "tel:116117",

            use_container_width=True,

        )

    # --------------------------------------------------------
    # KEINE PROGRAMMIERTE WARNREGEL
    # --------------------------------------------------------

    else:

        st.info(

            "ℹ️ Keine programmierten Warnregeln ausgelöst."

        )

        st.markdown(

            """
            Dies ist keine medizinische Entwarnung.

            Eine Erkrankung oder Verletzung kann durch diese
            Anwendung nicht ausgeschlossen werden.
            """

        )

    # --------------------------------------------------------
    # BEGRÜNDUNG
    # --------------------------------------------------------

    st.divider()

    st.markdown("#### 📋 Begründung der Einstufung")

    for grund in result.get("gruende", []):

        st.markdown(f"- {esc(grund)}")

    # --------------------------------------------------------
    # PATIENTENANGABEN
    # --------------------------------------------------------

    st.divider()

    st.markdown("#### 📝 Erfasste Angaben")

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Hauptbeschwerde**")

        st.write(result.get("kategorie", "Keine Angaben"))

        st.write("**Beschwerdedauer**")

        st.write(result.get("dauer", "Keine Angaben"))

    with col2:

        st.write("**Schmerzintensität**")

        st.write(result.get("schwere", "Keine Angaben"))

        st.write("**Hergang**")

        st.write(result.get("hergang") or "Keine Angaben")

    # --------------------------------------------------------
    # BILDANALYSE
    # --------------------------------------------------------

    bild = result.get("bild")

    if bild:

        st.divider()

        st.markdown("#### 📸 Bildverarbeitung")

        st.write(bild.get("text", "Keine Bildbeschreibung vorhanden."))

        source = bild.get("source", "Unbekannt")

        st.caption(

            f"Verarbeitungsquelle: {source}"

        )

        details = bild.get("details", "")

        if details:

            with st.expander("Technische Details anzeigen"):

                st.code(details)

    # --------------------------------------------------------
    # ABSCHLUSSHINWEIS
    # --------------------------------------------------------

    st.divider()

    st.caption(

        "MedicalAssistant Pro ist ein Demonstrationsprototyp. "
        "Die dargestellten Ergebnisse sind keine ärztliche Diagnose "
        "und nicht für klinische Entscheidungen validiert."

    )


# ============================================================
# ENDE TEIL 3
# ============================================================

# ============================================================
# MEDICALASSISTANT PRO
# TEIL 4 VON 4
# STREAMLIT OBERFLÄCHE UND ANWENDUNGSSTART
# ============================================================


# ============================================================
# 19. SESSION STATE INITIALISIEREN
# ============================================================

if "triage_ergebnis" not in st.session_state:

    st.session_state.triage_ergebnis = None


if "api_status" not in st.session_state:

    st.session_state.api_status = "Noch nicht getestet"


if "bild_result" not in st.session_state:

    st.session_state.bild_result = None


# ============================================================
# 20. HEADER
# ============================================================

st.markdown(

    """
    <div class="hero">

        <h1>🩺 MedicalAssistant Pro</h1>

        <p>
        Erweiterte Symptomerfassung,
        technische Bildverarbeitung und
        strukturierte Ersteinschätzung.
        </p>

    </div>
    """,

    unsafe_allow_html=True,

)


# ============================================================
# 21. MEDIZINISCHER HINWEIS
# ============================================================

st.markdown(

    """
    <div class="disclaimer">

        <b>⚠️ Medizinischer Sicherheitshinweis</b><br><br>

        Diese Anwendung ist ein technischer Demonstrationsprototyp.

        Sie ersetzt weder eine ärztliche Untersuchung
        noch eine medizinische Diagnose.

        Bei akuter Lebensgefahr oder schweren Beschwerden
        sofort den Notruf <b>112</b> wählen.

    </div>
    """,

    unsafe_allow_html=True,

)


# ============================================================
# 22. API STATUS
# ============================================================

with st.expander("🔧 Technischer Systemstatus"):

    if HF_TOKEN:

        st.success(
            "Hugging-Face-Token wurde gefunden."
        )

    else:

        st.warning(
            "Kein Hugging-Face-Token konfiguriert. "
            "Der lokale technische Bildfallback steht zur Verfügung."
        )

    st.write(

        f"**Modell:** {HF_MODEL}"

    )

    st.write(

        f"**API-Endpunkt:** {HF_API_URL}"

    )

    st.caption(

        "Die tatsächliche Erreichbarkeit und Modellverfügbarkeit "
        "werden erst bei einer Bildanalyse geprüft."

    )


# ============================================================
# 23. TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(

    [

        "🩺 1. Anamnese",

        "💡 2. Auswertung",

        "🏥 3. Notdienst",

    ]

)


# ============================================================
# 24. TAB 1 – ANAMNESE
# ============================================================

with tab1:

    st.subheader(
        "Beschwerden und Untersuchungsdaten erfassen"
    )

    st.write(

        "Bitte geben Sie die bekannten Informationen ein."

    )

    col1, col2 = st.columns(

        [1, 1],

        gap="large",

    )

    # --------------------------------------------------------
    # HAUPTBESCHWERDE
    # --------------------------------------------------------

    with col1:

        hauptsymptom = st.selectbox(

            "Hauptbeschwerde",

            SYMPTOME,

            key="hauptsymptom",

        )

        dauer = st.selectbox(

            "Dauer der Beschwerden",

            DAUER,

            key="dauer",

        )

        schweregrad = st.selectbox(

            "Schmerzintensität",

            SCHWERE,

            key="schweregrad",

        )

        hergang = st.text_area(

            "Wie ist es passiert?",

            placeholder=(

                "Beispielsweise: Beim Sport umgeknickt, "
                "gestürzt oder gestoßen..."

            ),

            height=130,

            key="hergang",

        )

    # --------------------------------------------------------
    # BILDUPLOAD
    # --------------------------------------------------------

    with col2:

        st.markdown("#### 📸 Bilddokumentation")

        uploaded_file = st.file_uploader(

            "Foto hochladen",

            type=["jpg", "jpeg", "png"],

            max_upload_size=8,

            key="medizinisches_bild",

        )

        if uploaded_file is not None:

            try:

                uploaded_file.seek(0)

                st.image(

                    uploaded_file,

                    caption="Hochgeladenes Bild",

                    use_container_width=True,

                )

                uploaded_file.seek(0)

            except Exception:

                st.error(
                    "Das Bild konnte nicht angezeigt werden."
                )

        analyse_modus = st.selectbox(

            "Bildverarbeitung",

            MODI,

            key="analyse_modus",

        )

    # --------------------------------------------------------
    # ZUSÄTZLICHE ANGABEN
    # --------------------------------------------------------

    notizen = st.text_area(

        "Zusätzliche Beobachtungen",

        placeholder=(

            "Beispielsweise: Blutverdünner, "
            "Vorerkrankungen, Allergien oder weitere Symptome..."

        ),

        height=110,

        key="notizen",

    )

    st.divider()

    # --------------------------------------------------------
    # AUSWERTUNGSBUTTON
    # --------------------------------------------------------

    auswerten = st.button(

        "🚀 Analyse und Auswertung starten",

        type="primary",

        use_container_width=True,

    )

    if auswerten:

        if hauptsymptom == "Bitte wählen...":

            st.error(

                "Bitte zuerst eine Hauptbeschwerde auswählen."

            )

        else:

            try:

                bild_result = None

                bild_bytes = None

                # Foto einlesen

                if uploaded_file is not None:

                    uploaded_file.seek(0)

                    bild_bytes = uploaded_file.getvalue()

                # Bildanalyse nur bei automatischem Modus

                if (

                    bild_bytes is not None

                    and analyse_modus == MODI[0]

                ):

                    with st.spinner(

                        "Bild wird technisch verarbeitet. "
                        "Hugging Face wird angefragt..."

                    ):

                        bild_result = analysiere_bild(
                            bild_bytes
                        )

                    if bild_result.get("error"):

                        st.warning(

                            "API-Status: Hugging Face nicht "
                            "verfügbar. Lokaler Fallback wurde "
                            "verwendet, sofern möglich."

                        )

                    elif bild_result.get("source"):

                        st.success(

                            "Bildverarbeitung abgeschlossen."

                        )

                # Manuelle Dokumentation

                elif (

                    bild_bytes is not None

                    and analyse_modus == MODI[1]

                ):

                    bild_result = {

                        "success": False,

                        "text": (

                            "Bild wurde hochgeladen. "
                            "Keine automatische medizinische "
                            "Beurteilung durchgeführt."

                        ),

                        "details": "",

                        "source": "Manuelle Dokumentation",

                    }

                # Triage-Eingaben

                eingaben = {

                    "kategorie": hauptsymptom,

                    "dauer": dauer,

                    "schwere": schweregrad,

                    "hergang": hergang,

                    "notizen": notizen,

                    "bild_result": bild_result,

                }

                # Triage berechnen

                ergebnis = berechne_triage(
                    eingaben
                )

                # Ergebnis speichern

                st.session_state.triage_ergebnis = ergebnis

                st.session_state.bild_result = bild_result

                st.success(

                    "Auswertung abgeschlossen. "
                    "Bitte den zweiten Tab öffnen."

                )

            except Exception as exc:

                logger.exception(
                    "Fehler bei der Auswertung"
                )

                st.error(

                    "Die Auswertung konnte nicht abgeschlossen werden."

                )

                st.caption(

                    f"Technischer Fehler: {type(exc).__name__}"

                )


# ============================================================
# 25. TAB 2 – AUSWERTUNG
# ============================================================

with tab2:

    st.subheader(
        "Klinische Ersteinschätzung"
    )

    ergebnis = st.session_state.triage_ergebnis

    if ergebnis is None:

        st.info(

            "Bitte zuerst die Anamnese im ersten Tab ausfüllen "
            "und die Auswertung starten."

        )

    else:

        try:

            render_ergebnis(ergebnis)

        except Exception:

            logger.exception(
                "Fehler bei Ergebnisdarstellung"
            )

            st.error(

                "Das Ergebnis konnte nicht dargestellt werden. "
                "Bitte die Auswertung erneut starten."

            )


# ============================================================
# 26. TAB 3 – NOTDIENST
# ============================================================

with tab3:

    st.subheader(

        "🏥 Ärztlicher Bereitschaftsdienst"

    )

    st.write(

        "Geben Sie Ihre deutsche Postleitzahl ein, "
        "um den zuständigen Bereitschaftsdienst zu finden."

    )

    plz = st.text_input(

        "Postleitzahl",

        placeholder="z. B. 23552",

        max_chars=5,

        key="notdienst_plz",

    ).strip()

    if plz:

        if not (

            plz.isdigit()

            and len(plz) == 5

        ):

            st.warning(

                "Bitte eine gültige fünfstellige "
                "deutsche Postleitzahl eingeben."

            )

        else:

            st.markdown(

                f"""
                <div class="card">

                    <h3>📍 Bereitschaftsdienst</h3>

                    <p>
                    Angegebene Postleitzahl:
                    <b>{esc(plz)}</b>
                    </p>

                    <p>
                    Der ärztliche Bereitschaftsdienst
                    hilft außerhalb regulärer Praxiszeiten.
                    </p>

                    <h3>📞 116 117</h3>

                    <p>
                    Über die bundesweite Rufnummer erhalten
                    Sie Informationen zu zuständigen
                    Bereitschaftspraxen und medizinischer Hilfe.
                    </p>

                    <p>
                    Bei lebensbedrohlichen Beschwerden:
                    <b>112</b>.
                    </p>

                </div>
                """,

                unsafe_allow_html=True,

            )

            col_a, col_b = st.columns(2)

            with col_a:

                st.link_button(

                    "📞 116 117 anrufen",

                    "tel:116117",

                    use_container_width=True,

                )

            with col_b:

                st.link_button(

                    "🚨 Notruf 112",

                    "tel:112",

                    use_container_width=True,

                )

            st.link_button(

                "🔎 Bereitschaftspraxis suchen",

                "https://www.116117.de",

                use_container_width=True,

            )

    else:

        st.info(

            "Bitte geben Sie Ihre Postleitzahl ein."

        )


# ============================================================
# 27. FOOTER
# ============================================================

st.divider()

st.markdown(

    """
    <div class="footer">

        <b>MedicalAssistant Pro</b><br>

        Technischer Demonstrationsprototyp<br>

        Keine medizinische Diagnose oder Therapieempfehlung.<br>

        Bei akuten Notfällen: 112

    </div>
    """,

    unsafe_allow_html=True,

)


# ============================================================
# ENDE DER APP
# ============================================================
