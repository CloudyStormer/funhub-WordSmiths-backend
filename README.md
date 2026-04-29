# WordSmiths AI Backend

Minimal Python backend for AI features:

- English learning chat
- Daily learning plan generation

## 1) Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

## 3) Configure environment

```bash
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

## 4) Run API

```bash
uvicorn app.main:app --reload --port 8000
```

## 5) Test endpoints

- Health: `GET /health`
- Chat: `POST /ai/chat`
- Daily plan: `POST /ai/daily-plan`

Open docs at: `http://127.0.0.1:8000/docs`
