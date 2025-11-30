from voice_feature.backend_voice_timer import run_voice_timer

@app.get("/voice/timer")
def api_voice_timer():
    """
    Memulai voice timer 1 sesi.
    Mengembalikan:
    {
        "seconds": 0,
        "spoken_text": "ten"
    }
    """
    try:
        result = run_voice_timer()
        return result
    except Exception as e:
        return {"error": str(e)}
