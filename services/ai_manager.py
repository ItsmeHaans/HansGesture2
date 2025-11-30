import google.generativeai as genai
import threading

class AIManager:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    # =====================================================
    # SMART PROMPT BUILDER
    # =====================================================
    def build_prompt(self, text):
        txt = text.lower().strip()

        # 100% LOCAL OPEN / BUKA → BYPASS AI
        if txt.startswith("open") or txt.startswith("buka"):
            return ("_LOCAL_APP_", text)

        # Otherwise → normal Gemini task
        return f"""
Your job is to convert voice commands into:

1. TYPE: link → used when the user requests an online service such as search, video, direct video playback, image, music, maps, etc. This type can open a webpage, trigger a search query, or directly open a specific video URL for immediate playback.
2. TYPE: chat → normal chatbot answer in english

NEVER explain.
NEVER add extra words.

OUTPUT FORMAT (must follow EXACTLY):
TYPE: <link/chat>
RESULT: <url or text>

Examples:
User: play video ferrari
TYPE: link
RESULT: https://www.youtube.com/results?search_query=ferrari

User: search image f8 spider
TYPE: link
RESULT: https://www.google.com/search?tbm=isch&q=f8+spider

User: what is machine learning
TYPE: chat
RESULT: Machine learning is...

Now convert:

"{text}"
"""

    # =====================================================
    # PRIVATE ASK
    # =====================================================
    def _ask(self, text, callback=None):
        try:
            prompt = self.build_prompt(text)

            # BYPASS: local open
            if isinstance(prompt, tuple) and prompt[0] == "_LOCAL_APP_":
                if callback:
                    callback("local_app", prompt[1])
                return

            # NORMAL GEMINI CALL
            response = self.model.generate_content(prompt)
            raw = response.text or ""
            lines = raw.split("\n")

            result_type = ""
            result_value = ""

            for line in lines:
                l = line.lower().strip()
                if l.startswith("type:"):
                    result_type = line.split(":", 1)[1].strip()
                if l.startswith("result:"):
                    result_value = line.split(":", 1)[1].strip()

            if callback:
                callback(result_type, result_value)

        except Exception as e:
            if callback:
                callback("chat", f"AI error: {e}")

    # =====================================================
    # PUBLIC CALL
    # =====================================================
    def ask(self, text, callback=None):
        thread = threading.Thread(target=self._ask, args=(text, callback), daemon=True)
        thread.start()
