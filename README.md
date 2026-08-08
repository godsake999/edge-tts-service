# Edge TTS Service

Free text-to-speech API using Microsoft Edge TTS voices.
Supports Burmese (Myanmar) and many other languages.

## Endpoints

### GET /healthz
Health check. Returns available voices.

### GET /voices
List all available voices.

### POST /tts
Single text to speech.

Request:
{
  "text": "မင်္ဂလာပါ",
  "voice": "my-MM-NilarNeural",
  "rate": "+0%",
  "volume": "+0%",
  "pitch": "+0Hz",
  "format": "base64"
}

Response:
{
  "audio_base64": "...",
  "size_kb": 12.3,
  "voice": "my-MM-NilarNeural",
  "format": "mp3"
}

### POST /tts/batch
Multiple texts at once (max 20 items).

Request:
{
  "items": [
    {"text": "မင်္ဂလာပါ", "voice": "my-MM-NilarNeural"},
    {"text": "ကျေးဇူးတင်ပါတယ်", "voice": "my-MM-NilarNeural"}
  ]
}

## Burmese Voices
- my-MM-NilarNeural (Female)
- my-MM-ThihaNeural (Male)
