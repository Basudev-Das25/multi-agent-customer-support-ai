# Multi-Agent Customer Support AI

An AI-powered customer support platform that uses specialized agents to handle different types of customer queries — billing, technical support, product questions, complaints, and general FAQs — with retrieval-augmented generation (RAG) from a knowledge base.

## Features

- **Multi-Agent Architecture** — 5 specialized AI agents (Billing, Technical, Product, Complaint, FAQ) with automatic intent classification
- **RAG Pipeline** — Semantic search over ingested documents using FAISS + sentence-transformer embeddings
- **Dataset Ingestion** — Pre-built loaders for FAQ, Banking77, SQuAD, DailyDialog, and CFPB Complaints datasets with idempotent ingestion
- **Source Attribution** — Every AI response includes which agent answered and which knowledge base documents were used
- **PDF Upload** — Admins can upload PDF documents directly to the knowledge base
- **Real-time Chat** — WebSocket-style chat interface with conversation history
- **JWT Authentication** — Secure user registration, login, and role-based access (user/admin)
- **Modern UI** — Indigo-violet dark theme with glass-morphism, fluid animations, and responsive design

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI, Python 3.13, Pydantic v2 |
| Database | MongoDB Atlas |
| Vector Store | FAISS (Facebook AI Similarity Search) |
| Embeddings | BAAI/bge-small-en-v1.5 (sentence-transformers) |
| LLM | OpenRouter API (NVIDIA Nemotron) |
| Auth | JWT (PyJWT + bcrypt) |

## Project Structure

```
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/               # App router pages
│   │   │   ├── dashboard/     # Main chat interface
│   │   │   ├── login/         # Login page
│   │   │   ├── register/      # Registration page
│   │   │   └── admin/knowledge/  # Admin knowledge base panel
│   │   ├── components/        # React components
│   │   │   └── chat/          # ChatWindow, ChatInput, ConversationSidebar
│   │   ├── services/          # API client functions
│   │   ├── store/             # Zustand state management
│   │   └── types/             # TypeScript interfaces
│   └── package.json
│
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── agents/            # Specialized AI agents
│   │   │   ├── billing.py     # Billing support agent
│   │   │   ├── technical.py   # Technical support agent
│   │   │   ├── product.py     # Product specialist agent
│   │   │   ├── complaint.py   # Complaint handling agent
│   │   │   ├── faq.py         # General FAQ agent
│   │   │   ├── router.py      # Intent-based agent routing
│   │   │   └── intent.py      # Keyword-based intent classifier
│   │   ├── api/v1/            # REST API endpoints
│   │   ├── services/          # Business logic
│   │   │   ├── knowledge_service.py   # PDF ingestion pipeline
│   │   │   ├── dataset_service.py     # Dataset ingestion with idempotency
│   │   │   ├── retrieval_service.py   # RAG retrieval + source resolution
│   │   │   ├── embedding_service.py   # Sentence-transformer embeddings
│   │   │   ├── vector_service.py      # FAISS vector indexing
│   │   │   └── llm_service.py         # OpenRouter LLM calls
│   │   ├── schemas/           # Pydantic models
│   │   └── database/          # MongoDB connection + indexes
│   ├── scripts/               # CLI tools
│   │   ├── ingest_dataset.py  # Dataset ingestion CLI
│   │   └── promote_admin.py   # User role management
│   ├── datasets/              # Public datasets (gitignored, ~1.9GB)
│   └── requirements.txt
│
├── docker-compose.yml
└── .gitignore
```

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+ (or pnpm)
- MongoDB Atlas account (or local MongoDB)

### 1. Clone and install

```bash
git clone <repo-url>
cd multi-agent-customer-support-ai

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
pnpm install
```

### 2. Configure environment

```bash
cd backend
cp .env.example .env
# Edit .env with your values:
#   MONGODB_URI=mongodb+srv://...
#   JWT_SECRET_KEY=<random-secret>
#   OPENROUTER_API_KEY=sk-or-...
```

### 3. Start the servers

```bash
# Backend (from backend/)
python -m uvicorn app.main:app --reload --port 8000

# Frontend (from frontend/)
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Create an admin user

Register an account through the UI, then promote it:

```bash
cd backend
python scripts/promote_admin.py --email your@email.com
```

Log out and log back in to see the admin panel.

### 5. Ingest knowledge base

From the admin panel (⚙ Knowledge Base → Datasets tab), click **Ingest All** to load the pre-packaged datasets. Or use the CLI:

```bash
cd backend
python scripts/ingest_dataset.py --dataset faq --path datasets/sample_faq.json
python scripts/ingest_dataset.py --dataset banking77
python scripts/ingest_dataset.py --dataset squad --path datasets/SQuAD-explorer/dataset/dev-v1.1.json
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | Public | Register a new user |
| POST | `/api/v1/auth/login` | Public | Login and get JWT token |
| GET | `/api/v1/auth/me` | User | Get current user profile |
| POST | `/api/v1/chat/messages` | User | Send a chat message |
| GET | `/api/v1/chat/conversations` | User | List conversation history |
| GET | `/api/v1/chat/conversations/{id}` | User | Get a conversation |
| POST | `/api/v1/knowledge/upload` | Admin | Upload a PDF document |
| GET | `/api/v1/knowledge` | User | List knowledge documents |
| GET | `/api/v1/knowledge/search` | User | Semantic search |
| GET | `/api/v1/knowledge/datasets` | Admin | List available datasets |
| POST | `/api/v1/knowledge/ingest-datasets` | Admin | Trigger dataset ingestion |
| DELETE | `/api/v1/knowledge/{id}` | Admin | Delete a document |

## How It Works

1. **User sends a message** → Frontend calls `POST /chat/messages`
2. **Intent classification** → Keyword-based classifier routes to the best agent
3. **RAG retrieval** → Agent embeds the query, searches FAISS for relevant chunks, expands with neighboring context
4. **LLM generation** → Agent builds a prompt with the retrieved context and sends it to the LLM
5. **Source attribution** → Response includes which agent answered and which documents were used
6. **Frontend renders** → Message displayed with expandable sources panel showing document names, text previews, and relevance scores

## License

MIT
