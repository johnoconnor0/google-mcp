# Security Policy

## Supported Versions

The following versions of the Google Ads MCP Server are currently supported with security updates:

| Version | Supported          | Notes                                    |
| ------- | ------------------ | ---------------------------------------- |
| 1.0.x   | :white_check_mark: | Current stable release (v1)              |
| 2.0.x   | :construction:     | In development (v2) - not yet released   |
| < 1.0   | :x:                | Pre-release versions no longer supported |

## Reporting a Vulnerability

We take the security of the Google Ads MCP Server seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**GitHub Issues (Preferred)**

1. Go to the [Issues page](https://github.com/johnoconnor0/google-ads-mcp/issues)
2. Click "New Issue"
3. **For sensitive security issues**: Email open-source@weblifter.com.au first, or use GitHub's private vulnerability reporting if available
4. **For non-sensitive issues**: Create a public issue with the "security" label

**What to Include**

Please include the following information in your report:

- **Description**: Clear description of the vulnerability
- **Impact**: What could an attacker accomplish?
- **Reproduction Steps**: Detailed steps to reproduce the issue
- **Affected Versions**: Which versions are affected?
- **Suggested Fix**: If you have ideas for how to fix it (optional)
- **Environment**: Python version, OS, Google Ads API version

**Example Report Template**:
```
## Vulnerability Description
[Brief description of the security issue]

## Impact
[What could happen if this is exploited?]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [Additional steps...]

## Affected Versions
- Version 1.0.0
- All versions prior to X.X.X

## Suggested Fix (Optional)
[Your suggestions for fixing the issue]

## Environment
- Python: 3.10
- OS: Windows 11
- Google Ads API: v17
```

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: 1-7 days
  - **High**: 7-14 days
  - **Medium**: 14-30 days
  - **Low**: 30-90 days

### Disclosure Policy

- **Private Disclosure**: Please give us reasonable time to fix the issue before public disclosure
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)
- **Public Advisory**: Once fixed, we will publish a security advisory with details

## Security Best Practices

### Credential Management

**NEVER commit credentials to version control**

- Do NOT commit your `developer_token`, `client_id`, `client_secret`, or `refresh_token`
- Use environment variables for sensitive configuration
- Use `.gitignore` to exclude configuration files containing secrets
- Consider using a secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)

**Example - Secure credential storage**:
```bash
# Use environment variables
export GOOGLE_ADS_DEVELOPER_TOKEN="your-token"
export GOOGLE_ADS_CLIENT_ID="your-client-id"
export GOOGLE_ADS_CLIENT_SECRET="your-secret"
export GOOGLE_ADS_REFRESH_TOKEN="your-refresh-token"
```

### OAuth Token Management

**Rotate tokens regularly**

- Refresh tokens should be rotated periodically (every 90 days recommended)
- Use short-lived access tokens (handled automatically by the Google Ads API client)
- Revoke tokens that are no longer needed

**Secure token storage**:
- Store refresh tokens in encrypted storage
- Limit file permissions: `chmod 600 config.yaml` on Linux/macOS
- Never log refresh tokens or access tokens

### MCC (Manager) Account Security

**For multi-account management**:

- Use MCC accounts with appropriate access levels
- Follow the principle of least privilege
- Audit MCC access regularly
- Enable two-factor authentication (2FA) on Google Ads accounts

### API Rate Limiting

**Prevent abuse and quota exhaustion**:

- Implement rate limiting in your application
- Use the built-in caching mechanisms (Memory or Redis)
- Monitor API quota usage via Google Ads API reporting
- Implement exponential backoff for retries

### Logging and Monitoring

**Secure logging practices**:

- Never log sensitive data (tokens, credentials, personal information)
- Use structured logging with appropriate log levels
- Implement log rotation to prevent disk exhaustion
- Monitor logs for suspicious activity
- Use the built-in logger with appropriate configurations:

```yaml
logging:
  level: INFO  # Use INFO or WARNING in production (not DEBUG)
  format: json
  console: false
  file: /var/log/google-mcp/server.log
```

### Network Security

**Secure communications**:

- Always use HTTPS for API communications (enforced by Google Ads API)
- If exposing the MCP server over a network, use TLS/SSL
- Implement proper authentication and authorization
- Use firewall rules to restrict access

### Input Validation

**Prevent injection attacks**:

- The server validates all GAQL queries using `query_optimizer.py`
- Customer IDs are validated to prevent injection
- User inputs are sanitized before being used in API calls
- Pydantic models enforce type safety

### Dependency Management

**Keep dependencies up to date**:

```bash
# Check for outdated packages
pip list --outdated

# Update packages
pip install --upgrade google-ads mcp httpx pydantic

# Audit for known vulnerabilities
pip-audit
```

**Monitor security advisories**:
- Subscribe to GitHub security advisories for this repository
- Monitor [Google Ads API release notes](https://developers.google.com/google-ads/api/docs/release-notes)
- Check [Python security advisories](https://www.python.org/news/security/)

## Known Security Considerations

### Google Ads API Authentication

- **OAuth 2.0 Flow**: The server uses OAuth 2.0 for authentication
- **Developer Token**: Required for API access - protect like a password
- **Refresh Token**: Long-lived token that can generate access tokens - protect carefully

### Refresh Token Storage

- Refresh tokens are stored in `config.yaml` or environment variables
- **Risk**: If compromised, an attacker can access your Google Ads accounts
- **Mitigation**: Use encrypted storage, restrict file permissions, rotate regularly

### Developer Token Protection

- Developer tokens are account-specific and grant API access
- **Risk**: Token misuse could lead to unauthorized API access
- **Mitigation**: Treat as a secret, never commit to version control, use environment variables

### Multi-Account Access

- MCC accounts can access multiple client accounts
- **Risk**: Compromise of MCC credentials affects all managed accounts
- **Mitigation**: Use strict access controls, audit regularly, enable 2FA

### GAQL Query Execution

- Custom GAQL queries can access account data
- **Risk**: Malicious queries could extract sensitive information
- **Mitigation**: Query validation, input sanitization, access controls

## Security Updates

### Update Notifications

Security updates will be announced via:

- **GitHub Releases**: All releases include security notes
- **GitHub Security Advisories**: Critical vulnerabilities
- **CHANGELOG.md**: Detailed change notes (when created)

### Applying Security Updates

```bash
# Update to the latest version
cd /path/to/google-mcp
git pull origin main
pip install -r requirements.txt --upgrade

# Restart the MCP server
# (restart Claude Desktop or your integration)
```

### Security Patch Policy

- **Critical vulnerabilities**: Immediate patch release
- **High severity**: Patch within 7 days
- **Medium/Low severity**: Included in next regular release

## Additional Resources

- [Google Ads API Security Best Practices](https://developers.google.com/google-ads/api/docs/best-practices/security)
- [OAuth 2.0 Security Best Current Practice](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Contact

For security-related questions or concerns:

- **Security Issues**: [GitHub Issues](https://github.com/johnoconnor0/google-ads-mcp/issues) (use "security" label)
- **Email**: open-source@weblifter.com.au
- **General Support**: See [README.md](README.md#support--resources)

---

**Last Updated**: December 17, 2025
