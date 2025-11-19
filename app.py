import os
import json
import boto3
import numpy as np
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
import uvicorn

app = FastAPI(title="Simple RAG Demo", version="2.0.0")

# Global variables
client = None
documents = []
embeddings_cache = {}
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
        secrets_client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
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
        "id": "doc1"
    },
    {
        "content": "Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval "
                   "with text generation. It retrieves relevant documents and uses them as context for generating responses.",
        "id": "doc2"
    },
    {
        "content": "Vector databases store embeddings of text documents, allowing for semantic search. "
                   "FAISS is a popular library for efficient similarity search and clustering of dense vectors.",
        "id": "doc3"
    },
    {
        "content": "OpenAI provides powerful language models like GPT-4 and GPT-3.5-turbo. "
                   "These models can understand and generate human-like text for various applications.",
        "id": "doc4"
    },
    {
        "content": "AWS App Runner is a fully managed service that makes it easy to deploy containerized web applications. "
                   "It automatically builds and deploys your application and provides load balancing and auto-scaling.",
        "id": "doc5"
    },
    {
        "content": "CI/CD stands for Continuous Integration and Continuous Deployment. "
                   "GitHub Actions allows you to automate your software workflows with OIDC for secure authentication.",
        "id": "doc6"
    }
]

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def initialize_rag_system():
    """Initialize the RAG system with OpenAI client and pre-compute embeddings"""
    global client, documents, embeddings_cache, initialization_error

    try:
        # Get API key
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not found")

        print("Initializing OpenAI client...")
        client = OpenAI(api_key=api_key)

        print("Pre-computing document embeddings...")
        documents = SAMPLE_DOCUMENTS.copy()

        # Pre-compute embeddings for all documents
        for doc in documents:
            response = client.embeddings.create(
                input=doc["content"],
                model="text-embedding-ada-002"
            )
            embeddings_cache[doc["id"]] = response.data[0].embedding

        print(f"RAG system initialized successfully with {len(documents)} documents!")
        initialization_error = None
        return True

    except Exception as e:
        error_msg = f"Error initializing RAG system: {type(e).__name__}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        initialization_error = error_msg
        return False

def find_relevant_documents(query: str, top_k: int = 3) -> List[Dict]:
    """Find most relevant documents for a query using embeddings"""
    try:
        # Get query embedding
        response = client.embeddings.create(
            input=query,
            model="text-embedding-ada-002"
        )
        query_embedding = response.data[0].embedding

        # Calculate similarities
        similarities = []
        for doc in documents:
            doc_embedding = embeddings_cache[doc["id"]]
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in similarities[:top_k]]

    except Exception as e:
        print(f"Error finding relevant documents: {e}")
        return []

def generate_answer(question: str, context_docs: List[Dict]) -> str:
    """Generate an answer using GPT with context"""
    try:
        # Build context from documents
        context = "\n\n".join([f"Document {i+1}: {doc['content']}"
                               for i, doc in enumerate(context_docs)])

        # Create prompt
        prompt = f"""Answer the following question based on the provided context.

Context:
{context}

Question: {question}

Answer:"""

        # Call GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error generating answer: {e}")
        raise

# Request/Response models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict]

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
        "message": "Simple RAG API (No LangChain)",
        "version": "2.0.0",
        "endpoints": {
            "/health": "Health check",
            "/ask": "Ask a question (POST)",
            "/documents": "List documents (GET)",
            "/docs": "API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for App Runner"""
    if client is None:
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
    return {
        "status": "healthy",
        "rag_initialized": True,
        "documents_count": len(documents)
    }

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question and get an answer using RAG"""
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="RAG system not initialized. Check OpenAI API key configuration."
        )

    try:
        # Find relevant documents
        relevant_docs = find_relevant_documents(request.question)

        if not relevant_docs:
            raise HTTPException(status_code=500, detail="Could not find relevant documents")

        # Generate answer
        answer = generate_answer(request.question, relevant_docs)

        return AnswerResponse(
            question=request.question,
            answer=answer,
            sources=[{"content": doc["content"][:200] + "...", "id": doc["id"]}
                    for doc in relevant_docs]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all documents in the knowledge base"""
    return {
        "total_documents": len(documents),
        "documents": documents
    }

if __name__ == "__main__":
    # Run the FastAPI app
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
