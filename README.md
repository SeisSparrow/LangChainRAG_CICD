# LangChain RAG Application with CI/CD

A complete LangChain-based Retrieval-Augmented Generation (RAG) application with automated CI/CD pipeline deploying to AWS App Runner.

## Features

- **LangChain RAG System**: Question-answering system with vector-based document retrieval
- **FastAPI Backend**: RESTful API with automatic documentation
- **Docker Containerization**: Production-ready Docker setup
- **Automated CI/CD**: GitHub Actions with OIDC authentication (no access keys!)
- **AWS App Runner**: Fully managed deployment with auto-scaling
- **Secure Secret Management**: OpenAI API keys stored in AWS Secrets Manager

## Architecture

```
GitHub → GitHub Actions (OIDC) → AWS ECR → AWS App Runner
                                          ↓
                                  AWS Secrets Manager
```

## Prerequisites

- AWS Account with appropriate permissions
- GitHub Account and repository
- OpenAI API Key
- Terraform installed locally
- Git installed locally

## Setup Instructions

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd LangChainRAG_CICD
```

### Step 2: Deploy AWS Infrastructure with Terraform

1. **Create a `terraform.tfvars` file**:

```hcl
github_org_or_user = "your-github-username"
github_repo_name   = "LangChainRAG_CICD"
openai_api_key     = "sk-your-openai-api-key"
```

2. **Initialize and apply Terraform**:

```bash
terraform init
terraform plan
terraform apply
```

3. **Save the outputs** - You'll need these values for GitHub Secrets:

```bash
# View outputs
terraform output

# Example outputs:
# github_actions_role_arn = "arn:aws:iam::123456789012:role/github-actions-deploy-role"
# ecr_repository_name = "bee-edu-rag-app"
# apprunner_service_arn = "arn:aws:apprunner:us-east-1:123456789012:service/bee-edu-rag-service/..."
```

### Step 3: Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following 4 secrets:

| Secret Name | Value Source | Example |
|-------------|--------------|---------|
| `AWS_REGION` | Your AWS region | `us-east-1` |
| `ECR_REPOSITORY` | `terraform output ecr_repository_name` | `bee-edu-rag-app` |
| `APP_RUNNER_ARN` | `terraform output apprunner_service_arn` | `arn:aws:apprunner:...` |
| `AWS_IAM_ROLE_TO_ASSUME` | `terraform output github_actions_role_arn` | `arn:aws:iam::123456789012:role/github-actions-deploy-role` |

### Step 4: Push to GitHub

```bash
git add .
git commit -m "Initial commit: RAG app with CI/CD"
git push origin main
```

The GitHub Actions workflow will automatically:
1. Authenticate with AWS using OIDC (no access keys!)
2. Build the Docker image
3. Push to Amazon ECR
4. Deploy to AWS App Runner
5. Output the service URL

### Step 5: Access Your Application

After deployment completes (check GitHub Actions logs), access your application:

```bash
# Get the App Runner service URL
aws apprunner list-services --region us-east-1

# Or check the GitHub Actions workflow output
```

## API Endpoints

Once deployed, your API will have the following endpoints:

### `GET /`
Welcome message and API information

### `GET /health`
Health check endpoint (used by App Runner)

### `GET /docs`
Interactive API documentation (Swagger UI)

### `POST /ask`
Ask a question to the RAG system

**Request:**
```json
{
  "question": "What is LangChain?"
}
```

**Response:**
```json
{
  "question": "What is LangChain?",
  "answer": "LangChain is a framework for developing applications powered by language models...",
  "sources": [
    {
      "content": "LangChain is a framework...",
      "metadata": {
        "source": "langchain_intro",
        "topic": "framework"
      }
    }
  ]
}
```

### `GET /documents`
List all documents in the knowledge base

## Testing the API

### Using curl:

```bash
# Health check
curl https://<your-app-runner-url>/health

# Ask a question
curl -X POST https://<your-app-runner-url>/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'

# List documents
curl https://<your-app-runner-url>/documents
```

### Using Python:

```python
import requests

url = "https://<your-app-runner-url>"

# Ask a question
response = requests.post(
    f"{url}/ask",
    json={"question": "What is LangChain?"}
)
print(response.json())
```

## Local Development

1. **Create a virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Set environment variable**:

```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
```

4. **Run the application**:

```bash
python app.py
```

5. **Access locally**:
   - API: http://localhost:8080
   - Docs: http://localhost:8080/docs

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD workflow with OIDC
├── app.py                      # FastAPI + LangChain RAG application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── .dockerignore              # Docker build exclusions
├── main.tf                     # Terraform infrastructure
└── README.md                   # This file
```

## CI/CD Pipeline Details

The GitHub Actions workflow (`.github/workflows/deploy.yml`) implements:

1. **OIDC Authentication**: Secure, keyless authentication to AWS
2. **ECR Login**: Authenticate to Amazon Elastic Container Registry
3. **Docker Build & Push**: Build image and push with Git SHA tag
4. **Dynamic Role ARNs**: Automatically fetch required IAM role ARNs
5. **App Runner Deployment**: Deploy using `awslabs/amazon-app-runner-deploy`
6. **Service Stability Check**: Wait for deployment to complete

### Key Security Features:

- **No Access Keys**: Uses OIDC for temporary credentials
- **Least Privilege**: IAM roles with minimal required permissions
- **Secret Management**: OpenAI API key stored in AWS Secrets Manager
- **Branch Protection**: Only main branch can trigger deployments

## Customizing the Knowledge Base

To add your own documents, edit the `SAMPLE_DOCUMENTS` list in [app.py](app.py):

```python
SAMPLE_DOCUMENTS = [
    {
        "content": "Your document content here...",
        "metadata": {"source": "doc_name", "topic": "category"}
    },
    # Add more documents...
]
```

## Monitoring and Logs

### View logs in AWS Console:

1. Go to AWS App Runner console
2. Select your service: `bee-edu-rag-service`
3. Click "Logs" tab

### View logs using AWS CLI:

```bash
aws apprunner list-operations \
  --service-arn <your-service-arn> \
  --region us-east-1
```

## Troubleshooting

### Deployment fails with "Image not found"

Make sure you've pushed at least one image to ECR before App Runner can deploy:

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push manually
docker build -t <ecr-repository-url>:latest .
docker push <ecr-repository-url>:latest
```

### GitHub Actions fails with OIDC error

Verify your GitHub Secrets are correct:
- `AWS_IAM_ROLE_TO_ASSUME` should be the full ARN
- The role's trust policy allows your specific repo and branch

### App returns 503 Service Unavailable

Check App Runner logs - this usually means:
- OpenAI API key is invalid or missing
- API key retrieval from Secrets Manager failed
- Check IAM permissions for instance role

## Cleanup

To destroy all AWS resources:

```bash
# Delete App Runner service first (if managed by Terraform)
terraform destroy -target=aws_apprunner_service.rag_app_service

# Delete all other resources
terraform destroy
```

## Cost Estimation

- **AWS App Runner**: ~$0.007/GB-hour memory + $0.064/vCPU-hour compute
- **Amazon ECR**: $0.10/GB/month storage
- **AWS Secrets Manager**: $0.40/secret/month
- **Data Transfer**: Minimal costs for API requests

Estimated monthly cost for low-traffic app: **$10-20/month**

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
