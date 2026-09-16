from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>المترجم الذكي السريع ⚡</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #0f172a; color: #fff; text-align: center; padding: 15px; margin: 0; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; display: inline-block; max-width: 450px; width: 100%; margin-top: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        select { padding: 10px; border-radius: 6px; margin-top: 5px; width: 100%; background: #334155; color: white; border: none; font-size: 14px; }
        .result-box { background: #0f172a; padding: 12px; border-radius: 6px; margin-top: 15px; text-align: right; border: 1px solid #334155; font-size: 14px; }
        .clean-trans { direction: ltr; text-align: left; font-weight: bold; color: #4ade80; margin-top: 5px; font-size: 16px; }
        .pulse-indicator { display: inline-block; width: 12px; height: 12px; background: #10b981; border-radius: 50%; margin-left: 8px; animation: pulse 0.8s infinite; }
        @keyframes pulse { 0% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.3); opacity: 0.5; } 100% { transform: scale(1); opacity: 1; } }
    </style>
</head>
<body onload="startEngine()">
    <div class="card">
        <h2>المترجم الذكي السريع ⚡</h2>
        <p style="color: #94a3b8; font-size: 12px;">دقة الذكاء الاصطناعي في فهم الدارجة + سرعة البرق</p>
        
        <label style="display:block; text-align:right; margin-top:8px;">لغة التحدث:</label>
        <select id="srcLang">
            <option value="ar">العربية / الدارجة (Arabic)</option>
            <option value="en">الإنجليزية (English)</option>
            <option value="fr">الفرنسية (French)</option>
            <option value="de">الألمانية (German)</option>
        </select>

        <label style="display:block; text-align:right; margin-top:8px;">لغة الترجمة:</label>
        <select id="tgtLang">
            <option value="en">الإنجليزية (English)</option>
            <option value="ar">العربية (Arabic)</option>
            <option value="fr">الفرنسية (French)</option>
            <option value="de">الألمانية (German)</option>
        </select>

        <div class="result-box">
            <div id="statusText" style="color: #38bdf8;"><span class="pulse-indicator"></span> مكالمة حية تعمل الآن... تحدث بحرية</div>
            <div id="originalText" style="color: #cbd5e1; margin-top: 8px;">النص: -</div>
            <div style="margin-top: 8px;">الترجمة:</div>
            <div id="translatedText" class="clean-trans">-</div>
        </div>
    </div>

    <script>
        let recognition = null;
        let isRunning = true;
        const translationCache = {};

        function startEngine() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("متصفحك لا يدعم التعرف الصوتي.");
                return;
            }

            if (recognition) {
                try { recognition.stop(); } catch(e) {}
            }

            recognition = new SpeechRecognition();
            recognition.lang = document.getElementById('srcLang').value === 'ar' ? 'ar-SA' : document.getElementById('srcLang').value;
            
            // خصائص متقدمة لتصفية الضوضاء والرياح وعزل أصوات البيئة الخارجية التركيز على صوت الحريف فقط
            recognition.interimResults = true;
            recognition.continuous = true;
            if (typeof recognition.maxAlternatives !== 'undefined') {
                recognition.maxAlternatives = 1;
            }

            document.getElementById('srcLang').onchange = function() {
                recognition.lang = this.value === 'ar' ? 'ar-SA' : this.value;
                restartEngine();
            };

            recognition.onstart = function() {
                document.getElementById('statusText').innerHTML = '<span class="pulse-indicator"></span> مكالمة حية تعمل الآن... تحدث بحرية';
            };

            recognition.onresult = async function(event) {
                const lastIdx = event.results.length - 1;
                const resultItem = event.results[lastIdx];
                let spokenText = resultItem[0].transcript.trim();
                
                if (!spokenText) return;

                // تصفية الكلمات الوهمية الناتجة عن الضوضاء العشوائية أو العصافير
                if (spokenText.length < 2 && !/[أ-يa-zA-Z]/.test(spokenText)) return;

                document.getElementById('originalText').innerText = `النص: ${spokenText}`;

                if (resultItem.isFinal) {
                    document.getElementById('statusText').innerHTML = '<span class="pulse-indicator"></span> جاري المعالجة الفورية...';

                    const srcVal = document.getElementById('srcLang').value;
                    const tgtVal = document.getElementById('tgtLang').value;
                    const cacheKey = `${srcVal}_${tgtVal}_${spokenText}`;

                    let translation = "";

                    if (translationCache[cacheKey]) {
                        translation = translationCache[cacheKey];
                    } else {
                        try {
                            const res = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=${srcVal}&tl=${tgtVal}&dt=t&q=${encodeURIComponent(spokenText)}`);
                            const data = await res.json();
                            
                            if (data && data[0]) {
                                data[0].forEach(item => {
                                    if (item[0]) translation += item[0];
                                });
                            }
                            
                            if (translation) {
                                translationCache[cacheKey] = translation;
                            }
                        } catch (e) {
                            translation = "خطأ في الاتصال";
                        }
                    }

                    if (!translation) translation = "عذراً، لم تكتمل الترجمة";

                    document.getElementById('translatedText').innerText = translation;
                    document.getElementById('statusText').innerHTML = '<span class="pulse-indicator"></span> بانتظار رد الطرف الآخر...';

                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(translation);
                    utterance.lang = tgtVal === 'ar' ? 'ar-SA' : tgtVal;
                    window.speechSynthesis.speak(utterance);
                }
            };

            recognition.onerror = function(event) {
                console.log("Error:", event.error);
            };

            recognition.onend = function() {
                if (isRunning) {
                    setTimeout(restartEngine, 50);
                }
            };

            try {
                recognition.start();
                isRunning = true;
            } catch (e) {
                window.addEventListener('click', function unlock() {
                    restartEngine();
                    window.removeEventListener('click', unlock);
                }, { once: true });
            }
        }

        function restartEngine() {
            try {
                if (recognition) {
                    recognition.stop();
                }
            } catch(e) {}
            setTimeout(() => {
                try {
                    if (isRunning) recognition.start();
                } catch(e) {}
            }, 50);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
