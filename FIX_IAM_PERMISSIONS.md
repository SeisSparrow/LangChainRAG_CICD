# 修复 IAM 权限错误 (Fix IAM Permissions Error)

## 问题说明

GitHub Actions 在 "Get App Runner Role ARNs" 步骤失败，错误信息:

```
An error occurred (AccessDenied) when calling the GetRole operation:
User: arn:aws:sts::808579124752:assumed-role/github-actions-deploy-role/GitHubActions-Deploy
is not authorized to perform: iam:GetRole on resource: role bee-edu-apprunner-role
```

## 原因

GitHub Actions 使用的 IAM 角色缺少 `iam:GetRole` 权限，无法获取 App Runner 角色的 ARN。

## 解决方案

### 步骤 1: 更新 Terraform 配置

我已经修复了 [main.tf](main.tf) 文件，添加了缺失的权限。

**变更内容**: 在 GitHub Actions IAM 策略中添加了:

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

### 步骤 2: 应用 Terraform 变更

运行以下命令更新 AWS IAM 策略:

```bash
# 查看变更
terraform plan

# 应用变更
terraform apply
```

**预期输出**:

```
Terraform will perform the following actions:

  # aws_iam_policy.github_actions_policy will be updated in-place
  ~ resource "aws_iam_policy" "github_actions_policy" {
      ~ policy = jsonencode(...)
      ...
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

输入 `yes` 确认应用。

### 步骤 3: 重新触发 GitHub Actions

有两种方式:

**方式 1: 重新运行失败的 workflow**

1. 在 GitHub Actions 页面，点击失败的 workflow
2. 点击右上角 **Re-run jobs** → **Re-run failed jobs**

**方式 2: 推送新的 commit**

```bash
# 提交 Terraform 变更
git add main.tf
git commit -m "Fix: Add iam:GetRole permission for GitHub Actions"
git push origin main
```

---

## 验证修复

GitHub Actions 应该成功通过 "Get App Runner Role ARNs" 步骤:

```
✓ Get App Runner Role ARNs
  Access Role ARN: arn:aws:iam::808579124752:role/bee-edu-apprunner-role
  Instance Role ARN: arn:aws:iam::808579124752:role/bee-edu-apprunner-instance-role
```

然后继续部署到 App Runner。

---

## 完整修复命令

```bash
# 1. 应用 Terraform 变更
terraform apply -auto-approve

# 2. 提交变更
git add main.tf FIX_IAM_PERMISSIONS.md
git commit -m "Fix: Add iam:GetRole permission for GitHub Actions"
git push origin main

# 3. 等待 GitHub Actions 自动运行
# 或在 GitHub 网页上手动 Re-run failed jobs
```

---

## 为什么需要这个权限？

workflow 中的这一步需要动态获取 ARN:

```yaml
- name: Get App Runner Role ARNs
  run: |
    ACCESS_ROLE_ARN=$(aws iam get-role --role-name bee-edu-apprunner-role --query 'Role.Arn' --output text)
    INSTANCE_ROLE_ARN=$(aws iam get-role --role-name bee-edu-apprunner-instance-role --query 'Role.Arn' --output text)
```

`aws iam get-role` 命令需要 `iam:GetRole` 权限。

---

## 替代方案 (不推荐)

如果不想修改 IAM 权限，可以直接在 GitHub Secrets 中添加角色 ARN:

1. 获取角色 ARN:
   ```bash
   terraform output
   ```

2. 在 GitHub Secrets 中添加:
   - `APPRUNNER_ACCESS_ROLE_ARN` = arn:aws:iam::...
   - `APPRUNNER_INSTANCE_ROLE_ARN` = arn:aws:iam::...

3. 修改 workflow，使用 secrets 而不是动态获取

但这种方式不够灵活，推荐使用上面的 Terraform 修复方案。

---

**修复完成后，您的 CI/CD 流程应该可以正常工作了！** 🚀
