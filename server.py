from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
import edge_tts
import asyncio
import base64
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Available Burmese and useful voices
VOICES = {
    "burmese_female": "my-MM-NilarNeural",
    "burmese_male": "my-MM-ThihaNeural",
    "english_female": "en-US-JennyNeural",
    "english_male": "en-US-GuyNeural",
}


@app.get("/healthz")
def health():
    return {
        "status": "ok",
        "service": "Edge TTS API",
        "available_voices": VOICES
    }


@app.get("/voices")
async def list_voices():
    try:
        voices = await edge_tts.list_voices()
        return {"voices": voices}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/tts")
async def text_to_speech(data: dict):
    text = data.get("text", "").strip()
    voice = data.get("voice", "my-MM-NilarNeural")
    rate = data.get("rate", "+0%")
    volume = data.get("volume", "+0%")
    pitch = data.get("pitch", "+0Hz")
    return_format = data.get("format", "base64")

    # Validate
    if not text:
        return JSONResponse(
            status_code=400,
            content={"error": "text is required"}
        )

    if len(text) > 3000:
        return JSONResponse(
            status_code=400,
            content={"error": "text too long, max 3000 characters"}
        )

    logger.info(f"TTS request: voice={voice}, length={len(text)}")

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )

        audio_bytes = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.write(chunk["data"])

        audio_bytes.seek(0)
        audio_data = audio_bytes.read()

        if not audio_data:
            return JSONResponse(
                status_code=500,
                content={"error": "No audio generated"}
            )

        logger.info(
            f"TTS done: {len(audio_data) / 1024:.1f} KB"
        )

        # Return as base64 JSON (easier for n8n)
        if return_format == "base64":
            audio_base64 = base64.b64encode(audio_data).decode()
            return {
                "audio_base64": audio_base64,
                "size_kb": round(len(audio_data) / 1024, 1),
                "voice": voice,
                "format": "mp3"
            }

        # Return as raw audio file
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )

    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/tts/batch")
async def batch_tts(data: dict):
    """
    Generate multiple TTS at once for all scenes
    Input: { "items": [ {text, voice, rate}, ... ] }
    Output: { "results": [ {audio_base64, size_kb}, ... ] }
    """
    items = data.get("items", [])

    if not items:
        return JSONResponse(
            status_code=400,
            content={"error": "items array is required"}
        )

    if len(items) > 20:
        return JSONResponse(
            status_code=400,
            content={"error": "max 20 items per batch"}
        )

    logger.info(f"Batch TTS: {len(items)} items")

    results = []
    for i, item in enumerate(items):
        text = item.get("text", "").strip()
        voice = item.get("voice", "my-MM-NilarNeural")
        rate = item.get("rate", "+0%")

        if not text:
            results.append({
                "index": i,
                "error": "empty text",
                "audio_base64": ""
            })
            continue

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate
            )

            audio_bytes = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.write(chunk["data"])

            audio_bytes.seek(0)
            audio_data = audio_bytes.read()
            audio_base64 = base64.b64encode(audio_data).decode()

            results.append({
                "index": i,
                "audio_base64": audio_base64,
                "size_kb": round(len(audio_data) / 1024, 1),
                "voice": voice
            })

            logger.info(f"Batch item {i}: done")

        except Exception as e:
            logger.error(f"Batch item {i} error: {str(e)}")
            results.append({
                "index": i,
                "error": str(e),
                "audio_base64": ""
            })

    return {"results": results}
