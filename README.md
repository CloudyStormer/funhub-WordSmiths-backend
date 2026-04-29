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
- `LLM_PROVIDER=openai_compatible` or `LLM_PROVIDER=hunyuan` for compatible providers
- `LLM_API_KEY` is required in real mode
- `LLM_BASE_URL` is optional for OpenAI, usually required for compatible providers

Example (Hunyuan/OpenAI-compatible):

```env
LANGCHAIN_ENABLED=true
LLM_PROVIDER=hunyuan
LLM_API_KEY=your_key
LLM_MODEL=your_model_name
LLM_BASE_URL=your_provider_compatible_base_url
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

Open docs at: `http://127.0.0.1:8000/docs`
