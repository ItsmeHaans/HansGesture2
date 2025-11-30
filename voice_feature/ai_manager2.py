# ai_manager2.py
import google.generativeai as genai
import threading

class AIManager2:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=
                "You are a voice chatbot talking with Mr. Hans. "
                "Always answer using very short natural sentences. "
                "Never repeat the user's words. "
                "No formatting, no explanation."
        )

    def build_prompt(self, text):
        txt = text.lower().strip()
        if txt.startswith("open") or txt.startswith("buka"):
            return ("_LOCAL_APP_", txt)
        return text

    def _ask(self, text, callback):
        try:
            prompt = self.build_prompt(text)

            # local app mode
            if isinstance(prompt, tuple):
                callback("local_app", prompt[1])
                return

            # AI output
            res = self.model.generate_content(prompt)
            reply = res.text.strip()

            callback("chat", reply)

        except Exception as e:
            callback("chat", f"AI error: {e}")

    def ask(self, text, callback):
        thread = threading.Thread(
            target=self._ask, args=(text, callback), daemon=True
        )
        thread.start()
