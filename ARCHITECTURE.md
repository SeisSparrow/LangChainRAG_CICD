# 系统架构 (System Architecture)

## 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Developer Workflow                          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ git push
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           GitHub Repository                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Code Files:                                                  │  │
│  │  • app.py (LangChain RAG Application)                        │  │
│  │  • Dockerfile                                                 │  │
│  │  • requirements.txt                                          │  │
│  │  • .github/workflows/deploy.yml                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Triggers on push to main
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions (CI/CD)                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Workflow Steps:                                              │  │
│  │  1. ✓ Checkout code                                          │  │
│  │  2. ✓ OIDC Auth (No Access Keys!)                           │  │
│  │  3. ✓ Login to ECR                                           │  │
│  │  4. ✓ Build Docker image                                     │  │
│  │  5. ✓ Push to ECR                                            │  │
│  │  6. ✓ Deploy to App Runner                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ OIDC Authentication
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS Cloud Infrastructure                      │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  IAM - Identity & Access Management                          │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ OIDC Provider: token.actions.githubusercontent.com    │   │   │
│  │  │ GitHub Actions Role (Assumed by CI/CD)               │   │   │
│  │  │ App Runner Service Role (Pull ECR images)            │   │   │
│  │  │ App Runner Instance Role (Access Secrets Manager)    │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ECR - Elastic Container Registry                            │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ Repository: bee-edu-rag-app                          │   │   │
│  │  │ Images: latest, <git-sha>                            │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                         │                                            │
│                         │ Pulls Docker Image                         │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  App Runner - Fully Managed Container Service                │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ Service: bee-edu-rag-service                         │   │   │
│  │  │ • Auto-scaling                                       │   │   │
│  │  │ • Load balancing                                     │   │   │
│  │  │ • Health checks                                      │   │   │
│  │  │ • HTTPS endpoint                                     │   │   │
│  │  │                                                       │   │   │
│  │  │ Container:                                            │   │   │
│  │  │ • CPU: 1 vCPU                                        │   │   │
│  │  │ • Memory: 2 GB                                       │   │   │
│  │  │ • Port: 8080                                         │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                         │                                            │
│                         │ Reads Secrets                              │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Secrets Manager                                              │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ Secret: bee-edu-openai-key-secret                    │   │   │
│  │  │ Value: sk-proj-xxxxxxxxxxxxxx                        │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTPS Endpoint
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                              End Users                                │
│  • Browser: https://xxxxx.awsapprunner.com/docs                      │
│  • API Client: curl https://xxxxx.awsapprunner.com/ask               │
│  • Mobile App: REST API calls                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 应用内部架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application (app.py)                    │
│                                                                       │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │   Endpoints  │      │  LangChain   │      │   OpenAI     │      │
│  │              │      │     RAG      │      │     API      │      │
│  │  GET  /      │      │              │      │              │      │
│  │  GET  /health│ ───► │  Retrieval   │ ───► │  GPT-3.5     │      │
│  │  POST /ask   │      │  QA Chain    │      │  Turbo       │      │
│  │  GET  /docs  │      │              │      │              │      │
│  └──────────────┘      └──────────────┘      └──────────────┘      │
│         │                      │                                     │
│         │                      ▼                                     │
│         │            ┌──────────────────┐                           │
│         │            │  Vector Store    │                           │
│         │            │     (FAISS)      │                           │
│         │            │                  │                           │
│         │            │  • Embeddings    │                           │
│         │            │  • Similarity    │                           │
│         │            │    Search        │                           │
│         │            └──────────────────┘                           │
│         │                      │                                     │
│         │                      ▼                                     │
│         │            ┌──────────────────┐                           │
│         │            │  Knowledge Base  │                           │
│         │            │  (In-Memory)     │                           │
│         │            │                  │                           │
│         │            │  Sample Docs:    │                           │
│         │            │  • LangChain     │                           │
│         │            │  • RAG           │                           │
│         │            │  • AWS           │                           │
│         │            │  • CI/CD         │                           │
│         │            └──────────────────┘                           │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │           OpenAPI Documentation (Swagger UI)              │      │
│  │  Interactive API testing interface at /docs               │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## RAG 工作流程

```
User Question: "What is LangChain?"
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 1: Question Embedding                              │
│ Convert question to vector using OpenAI Embeddings      │
│ "What is LangChain?" → [0.123, -0.456, 0.789, ...]     │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2: Similarity Search in Vector Store               │
│ FAISS finds top 3 most relevant documents              │
│ • Doc 1: LangChain framework intro (score: 0.95)       │
│ • Doc 2: OpenAI models (score: 0.72)                   │
│ • Doc 3: Vector databases (score: 0.68)                │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3: Build Context                                   │
│ Combine retrieved documents as context                  │
│                                                          │
│ Context:                                                 │
│ "LangChain is a framework for developing applications   │
│  powered by language models..."                         │
│ + other relevant document snippets                      │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 4: Generate Answer with LLM                        │
│ Send to GPT-3.5-turbo:                                  │
│                                                          │
│ Prompt:                                                  │
│ "Use the following context to answer:                   │
│  Context: [retrieved documents]                         │
│  Question: What is LangChain?                           │
│  Answer:"                                                │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 5: Return Answer with Sources                      │
│ {                                                        │
│   "answer": "LangChain is a framework...",              │
│   "sources": [                                           │
│     {"content": "...", "metadata": {...}}               │
│   ]                                                      │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
```

---

## CI/CD 安全架构

```
┌─────────────────────────────────────────────────────────┐
│              Traditional Approach (INSECURE)             │
│  ┌──────────────────────────────────────────────────┐  │
│  │ GitHub Secrets:                                   │  │
│  │ • AWS_ACCESS_KEY_ID (long-lived)                 │  │
│  │ • AWS_SECRET_ACCESS_KEY (long-lived)             │  │
│  │                                                   │  │
│  │ Problems:                                         │  │
│  │ ✗ Keys can be stolen                             │  │
│  │ ✗ Permanent access                               │  │
│  │ ✗ Difficult to rotate                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

                         VS

┌─────────────────────────────────────────────────────────┐
│            Modern Approach (SECURE - OIDC)               │
│  ┌──────────────────────────────────────────────────┐  │
│  │ GitHub Actions Workflow:                          │  │
│  │ 1. Request temporary credentials from AWS        │  │
│  │ 2. AWS validates GitHub OIDC token               │  │
│  │ 3. AWS returns temporary credentials (1 hour)    │  │
│  │ 4. Use temporary credentials for deployment      │  │
│  │ 5. Credentials automatically expire              │  │
│  │                                                   │  │
│  │ Benefits:                                         │  │
│  │ ✓ No permanent keys stored                       │  │
│  │ ✓ Time-limited access (1 hour)                   │  │
│  │ ✓ Automatic rotation                             │  │
│  │ ✓ Granular permissions                           │  │
│  │ ✓ Audit trail                                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 数据流图

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ POST /ask {"question": "What is RAG?"}
     │
     ▼
┌─────────────────┐
│  App Runner     │
│  Load Balancer  │
└────┬────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  FastAPI Application                     │
│  ┌────────────────────────────────────┐ │
│  │ 1. Receive request                 │ │
│  └────┬───────────────────────────────┘ │
│       │                                  │
│  ┌────▼───────────────────────────────┐ │
│  │ 2. Generate question embedding    │ │
│  │    via OpenAI API                  │ │───┐
│  └────┬───────────────────────────────┘ │   │
│       │                                  │   │
│  ┌────▼───────────────────────────────┐ │   │
│  │ 3. Search FAISS vector store      │ │   │
│  │    for similar documents           │ │   │
│  └────┬───────────────────────────────┘ │   │
│       │                                  │   │
│  ┌────▼───────────────────────────────┐ │   │
│  │ 4. Retrieve top 3 documents       │ │   │
│  └────┬───────────────────────────────┘ │   │
│       │                                  │   │
│  ┌────▼───────────────────────────────┐ │   │
│  │ 5. Build prompt with context      │ │   │
│  └────┬───────────────────────────────┘ │   │
│       │                                  │   │
│  ┌────▼───────────────────────────────┐ │   │
│  │ 6. Call GPT-3.5-turbo             │ │───┤
│  └────┬───────────────────────────────┘ │   │
│       │                                  │   │
│  ┌────▼───────────────────────────────┐ │   │
│  │ 7. Format response with sources   │ │   │
│  └────┬───────────────────────────────┘ │   │
└───────┼──────────────────────────────────┘   │
        │                                       │
        │                                       ▼
        │                              ┌─────────────────┐
        │                              │   OpenAI API    │
        │                              │  (External)     │
        │                              │                 │
        │                              │ • Embeddings    │
        │                              │ • GPT-3.5-turbo │
        │                              └─────────────────┘
        │
        ▼
   ┌──────────┐
   │  Client  │ {"answer": "RAG is...", "sources": [...]}
   └──────────┘
```

---

## 成本优化架构

```
┌─────────────────────────────────────────────────────────┐
│  Low Traffic (< 1000 requests/day)                      │
│  ┌────────────────────────────────────────────────┐    │
│  │ App Runner: 1 vCPU, 2 GB Memory                │    │
│  │ • Scales down to 1 instance                     │    │
│  │ • Cost: ~$10-15/month                           │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Medium Traffic (1000-10000 requests/day)               │
│  ┌────────────────────────────────────────────────┐    │
│  │ App Runner: 2 vCPU, 4 GB Memory                │    │
│  │ • Auto-scales: 1-5 instances                    │    │
│  │ • Cost: ~$50-100/month                          │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  High Traffic (> 10000 requests/day)                    │
│  ┌────────────────────────────────────────────────┐    │
│  │ Consider migrating to:                          │    │
│  │ • ECS Fargate (more control)                    │    │
│  │ • EKS (Kubernetes)                              │    │
│  │ • Add caching layer (Redis/ElastiCache)        │    │
│  │ • Cost: Variable, $200+/month                   │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 监控和可观测性

```
┌─────────────────────────────────────────────────────────┐
│                    CloudWatch Logs                       │
│  ┌────────────────────────────────────────────────┐    │
│  │ Log Groups:                                     │    │
│  │ • /aws/apprunner/bee-edu-rag-service/app       │    │
│  │ • /aws/apprunner/bee-edu-rag-service/service   │    │
│  │                                                 │    │
│  │ Logs include:                                   │    │
│  │ • Request/Response                              │    │
│  │ • Errors and exceptions                         │    │
│  │ • Performance metrics                           │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   CloudWatch Metrics                     │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Request count                                 │    │
│  │ • Response time (p50, p99)                      │    │
│  │ • Error rate                                    │    │
│  │ • CPU utilization                               │    │
│  │ • Memory utilization                            │    │
│  │ • Active instances                              │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  App Runner Dashboard                    │
│  ┌────────────────────────────────────────────────┐    │
│  │ Visual monitoring:                              │    │
│  │ • Real-time request graphs                      │    │
│  │ • Deployment history                            │    │
│  │ • Health status                                 │    │
│  │ • Automatic restarts                            │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

**更多详情请参考**:
- [README.md](README.md) - 项目概览和 API 文档
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 完整部署指南
- [QUICKSTART.md](QUICKSTART.md) - 5 步快速开始
