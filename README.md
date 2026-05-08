# WordSmiths AI Backend

Minimal Python backend for AI features:

- English learning chat
- Daily learning plan generation

## 1) Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

## 3) Configure environment

```bash
cp .env.example .env
# then edit .env
```

Basic .env options:

- `LANGCHAIN_ENABLED=true` to use LangChain call path
- `LLM_PROVIDER=mock` means local mock mode (no external model call)
- `LLM_PROVIDER=openai` for OpenAI official endpoint
- `LLM_PROVIDER=openai_compatible` or `LLM_PROVIDER=hunyuan` or `LLM_PROVIDER=deepseek` for compatible providers
- `LLM_API_KEY` is required in real mode
- `LLM_BASE_URL` is optional for OpenAI, usually required for compatible providers
- `HUNYUAN_API_KEY` / `HUNYUAN_MODEL` / `HUNYUAN_BASE_URL` are optional provider-specific overrides when `LLM_PROVIDER=hunyuan`
- `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL` are optional provider-specific overrides when `LLM_PROVIDER=deepseek`
- `TOPIC_CHAT_STORE_PATH` controls where session history is persisted (default: `app/data/topic_chat_sessions.json`)
- `TOPIC_CHAT_MAX_HISTORY_MESSAGES` controls max saved messages per session (default: `100`)

Example (Hunyuan/OpenAI-compatible):

```env
LANGCHAIN_ENABLED=true
LLM_PROVIDER=hunyuan
LLM_API_KEY=your_key
LLM_MODEL=your_model_name
LLM_BASE_URL=your_provider_compatible_base_url
```

Example (DeepSeek):

```env
LANGCHAIN_ENABLED=false
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

When `LANGCHAIN_ENABLED=false`, backend uses OpenAI Python SDK directly.

Recommended for domestic model + LangChain:

```env
LANGCHAIN_ENABLED=true
LLM_PROVIDER=hunyuan
LLM_API_KEY=your_key
LLM_MODEL=your_model_name
LLM_BASE_URL=your_provider_compatible_base_url
```

How to verify you are really on LangChain path:

1. call `GET /ai/status`
2. ensure `engine` is `langchain`
3. ensure `mode` is `real`

If `engine` is `langchain-unavailable`, install dependencies again:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 4) Run API

```bash
uvicorn app.main:app --reload --port 8000
```

## 5) Test endpoints

- Health: `GET /health`
- Runtime status: `GET /ai/status`
- Chat: `POST /ai/chat`
- Daily plan: `POST /ai/daily-plan`
- Topic agent chat (session-based): `POST /ai/topic-agent-chat`
- Topic agent history by session: `GET /ai/topic-agent-chat/history/{session_id}?user_id=...`

### Topic agent multi-turn usage

1. Start a new session by calling `POST /ai/topic-agent-chat` with empty `session_id` and providing `type` + `words`.
2. Save the returned `session_id` on the client side.
3. Continue conversation by sending the same `session_id` (you can omit `type` and `words` in later turns).
4. Re-open history anytime with `GET /ai/topic-agent-chat/history/{session_id}?user_id=...`.

Because session data is persisted to a JSON file, conversations survive process restarts.

Open docs at: `http://127.0.0.1:8000/docs`
