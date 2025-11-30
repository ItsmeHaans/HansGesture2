from voice_feature.backend_voice_chat import run_voice_chat

@app.get("/voice/chat")
def api_voice_chat():
    """
    Tidak membutuhkan input apa pun.
    Menjalankan 1 sesi voice chat dan mengembalikan:
    {
        "user": "...",
        "ai": "..."
    }
    """
    try:
        result = run_voice_chat()
        return result
    except Exception as e:
        return {"error": str(e)}
