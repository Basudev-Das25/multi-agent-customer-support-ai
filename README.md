<div align="center">

# 🤖 Multi-Agent Customer Support AI

### Intelligent Customer Support Powered by Specialized AI Agents

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![FAISS](https://img.shields.io/badge/FAISS-Vector-Search-006400?style=for-the-badge&logo=meta&logoColor=white)](https://faiss.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

**An enterprise-grade AI customer support platform** that uses specialized agents to handle different types of customer queries with retrieval-augmented generation (RAG) from a knowledge base.

[🚀 Quick Start](#-quick-start) · [📖 Documentation](#-architecture) · [🎯 Features](#-features) · [🔧 API Reference](#-api-reference)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🧠 Multi-Agent Architecture
- **5 Specialized AI Agents** with automatic intent classification
- **FAQ Agent** — General questions and knowledge base queries
- **Billing Agent** — Payments, refunds, subscriptions, invoices
- **Technical Agent** — Login issues, errors, bugs, installation
- **Product Agent** — Features, pricing, comparisons
- **Complaint Agent** — Empathetic handling of customer issues

</td>
<td width="50%">

### 🔍 RAG Pipeline
- **Semantic Search** using FAISS vector store
- **Sentence-Transformer Embeddings** (BAAI/bge-small-en-v1.5)
- **Chunk Expansion** with neighboring context for better relevance
- **Source Attribution** — Every response shows which documents were used
- **PDF Upload** — Admins can add documents directly

</td>
</tr>
<tr>
<td>

### 📊 Dataset Ingestion
- **5 Pre-built Datasets** ready to ingest
  - FAQ (sample Q&A)
  - Banking77 (13K customer queries)
  - SQuAD (Wikipedia comprehension)
  - DailyDialog (multi-turn conversations)
  - CFPB Complaints (consumer complaints)
- **Idempotent Ingestion** — Run multiple times safely

</td>
<td>

### 🎨 Modern UI/UX
- **Indigo-Violet Dark Theme** with glass-morphism
- **Fluid Animations** — Staggered lists, floating elements, typing pulse
- **Source Attribution Panel** — Expandable docs with relevance scores
- **Agent Tags** — Color-coded badges showing which agent answered
- **Responsive Design** — Works on desktop and mobile

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Chat Window  │  │  Sidebar     │  │  Admin Dashboard     │   │
│  │  (Messages)   │  │  (History)   │  │  (Knowledge Base)    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
└─────────┼─────────────────┼──────────────────────┼───────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Layer                              │   │
│  │  POST /chat/messages  │  GET /knowledge  │  POST /upload  │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐   │
│  │                 Agent Router                              │   │
│  │            (Intent Classification)                        │   │
│  └───┬───────┬───────┬───────┬───────┬──────────────────────┘   │
│      │       │       │       │       │                          │
│      ▼       ▼       ▼       ▼       ▼                          │
│  ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐                      │
│  │ FAQ  ││ BILL ││TECH  ││PROD  ││COMP  │  ← Specialized Agents│
│  └──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘                      │
│     │       │       │       │       │                          │
│     └───────┴───────┴───┬───┴───────┘                          │
│                         │                                      │
│  ┌──────────────────────▼──────────────────────────────────┐   │
│  │              RAG Retrieval Service                       │   │
│  │  Query → Embed → FAISS Search → Chunk Expansion         │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐   │
│  │                  LLM Service                              │   │
│  │        (OpenRouter API → NVIDIA Nemotron)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   MongoDB   │  │    FAISS    │  │  Sentence-Transformer   │ │
│  │  (Metadata) │  │  (Vectors)  │  │    (Embeddings)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|------------|---------|---------|
| Python | 3.13+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| pnpm | Latest | Package manager |
| MongoDB Atlas | Free tier | Database |

### 1️⃣ Clone & Install

```bash
# Clone the repository
git clone https://github.com/Basudev-Das25/multi-agent-customer-support-ai.git
cd multi-agent-customer-support-ai

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
pnpm install
```

### 2️⃣ Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# MongoDB Atlas (get from cloud.mongodb.com)
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority

# JWT Secret (generate a random string)
JWT_SECRET_KEY=your-super-secret-key-here

# OpenRouter API (get from openrouter.ai)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
```

### 3️⃣ Start Servers

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
pnpm dev
```

### 4️⃣ Access the App

Open **http://localhost:3000** in your browser.

---

## 👤 User Management

### Register & Login

1. Navigate to **http://localhost:3000/register**
2. Create an account with email and password
3. Login at **http://localhost:3000/login**

### Promote to Admin

```bash
# List all users
python scripts/promote_admin.py --list

# Promote specific user
python scripts/promote_admin.py --email user@example.com

# Promote first non-admin user
python scripts/promote_admin.py --first
```

**Admin privileges:**
- Access Knowledge Base dashboard
- Upload PDF documents
- Ingest datasets
- Delete documents

---

## 📚 Knowledge Base

### Ingest Pre-built Datasets

From the admin panel (**⚙ Knowledge Base → Datasets tab**), click **Ingest All**.

Or use the CLI:

```bash
# Ingest all datasets
python scripts/ingest_dataset.py --dataset faq --path datasets/sample_faq.json
python scripts/ingest_dataset.py --dataset banking77
python scripts/ingest_dataset.py --dataset squad --path datasets/SQuAD-explorer/dataset/dev-v1.1.json
python scripts/ingest_dataset.py --dataset dailydialog --path datasets/XDailyDialog/data/1k_part_data/dialogues_text_En.txt
python scripts/ingest_dataset.py --dataset complaints --path datasets/complaints.json.zip --sample 1000
```

### Available Datasets

| Dataset | Description | Records |
|---------|-------------|---------|
| **FAQ** | Sample Q&A for password, refunds, subscriptions | 3 |
| **Banking77** | Customer intent queries (77 categories) | 13,083 |
| **SQuAD** | Wikipedia reading comprehension | 10,000+ |
| **DailyDialog** | Multi-turn conversation snippets | 1,000 |
| **CFPB Complaints** | Consumer financial complaints | 1,000+ |

### Upload Custom PDFs

1. Go to **⚙ Knowledge Base → Documents tab**
2. Drag & drop a PDF or click to browse
3. Document is automatically chunked, embedded, and indexed

---

## 🤖 Agent System

### How Intent Classification Works

```
User Query: "I want a refund for my subscription"
                    │
                    ▼
        ┌─────────────────────┐
        │  Intent Classifier  │
        │  (Keyword Matching) │
        └──────────┬──────────┘
                   │
        Matches: "refund", "subscription"
                   │
                   ▼
        ┌─────────────────────┐
        │   Billing Agent     │
        │  (Specialized)      │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  RAG Retrieval      │
        │  (Knowledge Base)   │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  LLM Generation     │
        │  (With Context)     │
        └─────────────────────┘
```

### Agent Specializations

| Agent | Keywords | Use Case |
|-------|----------|----------|
| **FAQ** | policy, contact, hours, company | General questions |
| **Billing** | payment, refund, subscription, invoice | Financial queries |
| **Technical** | login, password, error, bug, crash | Technical issues |
| **Product** | feature, pricing, comparison, version | Product info |
| **Complaint** | angry, frustrated, terrible, escalate | Customer complaints |

---

## 🔧 API Reference

### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}

# Login
POST /api/v1/auth/login
{
  "email": "john@example.com",
  "password": "securepassword123"
}

# Response: { "access_token": "eyJ...", "token_type": "bearer" }
```

### Chat

```bash
# Send message
POST /api/v1/chat/messages
Authorization: Bearer <token>
{
  "content": "How do I reset my password?",
  "conversation_id": "optional-existing-conversation-id"
}

# Response includes:
# - answer: AI-generated response
# - metadata.agent_name: Which agent handled it
# - metadata.sources: Which documents were used
```

### Knowledge Base

```bash
# List documents
GET /api/v1/knowledge

# Search knowledge base
GET /api/v1/knowledge/search?query=password+reset

# Upload PDF (admin only)
POST /api/v1/knowledge/upload
Content-Type: multipart/form-data
Body: file=<pdf-file>

# List datasets (admin only)
GET /api/v1/knowledge/datasets

# Ingest datasets (admin only)
POST /api/v1/knowledge/ingest-datasets
{
  "dataset": "faq",  // optional, omit for all
  "force": false     // re-ingest even if already done
}
```

---

## 🎨 UI Features

### Chat Interface
- **Real-time messaging** with conversation history
- **Source Attribution Panel** — Expandable section showing:
  - Which agent answered (color-coded badge)
  - Document names and text previews
  - Relevance scores
- **Markdown rendering** with syntax highlighting
- **Copy messages** with one click
- **Auto-scroll** with "New messages" indicator

### Admin Dashboard
- **Documents Tab** — View, upload, delete PDFs
- **Datasets Tab** — One-click ingestion of pre-built datasets
- **Search** — Semantic search across knowledge base
- **Status Tracking** — See ingestion progress and document counts

### Animations & Effects
- **Glass-morphism** — Frosted glass effect on cards
- **Staggered Lists** — Items animate in sequence
- **Floating Elements** — Gentle hover animations
- **Typing Indicator** — Smooth pulsing dots
- **Shimmer Loading** — Elegant skeleton screens
- **Focus Glow** — Input fields glow on focus

---

## 🛠️ Development

### Code Quality

```bash
# Backend linting
cd backend
ruff check app/
black --check app/
isort --check-only app/

# Auto-fix
ruff check app/ --fix
black app/
isort app/
```

### Project Structure

```
multi-agent-customer-support-ai/
├── frontend/                    # Next.js 16 + React 19
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   ├── components/          # React components
│   │   ├── services/            # API client functions
│   │   ├── store/               # Zustand state
│   │   └── types/               # TypeScript types
│   └── package.json
│
├── backend/                     # FastAPI + Python 3.13
│   ├── app/
│   │   ├── agents/              # AI agents (FAQ, Billing, etc.)
│   │   ├── api/v1/              # REST endpoints
│   │   ├── services/            # Business logic
│   │   ├── schemas/             # Pydantic models
│   │   └── database/            # MongoDB connection
│   ├── scripts/                 # CLI tools
│   ├── tests/                   # Pytest tests
│   └── requirements.txt
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URI` | ✅ | MongoDB Atlas connection string |
| `DATABASE_NAME` | ✅ | Database name (default: `customer_support_ai`) |
| `JWT_SECRET_KEY` | ✅ | Secret key for JWT tokens |
| `OPENROUTER_API_KEY` | ✅ | API key from openrouter.ai |
| `OPENROUTER_MODEL` | ❌ | LLM model (default: `nvidia/nemotron-3-ultra-550b-a55b:free`) |
| `EMBEDDING_MODEL` | ❌ | Embedding model (default: `BAAI/bge-small-en-v1.5`) |
| `FAISS_INDEX_PATH` | ❌ | FAISS index storage path |
| `TOP_K_RESULTS` | ❌ | Number of search results (default: `5`) |

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Embedding Dimension** | 384 |
| **Chunk Size** | ~1000 characters |
| **Chunk Overlap** | ~150 characters |
| **Search Latency** | <100ms |
| **LLM Response Time** | 1-3 seconds |
| **Supported File Types** | PDF |

---

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [Next.js](https://nextjs.org/) — React framework
- [FAISS](https://faiss.ai/) — Vector similarity search
- [MongoDB Atlas](https://www.mongodb.com/atlas) — Cloud database
- [OpenRouter](https://openrouter.ai/) — LLM API gateway
- [BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) — Sentence embeddings

---

<div align="center">

**Built with ❤️ by Basudev Das**

[![GitHub](https://img.shields.io/badge/GitHub-Profile-181717?style=for-the-badge&logo=github)](https://github.com/Basudev-Das25)

</div>
