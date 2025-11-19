# 部署问题修复记录 (Deployment Fixes Log)

本文档记录了部署过程中遇到的问题和解决方案。

---

## 问题 1: iam:GetRole 权限缺失

### 错误信息
```
An error occurred (AccessDenied) when calling the GetRole operation:
User: arn:aws:sts::808579124752:assumed-role/github-actions-deploy-role/GitHubActions-Deploy
is not authorized to perform: iam:GetRole on resource: role bee-edu-apprunner-role
```

### 原因
GitHub Actions 需要动态获取 App Runner 角色的 ARN，但 IAM 策略中缺少 `iam:GetRole` 权限。

### 解决方案
在 [main.tf](main.tf) 的 GitHub Actions IAM 策略中添加:

```hcl
{
  Effect = "Allow",
  Action = [
    "iam:GetRole"
  ],
  Resource = [
    aws_iam_role.apprunner_instance_role.arn,
    aws_iam_role.apprunner_service_role.arn
  ]
}
```

### 修复时间
2025-11-19 03:12 UTC

### 状态
✅ 已解决 - Terraform apply 成功，GitHub Actions 可以获取角色 ARN

---

## 问题 2: CreateServiceLinkedRole 权限缺失

### 错误信息
```
Error: AccessDenied. Couldn't create a service-linked role for App Runner.
When creating the first service in the account, caller must have the
'iam:CreateServiceLinkedRole' permission. Use the 'AWSAppRunnerFullAccess'
managed user policy to ensure users have all required permissions.
```

### 原因
当 AWS 账户首次创建 App Runner 服务时，需要创建一个服务关联角色 (Service-Linked Role)。这需要 `iam:CreateServiceLinkedRole` 权限。

### 解决方案
在 [main.tf](main.tf) 的 GitHub Actions IAM 策略中添加:

```hcl
{
  Effect = "Allow",
  Action = [
    "iam:CreateServiceLinkedRole"
  ],
  Resource = "arn:aws:iam::*:role/aws-service-role/apprunner.amazonaws.com/AWSServiceRoleForAppRunner",
  Condition = {
    StringLike = {
      "iam:AWSServiceName" = "apprunner.amazonaws.com"
    }
  }
}
```

**重要**: 这个权限仅在账户首次创建 App Runner 服务时需要。一旦服务关联角色创建完成，后续部署不再需要此权限。

### 修复时间
2025-11-19 03:15 UTC

### 状态
✅ 已解决 - Terraform apply 成功，等待 GitHub Actions 验证

---

## 完整的 GitHub Actions IAM 权限列表

修复后，GitHub Actions 角色具有以下权限:

### ECR (镜像仓库)
- `ecr:GetAuthorizationToken` - 登录 ECR
- `ecr:BatchCheckLayerAvailability` - 检查镜像层
- `ecr:CompleteLayerUpload` - 完成层上传
- `ecr:InitiateLayerUpload` - 初始化层上传
- `ecr:PutImage` - 推送镜像
- `ecr:UploadLayerPart` - 上传镜像层

### App Runner (服务管理)
- `apprunner:StartDeployment` - 启动部署
- `apprunner:DescribeService` - 查看服务详情
- `apprunner:UpdateService` - 更新服务
- `apprunner:ListOperations` - 列出操作
- `apprunner:ListServices` - 列出服务
- `apprunner:CreateService` - 创建服务

### IAM (权限管理)
- `iam:PassRole` - 传递角色给 App Runner
- `iam:GetRole` - 获取角色信息
- `iam:CreateServiceLinkedRole` - 创建服务关联角色 (仅首次)

---

## 部署流程图

```
1. GitHub Actions 触发
   ↓
2. OIDC 认证 → AWS (临时凭证)
   ↓
3. 登录 ECR ✅
   ↓
4. 构建并推送 Docker 镜像 ✅
   ↓
5. 获取 App Runner 角色 ARN ✅ (修复 1)
   ↓
6. 创建/更新 App Runner 服务 ✅ (修复 2)
   ↓
7. 等待服务稳定
   ↓
8. 输出服务 URL ✅
```

---

## 验证步骤

1. **检查 Terraform 应用**
   ```bash
   terraform plan
   # 应该显示 "No changes"
   ```

2. **查看 IAM 策略**
   ```bash
   aws iam get-policy-version \
     --policy-arn arn:aws:iam::808579124752:policy/github-actions-deploy-policy \
     --version-id v3
   ```

3. **监控 GitHub Actions**
   - 访问: https://github.com/SeisSparrow/LangChainRAG_CICD/actions
   - 查看最新的 workflow run
   - 所有步骤应该显示绿色 ✅

4. **测试 App Runner 服务**
   ```bash
   # 获取服务 URL
   aws apprunner list-services --region us-east-1

   # 测试健康检查
   curl https://YOUR-SERVICE-URL/health
   ```

---

## 最佳实践总结

### 1. 权限最小化原则
- ✅ 只授予必需的权限
- ✅ 使用 Resource 限制权限范围
- ✅ 使用 Condition 增加额外限制

### 2. OIDC vs Access Keys
- ✅ 使用 OIDC (无永久密钥)
- ✅ 临时凭证自动过期
- ✅ 更安全，易于审计

### 3. 增量调试
- ✅ 逐步添加权限
- ✅ 根据错误信息调整
- ✅ 记录每次修复

### 4. 服务关联角色
- App Runner 服务关联角色只需创建一次
- 后续部署不再需要 `CreateServiceLinkedRole` 权限
- 可以在首次成功部署后移除此权限

---

## 如果仍然失败

### 检查清单

- [ ] Terraform apply 成功执行
- [ ] GitHub Secrets 配置正确
- [ ] IAM 策略版本已更新 (v3 或更高)
- [ ] GitHub Actions 使用的是最新的代码
- [ ] ECR 镜像成功推送
- [ ] App Runner 服务关联角色已创建

### 调试命令

```bash
# 检查 IAM 策略版本
aws iam list-policy-versions \
  --policy-arn arn:aws:iam::808579124752:policy/github-actions-deploy-policy

# 查看 App Runner 服务
aws apprunner list-services --region us-east-1

# 查看服务关联角色
aws iam get-role \
  --role-name AWSServiceRoleForAppRunner
```

---

## 下一步

一旦 GitHub Actions 成功完成:

1. **获取 App Runner URL**
2. **测试 API 端点**
3. **更新 GitHub Secrets** (如果需要)
4. **配置自定义域名** (可选)
5. **设置监控告警** (可选)

---

**当前状态**: ✅ 所有已知权限问题已修复，等待 GitHub Actions 验证
**最后更新**: 2025-11-19 03:15 UTC
