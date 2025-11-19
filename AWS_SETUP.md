# AWS 凭证配置指南 (AWS Credentials Setup)

在运行 Terraform 之前，您需要配置 AWS 凭证。

## 方式一: 使用 AWS CLI 配置 (推荐)

### 步骤 1: 获取 AWS 凭证

1. 登录 AWS Console: https://console.aws.amazon.com/
2. 点击右上角您的用户名 → **Security Credentials** (安全凭证)
3. 找到 **Access keys** 部分
4. 点击 **Create access key** (创建访问密钥)
5. 选择用例: **Command Line Interface (CLI)**
6. 勾选确认框，点击 **Next**
7. (可选) 添加描述标签: "Terraform Deployment"
8. 点击 **Create access key**
9. **重要**: 保存 **Access key ID** 和 **Secret access key** (只显示一次!)

### 步骤 2: 配置 AWS CLI

运行以下命令:

```bash
aws configure
```

按提示输入:

```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

### 步骤 3: 验证配置

```bash
# 验证凭证是否有效
aws sts get-caller-identity
```

**预期输出**:
```json
{
    "UserId": "AIDAIOSFODNN7EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

如果看到类似输出，说明配置成功! ✅

---

## 方式二: 使用环境变量 (临时)

如果您不想持久化保存凭证，可以使用环境变量:

```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="us-east-1"
```

**注意**: 这些环境变量只在当前终端会话有效。

---

## 方式三: 使用 AWS SSO (企业用户)

如果您的组织使用 AWS SSO:

```bash
# 配置 SSO
aws configure sso

# 登录
aws sso login --profile your-profile-name

# 使用特定 profile
export AWS_PROFILE=your-profile-name
```

---

## 验证 IAM 用户权限

您的 IAM 用户需要以下权限才能运行 Terraform:

### 必需的 IAM 权限策略

创建一个自定义策略或使用以下托管策略:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:*",
        "ecr:*",
        "secretsmanager:*",
        "apprunner:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**或使用 AWS 托管策略** (不推荐用于生产):
- `AdministratorAccess` (完全访问权限)

### 检查权限

```bash
# 列出您的 IAM 用户附加的策略
aws iam list-attached-user-policies --user-name your-username

# 测试创建 ECR 仓库权限
aws ecr describe-repositories --region us-east-1
```

---

## 常见问题

### Q: 我没有 Access Key 创建权限怎么办?

**A**: 联系您的 AWS 管理员，请求:
1. 创建 Access Key 的权限
2. 或者让管理员为您创建并提供凭证

### Q: 我的账户启用了 MFA，如何使用?

**A**: 需要使用临时会话令牌:

```bash
# 获取临时凭证
aws sts get-session-token \
  --serial-number arn:aws:iam::123456789012:mfa/your-username \
  --token-code 123456

# 使用返回的临时凭证
export AWS_ACCESS_KEY_ID="ASIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_SESSION_TOKEN="FwoGZXIvYXdzEBYaD..."
```

### Q: 凭证文件存储在哪里?

**A**:
- **macOS/Linux**: `~/.aws/credentials` 和 `~/.aws/config`
- **Windows**: `%USERPROFILE%\.aws\credentials` 和 `%USERPROFILE%\.aws\config`

### Q: 如何使用多个 AWS 账户?

**A**: 使用 profiles:

```bash
# 配置多个 profile
aws configure --profile personal
aws configure --profile work

# 使用特定 profile
export AWS_PROFILE=work

# 或在 Terraform 中指定
terraform plan -var="profile=work"
```

---

## 安全最佳实践

1. **不要提交凭证到 Git**
   - `.gitignore` 已包含 `~/.aws/` 和相关文件
   - 永远不要在代码中硬编码 Access Keys

2. **定期轮换 Access Keys**
   - 建议每 90 天轮换一次
   - AWS Console → IAM → Users → Security Credentials

3. **使用最小权限原则**
   - 只授予必需的权限
   - 避免使用 `AdministratorAccess`

4. **启用 MFA**
   - IAM 用户启用 Multi-Factor Authentication
   - 增加账户安全性

5. **监控访问**
   - 启用 CloudTrail 记录 API 调用
   - 定期检查访问日志

---

## 下一步

配置完 AWS 凭证后:

1. **验证凭证**:
   ```bash
   aws sts get-caller-identity
   ```

2. **再次运行 setup.sh**:
   ```bash
   ./setup.sh
   ```

3. **或手动运行 Terraform**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

---

## 快速检查清单

- [ ] 已创建 AWS Access Key
- [ ] 已运行 `aws configure` 配置凭证
- [ ] 已验证 `aws sts get-caller-identity` 返回正确信息
- [ ] IAM 用户有足够权限 (IAM, ECR, Secrets Manager, App Runner)
- [ ] 已设置默认区域为 `us-east-1`
- [ ] 准备好运行 Terraform

---

**配置完成后，请重新运行 `./setup.sh` !**
