# Support Escalation AI

Support Escalation AI is an enterprise-grade IT support assistant that automates first-level technical support using Retrieval-Augmented Generation (RAG) and a multi-agent architecture. The system simulates a real-world enterprise helpdesk by intelligently routing user requests through Tier-1 and Tier-2 support workflows while preserving conversational context and maintaining detailed operational analytics.

Built using Python, Streamlit, LangGraph, Google Gemini, FAISS, Sentence Transformers, and Supabase, the application combines semantic search, confidence-aware routing, specialist escalation, secure authentication, persistent chat history, and an analytics dashboard into a single modern platform.

---

# Features

- Multi-Agent Support Workflow
  - Tier-1 AI Support Agent for common IT issues.
  - Automatic escalation to Tier-2 specialists for complex technical problems.
  - LangGraph-powered workflow orchestration.

- Retrieval-Augmented Generation (RAG)
  - Semantic document retrieval using FAISS.
  - SentenceTransformer embeddings for similarity search.
  - Knowledge Base powered troubleshooting.

- Confidence-Based Routing
  - Intelligent routing based on retrieval confidence.
  - Tier-1 resolves common issues.
  - Tier-2 specialists handle advanced diagnostics.

- Persistent Conversation History
  - Automatically saves conversations.
  - Sidebar conversation management.
  - Rename and delete conversations.
  - Conversation restoration across sessions.

- Authentication
  - Secure login and signup using Supabase Authentication.
  - Persistent user sessions.
  - Role-based access control (User & Admin).

- Admin Analytics Dashboard
  - Total users
  - Total queries
  - Tier-1 resolution rate
  - Tier-2 escalation rate
  - Retrieval confidence
  - Category distribution
  - Query trends
  - Recent escalations

- Modern User Interface
  - Dark & Light themes
  - Responsive layout
  - Modern conversation interface
  - Professional sidebar
  - Expandable technical details

---

# System Architecture

```text
                         User
                           │
                           ▼
               Authentication (Supabase)
                           │
                           ▼
                  Intent Detection Layer
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
 Greeting / Small Talk              IT Support Request
          │                                 │
          ▼                                 ▼
 Direct Response                 FAISS Knowledge Retrieval
                                            │
                                            ▼
                                      Router Agent
                                            │
                                            ▼
                                   Tier-1 Support Agent
                                            │
                           ┌────────────────┴───────────────┐
                           │                                │
                           ▼                                ▼
                      Issue Resolved                 Escalation Required
                           │                                │
                           ▼                                ▼
                    Final Response              Tier-2 Specialist Agent
                                                        │
                                                        ▼
                                                 Final Response
                                                        │
                                                        ▼
                                          Logging & Conversation Storage
                                                        │
                                                        ▼
                                               Analytics Dashboard
```

---

# AI Workflow

### 1. Intent Detection
Every user message is first classified to determine whether it is:

- Greeting
- Small Talk
- Gratitude
- Farewell
- Genuine IT Support Request

Conversational messages are answered directly without entering the support pipeline.

---

### 2. Knowledge Retrieval

Support-related queries undergo semantic search using:

- FAISS
- Sentence Transformers

The system retrieves the most relevant knowledge base documents.

---

### 3. Router Agent

The Router Agent:

- Determines the issue category
- Calculates retrieval confidence
- Routes the query to the appropriate support tier

Supported Categories:

- Authentication
- Software
- Hardware
- Network
- General

---

### 4. Tier-1 Support Agent

Tier-1 attempts to resolve common support requests using the retrieved knowledge base.

Possible outcomes:

- Resolved
- Needs More Information
- Escalated

---

### 5. Tier-2 Specialist Agents

When escalation is required, the request is forwarded to a specialist agent.

Current specialists include:

- Authentication
- Software
- Hardware
- Network

Tier-2 performs:

- Advanced diagnostics
- Root cause analysis
- Administrative troubleshooting
- Specialist recommendations

---

# Technology Stack

| Component | Technology |
|------------|------------|
| Frontend | Streamlit |
| Backend | Python |
| AI Model | Google Gemini |
| Agent Orchestration | LangGraph |
| Vector Database | FAISS |
| Embeddings | Sentence Transformers |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Visualizations | Plotly |
| Data Processing | Pandas |

---

# Project Structure

```text
project/
│
├── agents/                 # Router, Tier-1 and Tier-2 agents
├── auth/                   # Authentication services
├── components/             # Reusable UI components
├── database/               # Database services
├── KnowledgeBaseGenerator/ # Scripts for generating the FAISS index
├── pages/                  # Streamlit application pages
├── rag/                    # Retrieval-Augmented Generation pipeline
├── services/               # Chat and export services
├── styles/                 # Light & Dark themes
├── supabase/               # SQL migrations
├── utils/                  # Helper utilities
│
├── app.py
├── graph.py
├── logger.py
├── config.py
└── requirements.txt
```

---

# Installation

## 1. Clone the Repository

```bash
git clone <repository-url>
cd SupportEscalationAI
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file.

```env
GEMINI_API_KEY=your_gemini_api_key

SUPABASE_URL=https://your-project.supabase.co

SUPABASE_ANON_KEY=your_supabase_anon_key

APP_BASE_URL=http://localhost:8501
```

---

## 4. Build the Knowledge Base

```bash
python KnowledgeBaseGenerator/generate_kb.py
```

---

## 5. Run the Application

```bash
streamlit run app.py
```

Open:

```
http://localhost:8501
```

---

# Sample Queries

### Tier-1 Resolution

- How do I reset my password?
- Printer is offline.
- How do I clear browser cache?
- How do I upload documents?
- My Wi-Fi keeps disconnecting.

---

### Tier-2 Escalation

- Docker daemon won't start after a kernel update.
- VPN connects but internal resources are inaccessible.
- Active Directory authentication is failing.
- Kubernetes pods are stuck in CrashLoopBackOff.
- PostgreSQL replication is significantly delayed.

---

# Admin Dashboard

Administrators can monitor:

- Total Users
- Total Conversations
- Total Queries
- Tier-1 Resolution Rate
- Tier-2 Escalation Rate
- Average Retrieval Confidence
- Category Distribution
- Daily Query Trends
- Recent Escalations
- User Activity

---

# Future Enhancements

- Voice-based support
- Multi-language support
- Live ticket creation
- ServiceNow integration
- Jira integration
- Slack & Microsoft Teams support
- Email notifications
- Knowledge Base management portal
- Fine-tuned domain-specific language models

---

# Authors

Developed as an enterprise AI support system demonstrating Retrieval-Augmented Generation (RAG), multi-agent orchestration, confidence-aware routing, and intelligent support escalation.
