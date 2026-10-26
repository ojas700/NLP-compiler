import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CACHE_FILE = BASE_DIR / "ai" / "explanation_cache.json"

def get_seed_data():
    return {
        # --- PRESET 1: ADD TWO NUMBERS ---
        "add": {
            "english": (
                "* **Purpose**: This program reads two integer numbers from the user, calculates their sum using arithmetic addition, and displays the result.\n"
                "* **Variables**: `num1` (int) stores the first user input, `num2` (int) stores the second user input, and `sum` (int) stores the computed addition.\n"
                "* **Execution**: First, `printf` prompts for `num1` and `scanf` reads it; next, `num2` is prompted and read; then `sum = num1 + num2` adds the values; finally, `printf` prints `Result: %d`.\n"
                "* **Output**: If the user inputs `10` and `25`, the program prints `Result: 35`."
            ),
            "hindi": (
                "* **उद्देश्य (Purpose)**: यह प्रोग्राम उपयोगकर्ता से दो पूर्णांक संख्याएं (integers) इनपुट लेता है, उनका योग (addition) करता है और परिणाम स्क्रीन पर दिखाता है।\n"
                "* **वेरिएबल्स (Variables)**: `num1` (int) पहले इनपुट के लिए, `num2` (int) दूसरे इनपुट के लिए, और `sum` (int) दोनों के योग को सुरक्षित रखने के लिए।\n"
                "* **निष्पादन (Execution)**: सबसे पहले `printf` और `scanf` से `num1` इनपुट लिया जाता है, फिर `num2` लिया जाता है; इसके बाद `sum = num1 + num2` से गणना होती है, और अंत में `printf` द्वारा `Result: %d` प्रदर्शित होता है।\n"
                "* **परिणाम (Output)**: यदि उपयोगकर्ता `10` और `25` दर्ज करता है, तो आउटपुट `Result: 35` प्राप्त होता है।"
            ),
            "tamil": (
                "* **நோக்கம் (Purpose)**: இந்த நிரல் பயனரிடமிருந்து இரண்டு முழு எண்களை (integers) உள்ளீடாகப் பெற்று, அவற்றைக் கூட்டி (addition), கூட்டுத்தொகையைத் திரையில் காட்டுகிறது.\n"
                "* **மாறிகள் (Variables)**: `num1` (int) முதல் எண், `num2` (int) இரண்டாவது எண், மற்றும் `sum` (int) கூட்டுத்தொகையைச் சேமிக்கப் பயன்படுகிறது.\n"
                "* **செயல்முறை (Execution)**: முதலில் `printf` மற்றும் `scanf` வழியாக `num1` பெறப்படுகிறது, பின்னர் `num2` பெறப்படுகிறது; அடுத்து `sum = num1 + num2` மூலம் கூட்டப்பட்டு, முடிவில் `printf` மூலம் `Result: %d` அச்சிடப்படுகிறது.\n"
                "* **வெளியீடு (Output)**: பயனர் `10` மற்றும் `25` என உள்ளிட்டால், நிரல் `Result: 35` என வெளியிடும்."
            ),
            "telugu": (
                "* **ఉద్దేశం (Purpose)**: ఈ ప్రోగ్రామ్ వినియోగదారు నుండి రెండు పూర్ణాంక సంఖ్యలను (integers) స్వీకరించి, వాటి కూడికను (addition) లెక్కించి ఫలితాన్ని చూపిస్తుంది.\n"
                "* **వేరియబుల్స్ (Variables)**: `num1` (int) మొదటి సంఖ్య, `num2` (int) రెండవ సంఖ్య, మరియు `sum` (int) కూడిక ఫలితాన్ని నిల్వ చేయడానికి.\n"
                "* **అమలు (Execution)**: మొదట `printf` మరియు `scanf` ద్వారా `num1` చదవబడుతుంది, తరువాత `num2` చదవబడుతుంది; ఆపై `sum = num1 + num2` ద్వారా కూడిక జరిగి, చివరగా `printf` ద్వారా `Result: %d` ప్రింట్ అవుతుంది.\n"
                "* **ఫలితం (Output)**: వినియోగదారు `10` మరియు `25` ఇస్తే, ప్రోగ్రామ్ `Result: 35` అని ఫలితాన్ని ఇస్తుంది."
            )
        },

        # --- PRESET 2: EVEN OR ODD ---
        "even_odd": {
            "english": (
                "* **Purpose**: This program checks whether an integer entered by the user is even or odd using the modulo operator `%`.\n"
                "* **Variables**: `num` (int) stores the integer value entered by the user.\n"
                "* **Execution**: `printf` prompts for `num` and `scanf` reads it; then `if (num % 2 == 0)` checks if the remainder when divided by 2 is 0; if true it prints `Result: 1` (even), else it prints `Result: 0` (odd).\n"
                "* **Output**: If the user inputs `8`, the output is `Result: 1`; if `7`, the output is `Result: 0`."
            ),
            "hindi": (
                "* **उद्देश्य (Purpose)**: यह प्रोग्राम जांचता है कि उपयोगकर्ता द्वारा दर्ज की गई संख्या सम (even) है या विषम (odd)। यह मॉड्युलो ऑपरेटर `%` का उपयोग करता है।\n"
                "* **वेरिएबल्स (Variables)**: `num` (int) उपयोगकर्ता द्वारा दी गई संख्या को रखने के लिए।\n"
                "* **निष्पादन (Execution)**: `printf` और `scanf` से संख्या पढ़ी जाती है; फिर `if (num % 2 == 0)` जांचता है कि शेषफल 0 है या नहीं; यदि हां तो `Result: 1` और नहीं तो `Result: 0` प्रिंट होता है।\n"
                "* **परिणाम (Output)**: यदि इनपुट `8` है तो `Result: 1` मिलता है, और यदि `7` है तो `Result: 0` मिलता है।"
            ),
            "tamil": (
                "* **நோக்கம் (Purpose)**: இந்த நிரல் பயனர் உள்ளீடு செய்த எண் இரட்டைப் படையா (even) அல்லது ஒற்றைப் படையா (odd) என்பதை `%` குறியீட்டைக் கொண்டு சரிபார்க்கிறது.\n"
                "* **மாறிகள் (Variables)**: `num` (int) பயனர் உள்ளிட்ட எண்ணைச் சேமிக்கப் பயன்படுகிறது.\n"
                "* **செயல்முறை (Execution)**: `printf` மற்றும் `scanf` மூலம் `num` பெறப்படுகிறது; `if (num % 2 == 0)` மூலம் 2-ஆல் வகுபடும்போது மீதி 0 என சோதிக்கப்பட்டு, இரட்டைப்படை எனில் `Result: 1` எனவும், ஒற்றைப்படை எனில் `Result: 0` எனவும் அச்சிடப்படுகிறது.\n"
                "* **வெளியீடு (Output)**: உள்ளீடு `8` எனில் `Result: 1` என்றும், `7` எனில் `Result: 0` என்றும் வரும்."
            ),
            "telugu": (
                "* **ఉద్దేశం (Purpose)**: వినియోగదారు ఇచ్చిన పూర్ణాంకం సరి సంఖ్య (even) లేదా బేసి సంఖ్య (odd) అని `%` మాడ్యులో ఆపరేటర్ ద్వారా తనిఖీ చేస్తుంది.\n"
                "* **వేరియబుల్స్ (Variables)**: `num` (int) వినియోగదారు నమోదు చేసిన సంఖ్యను నిల్వ చేస్తుంది.\n"
                "* **అమలు (Execution)**: `printf` మరియు `scanf` తో `num` స్వీకరించబడుతుంది; `if (num % 2 == 0)` శేషం 0 అవుతుందో లేదో పరీక్షిస్తుంది; సరి సంఖ్య అయితే `Result: 1`, బేసి సంఖ్య అయితే `Result: 0` ప్రింట్ అవుతుంది.\n"
                "* **ఫలితం (Output)**: ఇన్‌పుట్ `8` అయితే `Result: 1`, అదే `7` అయితే `Result: 0` ప్రింట్ అవుతుంది."
            )
        },

        # --- PRESET 3: LOOP SUM ---
        "loop_sum": {
            "english": (
                "* **Purpose**: This program computes the sum of the first 5 natural numbers (from 1 to 5) iteratively using a `for` loop.\n"
                "* **Variables**: `sum` (int) accumulates the running total (initialized to 0); `i` (int) serves as the loop counter.\n"
                "* **Execution**: The loop `for (i = 1; i <= 5; i++)` runs 5 iterations adding `i` to `sum` on each pass (`1+2+3+4+5`); after the loop terminates, `printf` outputs the final sum.\n"
                "* **Output**: The program automatically displays `Result: 15` without requiring user input."
            ),
            "hindi": (
                "* **उद्देश्य (Purpose)**: यह प्रोग्राम एक `for` लूप का उपयोग करके 1 से 5 तक की प्राकृतिक संख्याओं का कुल योग (sum) ज्ञात करता है।\n"
                "* **वेरिएबल्स (Variables)**: `sum` (int) कुल योग जोड़ने के लिए (प्रारंभ में 0); `i` (int) लूप काउंटर के रूप में 1 से 5 तक बढ़ता है।\n"
                "* **निष्पादन (Execution)**: लूप `for (i = 1; i <= 5; i++)` 5 बार चलता है और हर बार `sum = sum + i` करता है; लूप समाप्त होने के बाद `printf` द्वारा `Result: 15` प्रिंट होता है।\n"
                "* **परिणाम (Output)**: बिना किसी इनपुट के सीधे `Result: 15` प्रिंट होता है।"
            ),
            "tamil": (
                "* **நோக்கம் (Purpose)**: இந்த நிரல் `for` சுழற்சி (loop) மூலம் 1 முதல் 5 வரையிலான எண்களின் கூட்டுத்தொகையைக் கணக்கிடுகிறது.\n"
                "* **மாறிகள் (Variables)**: `sum` (int) மொத்தக் கூட்டலைச் சேமிக்க (தொடக்க மதிப்பு 0); `i` (int) சுழற்சியின் கவுண்டராக (counter) செயல்படுகிறது.\n"
                "* **செயல்முறை (Execution)**: `for (i = 1; i <= 5; i++)` சுழற்சி 5 முறை இயங்கி ஒவ்வொரு முறையும் `sum + i` எனக் கூட்டுகிறது; சுழற்சி முடிந்ததும் `printf` மூலம் இறுதித் தொகை அச்சிடப்படுகிறது.\n"
                "* **வெளியீடு (Output)**: நிரல் நேரடியாக `Result: 15` என வெளியிடும்."
            ),
            "telugu": (
                "* **ఉద్దేశం (Purpose)**: ఈ ప్రోగ్రామ్ `for` లూప్ ఉపయోగించి 1 నుండి 5 వరకు ఉన్న సహజ సంఖ్యల మొత్తాన్ని లెక్కిస్తుంది.\n"
                "* **వేరియబుల్స్ (Variables)**: `sum` (int) మొత్తాన్ని కూడబెట్టడానికి (ప్రారంభంలో 0); `i` (int) లూప్ కౌంటర్‌గా 1 నుండి 5 వరకు తిరుగుతుంది.\n"
                "* **అమలు (Execution)**: `for (i = 1; i <= 5; i++)` లూప్ 5 సార్లు తిరుగుతూ ప్రతిసారీ `sum = sum + i` చేస్తుంది; లూప్ పూర్తయిన తర్వాత `printf` ద్వారా ఫలితం ప్రింట్ అవుతుంది.\n"
                "* **ఫలితం (Output)**: ఎలాంటి ఇన్‌పుట్ అవసరం లేకుండా నేరుగా `Result: 15` అని ప్రదర్శిస్తుంది."
            )
        },

        # --- PRESET 4: TEMPERATURE CONVERSION ---
        "temperature": {
            "english": (
                "* **Purpose**: This program converts a Celsius temperature entered by the user into Fahrenheit using the formula `f = c * 9 / 5 + 32`.\n"
                "* **Variables**: `c` (int) stores the temperature in Celsius; `f` (int) stores the converted temperature in Fahrenheit.\n"
                "* **Execution**: `printf` prompts for `c` and `scanf` reads it; then `f = c * 9 / 5 + 32` applies the conversion arithmetic; finally `printf` displays `Result: %d`.\n"
                "* **Output**: If the user enters `100` for Celsius, the program calculates and prints `Result: 212`."
            ),
            "hindi": (
                "* **उद्देश्य (Purpose)**: यह प्रोग्राम उपयोगकर्ता से सेल्सियस तापमान प्राप्त करके उसे फारेनहाइट में परिवर्तित करता है (`f = c * 9 / 5 + 32`)।\n"
                "* **वेरिएबल्स (Variables)**: `c` (int) सेल्सियस तापमान के लिए; `f` (int) परिवर्तित फारेनहाइट तापमान के लिए।\n"
                "* **निष्पादन (Execution)**: `printf` और `scanf` से `c` पढ़ा जाता है; फिर सूत्र `f = c * 9 / 5 + 32` से गणना की जाती है; अंत में `printf` से `Result: %d` प्रदर्शित होता है।\n"
                "* **परिणाम (Output)**: यदि उपयोगकर्ता `100` दर्ज करता है, तो आउटपुट `Result: 212` प्राप्त होता है।"
            ),
            "tamil": (
                "* **நோக்கம் (Purpose)**: இந்த நிரல் பயனர் அளிக்கும் செல்சியஸ் வெப்பநிலையை பாரன்ஹீட் வெப்பநிலையாக மாற்றுகிறது (`f = c * 9 / 5 + 32`).\n"
                "* **மாறிகள் (Variables)**: `c` (int) செல்சியஸ் வெப்பநிலை; `f` (int) பாரன்ஹீட் வெப்பநிலை.\n"
                "* **செயல்முறை (Execution)**: `printf` மற்றும் `scanf` மூலம் `c` உள்ளீடாகப் பெறப்படுகிறது; பின்னர் `f = c * 9 / 5 + 32` சூத்திரப்படி கணக்கிடப்பட்டு, `printf` மூலம் முடிவு அச்சிடப்படுகிறது.\n"
                "* **வெளியீடு (Output)**: பயனர் `100` என உள்ளிட்டால், வெளியீடு `Result: 212` என வரும்."
            ),
            "telugu": (
                "* **ఉద్దేశం (Purpose)**: వినియోగదారు ఇచ్చిన సెల్సియస్ ఉష్ణోగ్రతను ఫారెన్‌హీట్‌గా మారుస్తుంది (`f = c * 9 / 5 + 32`).\n"
                "* **వేరియబుల్స్ (Variables)**: `c` (int) సెల్సియస్ ఉష్ణోగ్రత కోసం; `f` (int) మార్చబడిన ఫారెన్‌హీట్ ఉష్ణోగ్రత కోసం.\n"
                "* **అమలు (Execution)**: `printf` మరియు `scanf` తో `c` చదవబడుతుంది; తరువాత `f = c * 9 / 5 + 32` సూత్రం ద్వారా లెక్కించబడుతుంది; చివరగా `printf` తో ఫలితం ప్రదర్శించబడుతుంది.\n"
                "* **ఫలితం (Output)**: వినియోగదారు `100` ఇస్తే, ప్రోగ్రామ్ `Result: 212` అని ఫలితాన్ని ఇస్తుంది."
            )
        }
    }

print("Seed data prepared.")
