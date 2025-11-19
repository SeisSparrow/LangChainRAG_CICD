# 🚨 Security Incident - API Key Leaked

## Incident Summary

**Date**: 2025-11-19
**Issue**: OpenAI API key was leaked and has been disabled by OpenAI
**Status**: 🔴 **ACTION REQUIRED**

---

## What Happened

OpenAI detected that an API key belonging to your organization was leaked, likely because it was committed to this GitHub repository or exposed in logs. The key has been automatically disabled.

**Leaked Key Details**:
- User: user-9ewwekkotws0lo0poan133jo
- Name: MacBookAir14 (sk-proj-...AMA)
- Organization: Zhen Zhang
- Email: zhennan2010@hotmail.com

---

## ✅ Immediate Action Steps

### Step 1: Create New OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Give it a descriptive name (e.g., "RAG-Production-2025-11")
4. **COPY THE KEY IMMEDIATELY** - you won't be able to see it again
5. Store it securely (password manager, NOT in code)

### Step 2: Update AWS Secrets Manager

Run this command with your **NEW** API key:

```bash
aws secretsmanager put-secret-value \
  --secret-id bee-edu-openai-key-secret \
  --secret-string 'sk-proj-YOUR_NEW_KEY_HERE' \
  --region us-east-1
```

**Verify the update**:
```bash
aws secretsmanager get-secret-value \
  --secret-id bee-edu-openai-key-secret \
  --region us-east-1 \
  --query 'SecretString' \
  --output text
```

### Step 3: Force App Runner Deployment

After updating the secret, force App Runner to pick up the new key:

```bash
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-east-1:808579124752:service/bee-edu-rag-service/55d6d7e710ff4d1fab6aa8857e67dbd2 \
  --region us-east-1
```

### Step 4: Wait for Deployment (3-5 minutes)

Monitor the deployment:

```bash
aws apprunner list-operations \
  --service-arn arn:aws:apprunner:us-east-1:808579124752:service/bee-edu-rag-service/55d6d7e710ff4d1fab6aa8857e67dbd2 \
  --region us-east-1 \
  --max-results 1
```

### Step 5: Verify Service Health

```bash
curl https://e9z3n3tvzm.us-east-1.awsapprunner.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "documents_count": 6
}
```

---

## 🔒 How to Prevent Future Leaks

### 1. Never Commit API Keys to Git

**Check current repository**:
```bash
# Search for any API keys in git history
git log -p | grep -i "sk-proj" || echo "No API keys found in recent commits"

# Search in current files
grep -r "sk-proj" . --exclude-dir=.git || echo "No API keys in current files"
```

### 2. Use .gitignore Properly

Ensure these patterns are in your `.gitignore`:
```
.env
.env.*
*.key
secrets/
credentials/
```

### 3. Use Git Hooks (Pre-commit)

Install pre-commit hook to check for secrets:
```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

### 4. Use GitHub Secret Scanning

GitHub automatically scans for secrets, but you should:
- Enable push protection in repository settings
- Review security alerts regularly

### 5. Rotate Keys Regularly

- Set a calendar reminder to rotate API keys every 90 days
- Use key expiration features when available

---

## 📊 Current Status

After completing the steps above, update this section:

- [ ] New OpenAI API key created
- [ ] AWS Secrets Manager updated
- [ ] App Runner deployment triggered
- [ ] Service health verified
- [ ] Old key confirmed disabled
- [ ] Repository scanned for other secrets

---

## 🔍 Root Cause Analysis

### Why Did This Happen?

The API key was likely exposed through one of these methods:

1. **Committed to Git**: Key was in a file that was committed
2. **Logged in Application**: Key was printed in logs (now visible in App Runner logs)
3. **Shared Publicly**: Repository was public with key exposed

### Specific to This Project

Looking at the repository, the key was stored in **AWS Secrets Manager** (correct approach), but it may have been:

1. **Temporarily used in environment variables during local testing**
2. **Exposed in GitHub Actions logs** (though we used secrets correctly)
3. **Used in a local .env file that was accidentally committed**

### Debug Logging Issue

In [app.py](app.py) lines 212-220, the health check endpoint shows the API key prefix when unhealthy:

```python
"api_key_prefix": api_key[:10] + "..." if api_key else None,
```

While this only shows the first 10 characters, it's still a security concern. This debug code should be removed in production.

---

## 🛡️ Security Best Practices Going Forward

### 1. Remove Debug Logging

Update `app.py` to remove the API key prefix logging:

```python
# REMOVE THIS in production:
"api_key_prefix": api_key[:10] + "..." if api_key else None,
```

### 2. Enable AWS Secrets Manager Rotation

```bash
aws secretsmanager rotate-secret \
  --secret-id bee-edu-openai-key-secret \
  --rotation-lambda-arn <rotation-lambda-arn> \
  --rotation-rules AutomaticallyAfterDays=90
```

### 3. Use AWS CloudWatch Alarms

Monitor for suspicious API usage:
- Unusual number of requests
- Requests from unexpected regions
- Failed authentication attempts

### 4. Implement Rate Limiting

Add rate limiting to your API endpoints to prevent abuse.

---

## 📞 Support Resources

- **OpenAI Security**: https://platform.openai.com/docs/guides/safety-best-practices
- **AWS Secrets Manager**: https://docs.aws.amazon.com/secretsmanager/
- **GitHub Secret Scanning**: https://docs.github.com/en/code-security/secret-scanning

---

## ✅ Post-Incident Checklist

After resolving the issue:

- [ ] Document what happened
- [ ] Update security practices
- [ ] Remove debug logging from production code
- [ ] Set up monitoring alerts
- [ ] Schedule next key rotation
- [ ] Review all repository files for other secrets
- [ ] Update team security training

---

**Last Updated**: 2025-11-19
**Incident Status**: 🔴 **OPEN** - Awaiting new API key deployment
