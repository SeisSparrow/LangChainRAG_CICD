#!/bin/bash

# LangChain RAG Application Setup Script
# This script helps you set up and deploy the RAG application

set -e

echo "================================================"
echo "LangChain RAG Application Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required tools are installed
echo "Checking prerequisites..."

command -v terraform >/dev/null 2>&1 || { echo -e "${RED}Error: Terraform is not installed.${NC}" >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo -e "${RED}Error: AWS CLI is not installed.${NC}" >&2; exit 1; }
command -v git >/dev/null 2>&1 || { echo -e "${RED}Error: Git is not installed.${NC}" >&2; exit 1; }

echo -e "${GREEN}✓ All prerequisites installed${NC}"
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}Warning: terraform.tfvars not found${NC}"
    echo "Creating terraform.tfvars from example.tfvars..."
    cp example.tfvars terraform.tfvars
    echo -e "${YELLOW}Please edit terraform.tfvars with your actual values before continuing.${NC}"
    echo ""
    read -p "Press enter when you've updated terraform.tfvars..."
fi

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan Terraform changes
echo ""
echo "Planning Terraform changes..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "Do you want to apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborting..."
    exit 0
fi

# Apply Terraform
echo ""
echo "Applying Terraform configuration..."
terraform apply tfplan

# Get outputs
echo ""
echo "================================================"
echo "Terraform deployment complete!"
echo "================================================"
echo ""
echo "Please add the following secrets to your GitHub repository:"
echo "(Go to Settings > Secrets and variables > Actions > New repository secret)"
echo ""

echo -e "${GREEN}Secret Name:${NC} AWS_REGION"
echo -e "${GREEN}Value:${NC} us-east-1"
echo ""

echo -e "${GREEN}Secret Name:${NC} ECR_REPOSITORY"
echo -e "${GREEN}Value:${NC}"
terraform output -raw ecr_repository_name
echo ""
echo ""

echo -e "${GREEN}Secret Name:${NC} AWS_IAM_ROLE_TO_ASSUME"
echo -e "${GREEN}Value:${NC}"
terraform output -raw github_actions_role_arn
echo ""
echo ""

# Check if App Runner service was created
if terraform output apprunner_service_arn 2>/dev/null | grep -q "arn:aws"; then
    echo -e "${GREEN}Secret Name:${NC} APP_RUNNER_ARN"
    echo -e "${GREEN}Value:${NC}"
    terraform output -raw apprunner_service_arn
    echo ""
else
    echo -e "${YELLOW}Note: APP_RUNNER_ARN will be created by GitHub Actions on first deployment${NC}"
fi

echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo "1. Add the above secrets to your GitHub repository"
echo "2. Commit and push your code to the main branch:"
echo "   git add ."
echo "   git commit -m 'Initial commit: RAG app with CI/CD'"
echo "   git push origin main"
echo "3. Check GitHub Actions for deployment progress"
echo "4. Access your deployed application using the App Runner URL"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
