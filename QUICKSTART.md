# 快速开始 (Quick Start)

5 步完成从零到上线！

## 步骤 1: 准备配置文件

```bash
cp example.tfvars terraform.tfvars
```

编辑 `terraform.tfvars`:
```hcl
github_org_or_user = "your-github-username"
github_repo_name   = "LangChainRAG_CICD"
openai_api_key     = "sk-your-openai-api-key"
```

## 步骤 2: 部署 AWS 基础设施

```bash
./setup.sh
```

或手动运行:
```bash
terraform init
terraform apply
```

## 步骤 3: 配置 GitHub Secrets

在 GitHub 仓库: **Settings** → **Secrets** → **Actions** → **New secret**

添加以下 4 个 secrets:

```
AWS_REGION = us-east-1
ECR_REPOSITORY = <from terraform output>
AWS_IAM_ROLE_TO_ASSUME = <from terraform output>
APP_RUNNER_ARN = null  # 首次可留空
```

获取值:
```bash
terraform output
```

## 步骤 4: 推送代码

```bash
git add .
git commit -m "Initial commit: RAG app with CI/CD"
git push origin main
```

## 步骤 5: 测试应用

查看 GitHub Actions 日志获取 App Runner URL，然后:

```bash
# 健康检查
curl https://YOUR-APP-URL/health

# 提问测试
curl -X POST https://YOUR-APP-URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is LangChain?"}'

# 或使用测试脚本
python test_api.py YOUR-APP-URL
```

## 完成! 🎉

- API 文档: `https://YOUR-APP-URL/docs`
- 监控日志: AWS Console → App Runner → bee-edu-rag-service

---

## 常见问题

**Q: GitHub Actions 失败怎么办?**
A: 检查 Secrets 是否正确配置，特别是 `AWS_IAM_ROLE_TO_ASSUME` 必须是完整 ARN

**Q: 如何查看应用日志?**
A: AWS Console → App Runner → 选择服务 → Logs 标签

**Q: 如何更新知识库?**
A: 编辑 `app.py` 中的 `SAMPLE_DOCUMENTS`，推送到 GitHub 即可自动部署

**Q: 如何删除所有资源?**
A: `terraform destroy`

---

**详细文档**: 查看 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 和 [README.md](README.md)
