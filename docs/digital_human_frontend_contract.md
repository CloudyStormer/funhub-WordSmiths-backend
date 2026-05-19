# Digital Human MVP Contract

This module is intentionally isolated from existing AI/TTS endpoints.

## Recommended MVP Flow

1. React records microphone input while the user holds the button.
2. Browser ASR turns speech into text. For CRA, start with `window.SpeechRecognition` / `window.webkitSpeechRecognition` where available.
3. Frontend calls `POST /digital-human/chat` with the recognized text.
4. Backend asks the configured LLM for a reply.
5. Backend uses XFYUN TTS to synthesize reply audio.
6. Backend gives the audio URL to the configured avatar provider.
7. Frontend plays `avatar.video_url` when present; otherwise play `audio_url`.

## POST /digital-human/chat

Request:

```json
{
  "user_id": "user-001",
  "message": "I want to practice restaurant English.",
  "level": "A2",
  "avatar_id": "",
  "voice": "x4_yezi"
}
```

Response:

```json
{
  "job_id": "generated-job-id",
  "user_id": "user-001",
  "user_text": "I want to practice restaurant English.",
  "reply_text": "Great. Let's practice ordering food...",
  "audio_url": "http://127.0.0.1:8000/digital-human/media/generated-job-id.mp3",
  "avatar": {
    "provider": "mock",
    "avatar_id": "default",
    "status": "mock_ready",
    "video_url": "",
    "stream_url": "",
    "message": "Mock digital human response..."
  }
}
```

## GET /digital-human/status

Use this to show integration readiness in development.

## GET /digital-human/jobs/{job_id}

Use this for provider polling once a real avatar provider returns asynchronous jobs.

## React Hooks Shape

```tsx
const [isRecording, setIsRecording] = useState(false);
const [transcript, setTranscript] = useState("");
const [reply, setReply] = useState("");
const [audioUrl, setAudioUrl] = useState("");
const [videoUrl, setVideoUrl] = useState("");

async function sendMessage(text: string) {
  const res = await fetch("http://127.0.0.1:8000/digital-human/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "local-user",
      message: text,
      level: "A2",
    }),
  });
  const data = await res.json();
  setReply(data.reply_text);
  setAudioUrl(data.audio_url);
  setVideoUrl(data.avatar.video_url);
}
```

## About User Likeness

The backend cannot infer a user's appearance by itself. A real digital human provider needs one of these:

- A provider-created avatar id from uploaded portrait/video material.
- A photo avatar pipeline that accepts clear frontal photos.
- A custom clone pipeline that usually needs several photos or a short consented video.

For this backend, store the resulting provider avatar id in `TENCENT_DIGITAL_HUMAN_AVATAR_ID` or pass `avatar_id` per request.
