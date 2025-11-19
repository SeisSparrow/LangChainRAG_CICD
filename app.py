import os
import json
import boto3
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.schema import Document
import uvicorn

app = FastAPI(title="LangChain RAG Demo", version="1.0.0")

# Global variables to hold our RAG components
vector_store = None
qa_chain = None
initialization_error = None

# Get OpenAI API key from AWS Secrets Manager or environment
def get_openai_api_key():
    """Retrieve OpenAI API key from AWS Secrets Manager or environment variable"""
    # Try environment variable first (for local development)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    # Try AWS Secrets Manager (for production)
    try:
        secret_name = "bee-edu-openai-key-secret"
        region_name = "us-east-1"

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return secret
    except Exception as e:
        print(f"Warning: Could not retrieve secret from AWS Secrets Manager: {e}")
        return None

# Sample documents for the RAG system
SAMPLE_DOCUMENTS = [
    {
        "content": "LangChain is a framework for developing applications powered by language models. "
                   "It enables applications that are context-aware and can reason about how to answer based on provided context.",
        "metadata": {"source": "langchain_intro", "topic": "framework"}
    },
    {
        "content": "Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval "
                   "with text generation. It retrieves relevant documents and uses them as context for generating responses.",
        "metadata": {"source": "rag_intro", "topic": "technique"}
    },
    {
        "content": "Vector databases store embeddings of text documents, allowing for semantic search. "
                   "FAISS is a popular library for efficient similarity search and clustering of dense vectors.",
        "metadata": {"source": "vector_db_intro", "topic": "database"}
    },
    {
        "content": "OpenAI provides powerful language models like GPT-4 and GPT-3.5-turbo. "
                   "These models can understand and generate human-like text for various applications.",
        "metadata": {"source": "openai_intro", "topic": "ai_models"}
    },
    {
        "content": "AWS App Runner is a fully managed service that makes it easy to deploy containerized web applications. "
                   "It automatically builds and deploys your application and provides load balancing and auto-scaling.",
        "metadata": {"source": "aws_intro", "topic": "cloud"}
    },
    {
        "content": "CI/CD stands for Continuous Integration and Continuous Deployment. "
                   "GitHub Actions allows you to automate your software workflows with OIDC for secure authentication.",
        "metadata": {"source": "cicd_intro", "topic": "devops"}
    }
]

def initialize_rag_system():
    """Initialize the RAG system with vector store and QA chain"""
    global vector_store, qa_chain, initialization_error

    try:
        # Get API key
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not found")

        os.environ["OPENAI_API_KEY"] = api_key

        print("Creating embeddings...")
        # Create embeddings - use default model for compatibility
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)

        # Convert sample documents to LangChain documents
        documents = [
            Document(page_content=doc["content"], metadata=doc["metadata"])
            for doc in SAMPLE_DOCUMENTS
        ]

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        split_docs = text_splitter.split_documents(documents)

        print(f"Creating vector store with {len(split_docs)} document chunks...")
        # Create vector store
        vector_store = FAISS.from_documents(split_docs, embeddings)

        print("Creating LLM...")
        # Create LLM with explicit API key
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=api_key
        )

        print("Creating QA chain...")
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )

        print("RAG system initialized successfully!")
        initialization_error = None
        return True

    except Exception as e:
        error_msg = f"Error initializing RAG system: {type(e).__name__}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        initialization_error = error_msg
        return False

# Request/Response models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    success = initialize_rag_system()
    if not success:
        print("Warning: RAG system initialization failed. Health check will report unhealthy.")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LangChain RAG API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/ask": "Ask a question (POST)",
            "/docs": "API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for App Runner"""
    if qa_chain is None:
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        has_key = api_key is not None and len(api_key) > 0
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "RAG system not initialized",
                "has_api_key": has_key,
                "api_key_prefix": api_key[:10] + "..." if api_key else None,
                "error": initialization_error
            }
        )
    return {"status": "healthy", "rag_initialized": True}

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    api_key = os.getenv("OPENAI_API_KEY")
    return {
        "has_openai_key": api_key is not None,
        "key_length": len(api_key) if api_key else 0,
        "key_prefix": api_key[:15] + "..." if api_key else None,
        "all_env_vars": list(os.environ.keys())
    }

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question and get an answer using RAG

    Example:
    ```json
    {
        "question": "What is LangChain?"
    }
    ```
    """
    if qa_chain is None:
        raise HTTPException(
            status_code=503,
            detail="RAG system not initialized. Check OpenAI API key configuration."
        )

    try:
        result = qa_chain.invoke({"query": request.question})

        # Extract source information
        sources = []
        if "source_documents" in result:
            for doc in result["source_documents"]:
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })

        return AnswerResponse(
            question=request.question,
            answer=result["result"],
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all documents in the knowledge base"""
    return {
        "total_documents": len(SAMPLE_DOCUMENTS),
        "documents": SAMPLE_DOCUMENTS
    }

if __name__ == "__main__":
    # Run the FastAPI app
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
