# App Runner 服务状态 (Service Status)

## 当前状态

✅ **App Runner 服务已成功创建并运行**

- **服务名称**: bee-edu-rag-service
- **服务 URL**: https://e9z3n3tvzm.us-east-1.awsapprunner.com
- **状态**: RUNNING
- **区域**: us-east-1

---

## 最终配置

### Secrets Manager 集成

✅ **已配置** - 服务现在可以从 AWS Secrets Manager 读取 OpenAI API key

```json
{
  "RuntimeEnvironmentSecrets": {
    "OPENAI_API_KEY": "arn:aws:secretsmanager:us-east-1:808579124752:secret:bee-edu-openai-key-secret-SZBNzG"
  }
}
```

### IAM 角色

✅ **服务角色** (拉取 ECR 镜像):
```
arn:aws:iam::808579124752:role/bee-edu-apprunner-role
```

✅ **实例角色** (访问 Secrets Manager):
```
arn:aws:iam::808579124752:role/bee-edu-apprunner-instance-role
```

### 资源配置

- **CPU**: 1 vCPU (1024)
- **Memory**: 2 GB (2048 MB)
- **Port**: 8080

---

## 部署问题修复历史

### 问题 1: iam:GetRole 权限缺失 ✅ 已修复
- 添加了 `iam:GetRole` 权限到 GitHub Actions 角色
- GitHub Actions 现在可以获取 App Runner 角色的 ARN

### 问题 2: CreateServiceLinkedRole 权限缺失 ✅ 已修复
- 添加了 `iam:CreateServiceLinkedRole` 权限
- 允许首次创建 App Runner 服务时创建服务关联角色

### 问题 3: Secrets Manager 配置缺失 ✅ 已修复
- 初始部署时没有配置 Secrets Manager 环境变量
- 手动更新服务添加了完整的 Secret ARN (包含后缀 -SZBNzG)
- 修复了 GitHub Actions workflow 以在未来部署时自动配置

---

## 测试服务

### 等待新部署完成

当前正在重新部署以应用 Secrets Manager 配置。等待 2-3 分钟后测试。

### 检查部署状态

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:808579124752:service/bee-edu-rag-service/55d6d7e710ff4d1fab6aa8857e67dbd2" \
  --region us-east-1 \
  --query 'Service.Status' \
  --output text
```

### 测试健康检查

```bash
curl https://e9z3n3tvzm.us-east-1.awsapprunner.com/health
```

**预期输出** (一旦部署完成):
```json
{
  "status": "healthy",
  "rag_initialized": true
}
```

### 测试 RAG 问答

```bash
curl -X POST https://e9z3n3tvzm.us-east-1.awsapprunner.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is LangChain?"}'
```

**预期输出**:
```json
{
  "question": "What is LangChain?",
  "answer": "LangChain is a framework for developing applications powered by language models...",
  "sources": [...]
}
```

### 访问 API 文档

在浏览器中打开:
```
https://e9z3n3tvzm.us-east-1.awsapprunner.com/docs
```

---

## 监控和日志

### AWS Console

1. 访问 AWS App Runner Console
2. 选择区域: us-east-1
3. 点击服务: bee-edu-rag-service
4. 查看 "Logs" 标签

### AWS CLI 查看日志

```bash
# 列出最近的操作
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:808579124752:service/bee-edu-rag-service/55d6d7e710ff4d1fab6aa8857e67dbd2" \
  --region us-east-1

# 查看服务详情
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:808579124752:service/bee-edu-rag-service/55d6d7e710ff4d1fab6aa8857e67dbd2" \
  --region us-east-1
```

---

## 下一步

### 1. 验证服务健康

等待当前部署完成 (约 2-3 分钟)，然后测试健康端点。

### 2. 测试所有 API 端点

使用提供的测试脚本:
```bash
python test_api.py e9z3n3tvzm.us-east-1.awsapprunner.com
```

### 3. 提交 Workflow 更新

当前的 workflow 已更新以正确处理 Secrets Manager。提交更改:

```bash
git add .github/workflows/deploy.yml
git commit -m "Fix: Update workflow to correctly configure Secrets Manager"
git push origin main
```

### 4. 配置自定义域名 (可选)

如果需要自定义域名 (例如 api.yourdomain.com):

1. 在 App Runner 控制台点击 "Custom domains"
2. 添加您的域名
3. 在 DNS 提供商 (如 Cloudflare) 添加 CNAME 记录

### 5. 设置监控告警 (可选)

配置 CloudWatch 告警:
- 健康检查失败
- 高错误率
- 高延迟

---

## 故障排除

### 如果服务仍然显示 unhealthy

1. **检查 Secrets Manager 权限**
   ```bash
   aws iam get-role-policy \
     --role-name bee-edu-apprunner-instance-role \
     --policy-name apprunner-secrets-policy
   ```

2. **验证 Secret 存在且有效**
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id bee-edu-openai-key-secret \
     --region us-east-1
   ```

3. **查看应用日志**
   - 在 AWS Console 中查看 App Runner 日志
   - 查找 Python 错误或异常

4. **检查 OpenAI API Key 是否有效**
   - 登录 OpenAI Platform
   - 验证 API Key 状态和配额

### 如果需要重新部署

```bash
aws apprunner start-deployment \
  --service-arn "arn:aws:apprunner:us-east-1:808579124752:service/bee-edu-rag-service/55d6d7e710ff4d1fab6aa8857e67dbd2" \
  --region us-east-1
```

---

## 成本估算

基于当前配置 (1 vCPU, 2 GB RAM, 低流量):

- **App Runner**: ~$10-15/月
- **ECR**: ~$1/月
- **Secrets Manager**: $0.40/月
- **数据传输**: < $1/月

**总计**: 约 **$12-20/月**

---

## 完成的任务 ✅

- [x] AWS 基础设施部署 (Terraform)
- [x] ECR 镜像仓库创建
- [x] GitHub Actions OIDC 认证配置
- [x] Docker 镜像构建和推送
- [x] App Runner 服务创建
- [x] Secrets Manager 集成
- [x] IAM 权限修复
- [x] 服务配置更新

## 待完成 ⏳

- [ ] 验证服务健康状态
- [ ] 测试所有 API 端点
- [ ] (可选) 配置自定义域名
- [ ] (可选) 设置监控告警

---

**当前操作**: 等待新部署完成以应用 Secrets Manager 配置

**预计完成时间**: 2-3 分钟

**最后更新**: 2025-11-19 03:30 UTC
