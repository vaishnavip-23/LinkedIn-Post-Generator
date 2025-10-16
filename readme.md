## LinkedIn Post Generator

An AI-powered app that turns topics, YouTube videos, and PDFs into engaging LinkedIn posts. Includes a React UI and an alternative Streamlit UI.

### Features

- **Web research**: Uses Tavily + Exa to gather fresh info
- **YouTube to post**: Get transcripts from videos (≤15 min) and convert into a post
- **PDF to post**: Upload up to 3MB; automatic direct/RAG handling
- **Refinements**: Ask to shorten, change tone, add/remove emojis, etc.
- **LinkedIn posting**: OAuth + post from the app

### Tech Stack

- **Backend**: FastAPI, OpenAI (GPT-4o-mini, Whisper), ChromaDB, Instructor, Pydantic, Logfire (dev)
- **Tools**: Tavily, Exa, youtube-transcript-api (transcripts), YouTube oEmbed (metadata), PDF parsing (pypdf), tokenization (tiktoken)
- **Frontend (primary)**: React + TypeScript, Vite, Tailwind, shadcn/ui
- **Frontend (alt)**: Streamlit app for quick local usage

### Project Structure

```
.
├── backend/
│   ├── main.py                # FastAPI app + endpoints
│   ├── prompts.py             # System prompts and grounding rules
│   ├── models/schema.py       # Pydantic models
│   └── tools/                 # web_search, youtube_transcribe, file_search (RAG)
├── frontend-react/            # React app
├── frontend-streamlit/        # Streamlit UI
├── pyproject.toml             # Python dependencies (uv/poetry-style)
├── render.yaml                # Render (backend) blueprint
└── README.md                  
```

### Prerequisites

- Python 3.10+
- Node.js 20+
- API keys: OpenAI, Tavily, Exa, LinkedIn Client Id and Key
- **Note**: No FFmpeg or audio tools needed - YouTube transcripts are fetched directly 

### Environment Variables

Follow the `.env.example` file in the repo.

- Copy it to create your local `.env` and replace the placeholder values with secret keys


### Installation

1. Backend dependencies

```
uv sync
```

2. Frontend dependencies

```
cd frontend-react
npm install
cd ..
```

### Running Locally

- Backend (FastAPI)

```
uv run uvicorn backend.main:app --reload
```

- API: `http://localhost:8000`
- Frontend (React)

```
cd frontend-react
npm run dev
```

- App: `http://localhost:5173`

- Alternative UI (Streamlit)

```
cd frontend-streamlit
streamlit run streamlit_ui.py
```

### How To Use

- **Web search**: Enter a topic like "AI trends in healthcare" and send.
- **YouTube**: Paste a YouTube URL (≤15 minutes). The app fetches the transcript and generates a post. (Note: Only works with videos that have captions/transcripts - most do!)
- **PDF**: Click upload, add a PDF (≤3MB), then ask questions like "[file_id: ...] cloud cost optimization" via the UI (the React/Streamlit client adds the `[file_id: ...]` automatically once uploaded).
- **Refine**: Ask “make it more formal,” “shorten to 200 words,” “remove emojis,” etc.

### How It Works (High-level)

1. Client sends a query. If a PDF was uploaded, the client prefixes the message with `[file_id: ...]`.
2. The backend agent decides which tool to use:
   - `[file_id: ...]` → document search (direct text or RAG via ChromaDB)
   - YouTube URL → fetch transcript using youtube-transcript-api
   - Otherwise → web search (Tavily + Exa)
3. The research result is formatted and passed to an LLM (via Instructor) to produce a structured LinkedIn post `{ content, hashtags }`.
4. The client displays the post and allows refinements or posting to LinkedIn.

### Notes and Limits

- YouTube length limit: 15 minutes
- YouTube transcript requirement: Videos must have captions/transcripts enabled (auto-generated or manual)
- PDF size limit: 3MB; large docs switch to RAG automatically
- Hashtags are returned separately; the UI combines them for display

### Enhancements for future

- Increase the YouTube video limit and PDF size
- Support multiple document types for RAG (e.g., DOCX, TXT)
- Retrieve and fuse more sources via web search


### Final Thoughts and Thank you note
I would like to thank the ProspelloAI team for an engaging and thoughtfully designed hackathon challenge. Over the course of 48 hours, I built and deployed an end-to-end product that showcases practical use of the OpenAI SDK, integrated web search via Tavily and Exa, and a deliberate design choice for document handling—selecting between RAG and direct LLM generation through a smart PDF pipeline. The system produces structured outputs using Instructor and Pydantic, features a clean, modern UI, and supports real-world workflows, including posting directly to LinkedIn. Beyond the technical depth, the application serves as a creative partner—helping users brainstorm and post with one click.
I truly enjoyed working on this, hope it helps your team to gauge may technical competence. Look forward to your review and inputs.  Thank you.