# Security Guidelines

## Environment Variables

**CRITICAL**: Never commit sensitive data to your repository.

### Required Environment Variables

Before deploying, ensure these environment variables are set:

```bash
# Slack Configuration (Required)
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret

# Grafana Security (Production)
GRAFANA_ADMIN_USER=your-admin-username
GRAFANA_ADMIN_PASSWORD=your-secure-password-here

# Timeout Configurations
HTTP_TIMEOUT=30
OLLAMA_TIMEOUT=60
```

## Docker Security

### Production Deployment
- The application runs as non-root user (UID 1000)
- Use multi-stage builds to reduce image size
- Regularly update base images for security patches

### Ollama Considerations
- Ollama requires elevated permissions for GPU access
- In production, consider running Ollama as a separate service
- Use proper network segmentation

## Kubernetes Security

### RBAC
- Service account with minimal required permissions
- Network policies to restrict traffic
- Pod security standards enforced

### Secrets Management
- Use Kubernetes secrets for sensitive data
- Never store secrets in ConfigMaps
- Consider using external secret management (e.g., Vault)

## Network Security

### Recommended Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: infra-copilot-netpol
spec:
  podSelector:
    matchLabels:
      app: infra-copilot
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

## Security Checklist

- [ ] Environment variables properly set
- [ ] No secrets in code or config files
- [ ] Docker image runs as non-root
- [ ] RBAC properly configured
- [ ] Network policies in place
- [ ] Regular security updates applied
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures tested

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
1. Do not create a public GitHub issue
2. Email security concerns to: [your-security-email]
3. Include details about the vulnerability
4. Allow time for assessment and patching

## Security Updates

Regularly update dependencies for security patches:

```bash
# Check for vulnerabilities
pip audit

# Update dependencies
pip install --upgrade -r requirements.txt
```
