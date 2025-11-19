# 完整部署指南 (Complete Deployment Guide)

本指南将带您完成 LangChain RAG 应用从零到上线的全部步骤。

## 目录

1. [前置准备](#前置准备)
2. [第一步：部署 AWS 基础设施](#第一步部署-aws-基础设施)
3. [第二步：配置 GitHub Secrets](#第二步配置-github-secrets)
4. [第三步：部署应用](#第三步部署应用)
5. [第四步：测试应用](#第四步测试应用)
6. [故障排除](#故障排除)

---

## 前置准备

### 必需工具

- **AWS 账户**: 拥有创建 IAM、ECR、App Runner、Secrets Manager 权限
- **GitHub 账户**: 用于托管代码和运行 CI/CD
- **OpenAI API Key**: 从 https://platform.openai.com/api-keys 获取
- **本地工具**:
  - Terraform (>= 1.0)
  - AWS CLI (配置好凭证)
  - Git
  - Python 3.11+ (可选，用于本地测试)

### 验证工具安装

```bash
terraform --version
aws --version
git --version
python --version
```

---

## 第一步：部署 AWS 基础设施

### 1.1 克隆仓库

```bash
git clone <your-repository-url>
cd LangChainRAG_CICD
```

### 1.2 配置 Terraform 变量

创建 `terraform.tfvars` 文件 (已在 .gitignore 中，不会被提交):

```hcl
github_org_or_user = "your-github-username"
github_repo_name   = "LangChainRAG_CICD"
openai_api_key     = "sk-proj-xxxxxxxxxxxxxx"
```

> **重要**: 将上面的值替换为您的实际值

### 1.3 运行 Terraform

#### 方式一：使用自动化脚本 (推荐)

```bash
./setup.sh
```

这个脚本会：
- 检查所有必需工具
- 初始化 Terraform
- 显示变更计划
- 应用配置
- 显示需要添加到 GitHub 的 Secrets

#### 方式二：手动运行

```bash
# 初始化 Terraform
terraform init

# 查看变更计划
terraform plan

# 应用变更
terraform apply
```

### 1.4 保存 Terraform Outputs

运行成功后，保存以下输出值 (下一步需要用到):

```bash
# 查看所有输出
terraform output

# 单独查看每个值
terraform output github_actions_role_arn
terraform output ecr_repository_name
terraform output apprunner_service_arn  # 可能为 null
```

**示例输出**:

```
github_actions_role_arn = "arn:aws:iam::123456789012:role/github-actions-deploy-role"
ecr_repository_name = "bee-edu-rag-app"
apprunner_service_arn = null  # 将由 GitHub Actions 创建
```

---

## 第二步：配置 GitHub Secrets

### 2.1 进入 GitHub Secrets 设置

1. 打开您的 GitHub 仓库
2. 点击 **Settings** (设置)
3. 左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**

### 2.2 添加所需的 4 个 Secrets

按照下表添加每个 Secret:

| Secret 名称 | 值来源 | 示例值 |
|------------|--------|--------|
| `AWS_REGION` | 您使用的 AWS 区域 | `us-east-1` |
| `ECR_REPOSITORY` | `terraform output ecr_repository_name` | `bee-edu-rag-app` |
| `AWS_IAM_ROLE_TO_ASSUME` | `terraform output github_actions_role_arn` | `arn:aws:iam::123456789012:role/github-actions-deploy-role` |
| `APP_RUNNER_ARN` | `terraform output apprunner_service_arn` | 初次部署可以留空或填 `null` |

> **注意**: `APP_RUNNER_ARN` 在首次部署时可能为空，GitHub Actions 会自动创建服务

### 2.3 验证 Secrets 配置

所有 4 个 Secrets 应该显示在列表中。您无法查看值，但可以看到名称和创建时间。

---

## 第三步：部署应用

### 3.1 提交代码到 GitHub

如果这是新仓库，需要先连接到 GitHub:

```bash
# 初始化 Git 仓库 (如果还没有)
git init

# 添加远程仓库
git remote add origin https://github.com/your-username/LangChainRAG_CICD.git

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: LangChain RAG app with CI/CD"

# 推送到 main 分支 (会自动触发部署)
git push -u origin main
```

### 3.2 监控部署过程

1. 在 GitHub 仓库中，点击 **Actions** 标签
2. 查看正在运行的 "Deploy to AWS App Runner" workflow
3. 点击进入查看详细日志

**部署步骤** (约 5-10 分钟):
- ✓ Checkout code
- ✓ Configure AWS Credentials (OIDC)
- ✓ Log in to Amazon ECR
- ✓ Build and push Docker image
- ✓ Get App Runner Role ARNs
- ✓ Deploy to App Runner
- ✓ App Runner URL 输出

### 3.3 获取应用 URL

部署成功后，在 GitHub Actions 日志的最后一步 "App Runner URL" 可以看到:

```
App Runner Service URL: xxxxxx.us-east-1.awsapprunner.com
Service ID: xxxxxxxxxxxxxxxxxxxxxxxx
Deployment successful!
```

或者使用 AWS CLI 查询:

```bash
aws apprunner list-services --region us-east-1
```

---

## 第四步：测试应用

### 4.1 健康检查

```bash
curl https://your-app-url.us-east-1.awsapprunner.com/health
```

**预期输出**:
```json
{
  "status": "healthy",
  "rag_initialized": true
}
```

### 4.2 测试 RAG 问答

```bash
curl -X POST https://your-app-url.us-east-1.awsapprunner.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is LangChain?"}'
```

**预期输出**:
```json
{
  "question": "What is LangChain?",
  "answer": "LangChain is a framework for developing applications...",
  "sources": [
    {
      "content": "LangChain is a framework...",
      "metadata": {"source": "langchain_intro", "topic": "framework"}
    }
  ]
}
```

### 4.3 使用测试脚本

我们提供了一个自动化测试脚本:

```bash
# 安装 requests 库
pip install requests

# 测试部署的应用
python test_api.py your-app-url.us-east-1.awsapprunner.com

# 或本地测试
python test_api.py http://localhost:8080
```

### 4.4 访问 API 文档

在浏览器中打开:
```
https://your-app-url.us-east-1.awsapprunner.com/docs
```

这会显示 Swagger UI 交互式 API 文档。

---

## 故障排除

### 问题 1: Terraform apply 失败

**错误**: "Error: creating ECR repository"

**解决**:
- 检查 AWS 凭证是否正确配置
- 确认 IAM 用户有足够权限
- 运行 `aws sts get-caller-identity` 验证身份

### 问题 2: GitHub Actions OIDC 认证失败

**错误**: "Error: Could not assume role"

**解决**:
1. 检查 `AWS_IAM_ROLE_TO_ASSUME` Secret 是完整的 ARN
2. 确认 `terraform.tfvars` 中的 `github_org_or_user` 和 `github_repo_name` 正确
3. 确保推送到的是 `main` 分支 (信任策略限制)

### 问题 3: App Runner 部署失败

**错误**: "Service creation failed"

**可能原因**:

1. **ECR 镜像不存在**
   ```bash
   # 手动推送第一个镜像
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   docker build -t <ecr-url>:latest .
   docker push <ecr-url>:latest
   ```

2. **IAM 角色权限不足**
   - 检查 `apprunner_service_role` 是否有 ECR 访问权限
   - 检查 `apprunner_instance_role` 是否有 Secrets Manager 访问权限

### 问题 4: 应用返回 503 错误

**错误**: "RAG system not initialized"

**可能原因**:

1. **OpenAI API Key 无效**
   ```bash
   # 验证 Secrets Manager 中的值
   aws secretsmanager get-secret-value \
     --secret-id bee-edu-openai-key-secret \
     --region us-east-1
   ```

2. **实例角色无法读取 Secret**
   - 检查 IAM 策略
   - 查看 App Runner 日志

### 问题 5: 查看详细日志

**AWS Console**:
1. 打开 AWS App Runner 控制台
2. 选择 `bee-edu-rag-service`
3. 点击 "Logs" 标签

**AWS CLI**:
```bash
# 查看最近的操作
aws apprunner list-operations \
  --service-arn <your-service-arn> \
  --region us-east-1

# 查看服务详情
aws apprunner describe-service \
  --service-arn <your-service-arn> \
  --region us-east-1
```

---

## CI/CD 流程说明

### 工作原理

1. **触发**: 推送代码到 `main` 分支
2. **认证**: GitHub Actions 使用 OIDC 获取临时 AWS 凭证 (无需存储 Access Key!)
3. **构建**: 构建 Docker 镜像并打上 Git SHA 标签
4. **推送**: 推送镜像到 Amazon ECR
5. **部署**: 使用 `awslabs/amazon-app-runner-deploy` Action 更新服务
6. **验证**: 等待服务稳定并返回 URL

### 关键安全特性

- **OIDC 认证**: 无永久密钥，仅临时凭证
- **最小权限**: IAM 角色仅授予必需权限
- **分支保护**: 只有 `main` 分支可以部署
- **Secret 管理**: 敏感数据存储在 AWS Secrets Manager

---

## 本地开发

### 运行应用 (本地)

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export OPENAI_API_KEY="sk-your-api-key"

# 运行应用
python app.py
```

访问 http://localhost:8080/docs

### 本地 Docker 测试

```bash
# 构建镜像
docker build -t rag-app:local .

# 运行容器
docker run -p 8080:8080 \
  -e OPENAI_API_KEY="sk-your-api-key" \
  rag-app:local
```

---

## 自定义知识库

编辑 [app.py](app.py) 中的 `SAMPLE_DOCUMENTS`:

```python
SAMPLE_DOCUMENTS = [
    {
        "content": "您的文档内容...",
        "metadata": {"source": "doc1", "topic": "category1"}
    },
    # 添加更多文档...
]
```

修改后推送到 GitHub，CI/CD 会自动重新部署。

---

## 清理资源

**删除所有 AWS 资源**:

```bash
# 如果 App Runner 由 Terraform 管理
terraform destroy -target=aws_apprunner_service.rag_app_service

# 删除其他所有资源
terraform destroy
```

**注意**: 这会删除:
- App Runner 服务
- ECR 仓库及所有镜像
- Secrets Manager secret
- IAM 角色和策略
- OIDC 提供商

---

## 成本估算

- **App Runner**: ~$10-15/月 (低流量)
- **ECR**: ~$1/月 (存储)
- **Secrets Manager**: $0.40/月
- **数据传输**: < $1/月

**总计**: 约 **$12-20/月**

---

## 后续步骤

### 生产环境建议

1. **添加自定义域名**
   - 在 App Runner 中配置自定义域
   - 使用 Cloudflare 或 Route 53 管理 DNS

2. **监控和告警**
   - 配置 CloudWatch 告警
   - 设置日志保留策略
   - 启用 X-Ray 追踪

3. **扩展知识库**
   - 连接到数据库 (PostgreSQL + pgvector)
   - 支持文档上传
   - 实现向量索引持久化

4. **增强安全性**
   - 添加 API 认证 (JWT)
   - 实现速率限制
   - 启用 WAF

5. **性能优化**
   - 实现响应缓存
   - 优化 embedding 批处理
   - 考虑使用 Redis

---

## 联系和支持

如有问题，请：
1. 查看 [README.md](README.md)
2. 检查 GitHub Issues
3. 查看 AWS 日志
4. 参考官方文档

**相关资源**:
- [LangChain 文档](https://python.langchain.com/)
- [AWS App Runner 文档](https://docs.aws.amazon.com/apprunner/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

---

**祝您部署顺利! 🚀**
