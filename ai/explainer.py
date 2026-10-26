import requests
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = BASE_DIR / "ai" / "explanation_cache.json"

# In-memory and persistent cache for code explanations
_EXPLANATION_CACHE = {}

def _load_cache():
    global _EXPLANATION_CACHE
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _EXPLANATION_CACHE = json.load(f)
        except Exception as e:
            print(f"[Explainer] Warning: Failed to load cache file: {e}")
            _EXPLANATION_CACHE = {}

def _save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_EXPLANATION_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Explainer] Warning: Failed to save cache file: {e}")

# Initial load
_load_cache()

def normalize_c_code(code: str) -> str:
    """Strips comments and collapses whitespace so minor formatting changes hit cache."""
    cleaned = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    cleaned = re.sub(r'//.*', '', cleaned)
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    return "\n".join(lines)

EXPLAIN_PROMPT_TEMPLATES = {
    "english": (
        "You are an expert Computer Science teacher.\n"
        "Explain the following C program in beginner-friendly, clear English.\n"
        "Provide a concise, direct explanation with 4 short bullet points:\n"
        "- Purpose: What problem does this program solve?\n"
        "- Variables: List variable names, types (like int), and purpose.\n"
        "- Execution: Briefly explain scanf/read, calculations, if/loop, and printf in order.\n"
        "- Output: Mention sample output based on user input.\n"
        "Keep technical identifiers (printf, scanf, int, variable names) exact. Be concise and direct."
    ),
    "hindi": (
        "आप एक कंप्यूटर साइंस शिक्षक हैं।\n"
        "नीचे दिए गए C प्रोग्राम को शुरुआती छात्रों के लिए सरल हिंदी में संक्षेप में समझाएं।\n"
        "संक्षिप्त रूप में 4 बिंदुओं में व्याख्या करें:\n"
        "- उद्देश्य (Purpose): प्रोग्राम क्या कार्य करता है?\n"
        "- वेरिएबल्स (Variables): int, वेरिएबल नाम और उनका उपयोग।\n"
        "- निष्पादन (Execution): scanf, गणना, printf की क्रमबद्ध व्याख्या।\n"
        "- परिणाम (Output): इनपुट पर आधारित संभावित आउटपुट।\n"
        "तकनीकी शब्दों (printf, scanf, int) को अंग्रेजी में ही रखें। उत्तर संक्षिप्त और स्पष्ट रखें।"
    ),
    "tamil": (
        "நீங்கள் ஒரு கணினி அறிவியல் ஆசிரியர்.\n"
        "கீழே கொடுக்கப்பட்டுள்ள C நிரலை ஆரம்பநிலை மாணவர்களுக்கு எளிய தமிழில் சுருக்கமாக விளக்குங்கள்.\n"
        "4 சுருக்கமான புள்ளிகளில் விளக்குக:\n"
        "- நோக்கம் (Purpose): நிரல் என்ன செய்கிறது?\n"
        "- மாறிகள் (Variables): int, மாறிகளின் பெயர்கள்.\n"
        "- செயல்முறை (Execution): scanf, கணக்கீடு, printf வரிசை.\n"
        "- வெளியீடு (Output): உள்ளீட்டின் அடிப்படையிலான முடிவு.\n"
        "தொழில்நுட்ப பெயர்களை (printf, scanf, int) அப்படியே குறிப்பிடவும். சுருக்கமாக எழுதவும்."
    ),
    "telugu": (
        "మీరు కంప్యూటర్ సైన్స్ అధ్యాపకులు.\n"
        "క్రింది C ప్రోగ్రామ్‌ను ప్రారంభ విద్యార్థులకు సులభమైన తెలుగులో సంక్షిప్తంగా వివరించండి.\n"
        "4 సంక్షిప్త పాయింట్లలో వివరించండి:\n"
        "- ఉద్దేశం (Purpose): ప్రోగ్రామ్ ఏమి చేస్తుంది?\n"
        "- వేరియబుల్స్ (Variables): int, వేరియబుల్ పేర్లు.\n"
        "- అమలు (Execution): scanf, లెక్కలు, printf క్రమం.\n"
        "- ఫలితం (Output): ఇన్‌పుట్ ఆధారంగా ఫలితం.\n"
        "సాంకేతిక పదాలను (printf, scanf, int) ఆంగ్లంలోనే ఉంచండి. సంక్షిప్తంగా మరియు స్పష్టంగా రాయండి."
    )
}

_SESSION = requests.Session()

def explain_c_code(c_code: str, language: str = "english", ollama_url: str = "http://127.0.0.1:11434"):
    """
    Explains the provided generated C code in the specified language (English, Hindi, Tamil, Telugu).
    Uses persistent cache + Ollama qwen2.5:3b with graceful fallback.
    Returns (success: bool, explanation: str, error: str).
    """
    code_stripped = c_code.strip()
    if not code_stripped:
        return False, "", "No C code provided to explain. Please compile a program first."

    lang_key = language.strip().lower()
    if lang_key not in EXPLAIN_PROMPT_TEMPLATES:
        lang_key = "english"

    # 1. Check exact raw match in cache
    raw_key = f"{lang_key}:::{code_stripped}"
    if raw_key in _EXPLANATION_CACHE:
        return True, _EXPLANATION_CACHE[raw_key], None

    # 2. Check normalized C code match in cache
    norm_code = normalize_c_code(code_stripped)
    norm_key = f"{lang_key}:::{norm_code}"
    if norm_key in _EXPLANATION_CACHE:
        return True, _EXPLANATION_CACHE[norm_key], None

    # 3. Call local Ollama Qwen 2.5 3B
    sys_instruction = EXPLAIN_PROMPT_TEMPLATES.get(lang_key, EXPLAIN_PROMPT_TEMPLATES["english"])

    payload = {
        "model": "qwen2.5:3b",
        "stream": False,
        "keep_alive": -1,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 160
        },
        "messages": [
            {"role": "system", "content": sys_instruction},
            {"role": "user", "content": f"Explain this C code:\n\n```c\n{code_stripped}\n```"}
        ]
    }

    try:
        res = _SESSION.post(f"{ollama_url}/api/chat", json=payload, timeout=120)
        if res.status_code != 200:
            return False, "", f"Ollama HTTP error {res.status_code}: {res.text}"

        explanation = res.json().get("message", {}).get("content", "").strip()
        if not explanation:
            return False, "", "Empty explanation received from model."

        # Cache both raw and normalized keys
        _EXPLANATION_CACHE[raw_key] = explanation
        _EXPLANATION_CACHE[norm_key] = explanation
        _save_cache()

        return True, explanation, None

    except requests.exceptions.ConnectionError:
        return False, "", "Could not connect to Ollama. Make sure 'ollama serve' is running."
    except Exception as e:
        return False, "", f"Explanation generation error: {str(e)}"
