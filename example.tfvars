# Example Terraform variables file
# Copy this to terraform.tfvars and fill in your actual values

# Your GitHub username or organization name
github_org_or_user = "your-github-username"

# Your GitHub repository name
github_repo_name = "LangChainRAG_CICD"

# Your OpenAI API key (get from https://platform.openai.com/api-keys)
openai_api_key = "sk-your-openai-api-key-here"

# Optional: Set to true if you want Terraform to create the App Runner service
# Default is false - GitHub Actions will create/manage the service instead
# manage_apprunner_via_terraform = false
