# Contributing to Google Ads MCP Server

Thank you for your interest in contributing to the Google Ads MCP Server! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Welcome](#welcome)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Development Guidelines](#development-guidelines)
- [Code Style](#code-style)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Code Review Criteria](#code-review-criteria)
- [Roadmap Alignment](#roadmap-alignment)
- [Questions and Support](#questions-and-support)

## Welcome

The Google Ads MCP Server aims to provide a comprehensive Model Context Protocol interface for the Google Ads API, enabling AI assistants to manage and optimize advertising campaigns through natural language.

**Project Mission**: Make Google Ads campaign management accessible and efficient through AI-powered natural language interfaces.

**Current Status**:
- **v1**: 10 core tools implemented (stable)
- **v2**: Roadmap for 161 additional tools across 14 functional domains

## Ways to Contribute

### Bug Reports

Found a bug? Help us fix it!

- **Search first**: Check if the issue already exists
- **Create an issue**: Use the bug report template
- **Include details**: Steps to reproduce, expected vs actual behavior, environment
- **Be specific**: Include error messages, logs, and screenshots if applicable

### Feature Requests

Have an idea for a new feature?

- **Check the roadmap**: See [IMPLEMENTATION_PLAN.md](documentation/IMPLEMENTATION_PLAN.md)
- **Search existing issues**: Your feature might already be planned
- **Create an issue**: Describe the use case and expected behavior
- **Discuss first**: For major features, open a discussion before implementation

### Code Contributions

Want to contribute code?

- **Start small**: Fix a bug or improve documentation
- **Check for assignments**: Look for issues labeled "good first issue" or "help wanted"
- **Discuss major changes**: Open an issue to discuss significant changes before coding
- **Follow guidelines**: Adhere to the code style and testing requirements

### Documentation Improvements

Documentation is crucial!

- **Fix typos**: Small fixes are always welcome
- **Improve clarity**: Rewrite confusing sections
- **Add examples**: Practical examples help users
- **Update outdated content**: Keep docs in sync with code

### Testing and Feedback

Help us improve quality!

- **Test new features**: Try out unreleased features and provide feedback
- **Report issues**: Let us know about problems you encounter
- **Suggest improvements**: Share ideas for better UX or functionality

## Getting Started

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/google-ads-mcp.git
   cd google-ads-mcp
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/johnoconnor0/google-ads-mcp.git
   ```

### Development Environment Setup

1. **Python version**: Python 3.8 or higher
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies** (if needed):
   ```bash
   pip install pytest black flake8 mypy
   ```

### Running the Server Locally

1. **Configure credentials**: See [README.md](README.md#setup--installation) for OAuth setup
2. **Set environment variables**:
   ```bash
   export GOOGLE_ADS_DEVELOPER_TOKEN="your-token"
   export GOOGLE_ADS_CLIENT_ID="your-client-id"
   export GOOGLE_ADS_CLIENT_SECRET="your-secret"
   export GOOGLE_ADS_REFRESH_TOKEN="your-refresh-token"
   ```
3. **Run the server**:
   ```bash
   python google_ads_mcp.py
   ```
4. **Test with Claude Desktop**: Configure `claude_desktop_config.json` to point to your local copy

### Testing Your Changes

1. **Manual testing**: Test with Claude Desktop or another MCP client
2. **Verify functionality**: Ensure your changes work as expected
3. **Check for regressions**: Make sure you haven't broken existing functionality
4. **Test edge cases**: Try unusual inputs and error conditions

## Development Guidelines

### Code Style

**Python PEP 8**

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use 4 spaces for indentation (not tabs)
- Maximum line length: 100 characters (slightly more flexible than PEP 8's 79)
- Use descriptive variable names

**Formatting**

- Use `black` for automatic code formatting:
  ```bash
  black google_ads_mcp.py
  ```
- Use `flake8` for linting:
  ```bash
  flake8 google_ads_mcp.py
  ```

**Type Hints**

- Use type hints for function signatures:
  ```python
  def get_campaign_performance(
      customer_id: str,
      date_range: DateRange = DateRange.LAST_30_DAYS,
      limit: int = 50
  ) -> dict[str, Any]:
      ...
  ```
- Use Pydantic models for complex data structures:
  ```python
  from pydantic import BaseModel, Field

  class CampaignConfig(BaseModel):
      name: str = Field(..., description="Campaign name")
      budget_micros: int = Field(..., gt=0)
      status: CampaignStatus = CampaignStatus.ENABLED
  ```

### Manager Module Structure

When creating new manager modules, follow this pattern:

```python
"""
Module: campaign_manager.py
Purpose: Campaign creation and management operations
"""

from typing import Optional, List, Dict, Any
from google.ads.googleads.client import GoogleAdsClient
from pydantic import BaseModel


class CampaignManager:
    """Handles campaign-related operations."""

    def __init__(self, client: GoogleAdsClient):
        """Initialize the campaign manager."""
        self.client = client

    def create_campaign(
        self,
        customer_id: str,
        campaign_name: str,
        budget_amount_micros: int,
        **kwargs
    ) -> dict[str, Any]:
        """Create a new campaign."""
        # Implementation
        pass
```

### MCP Tool Registration Pattern

Follow this pattern for registering MCP tools:

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("google_ads_mcp")

class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""
    customer_id: str = Field(..., description="Customer ID (10 digits, no hyphens)")
    campaign_name: str = Field(..., description="Campaign name")
    budget_amount_micros: int = Field(..., description="Daily budget in micros")

@mcp.tool()
def google_ads_create_campaign(request: CampaignCreateRequest) -> dict:
    """
    Create a new Google Ads campaign.

    Args:
        request: Campaign creation parameters

    Returns:
        Campaign creation result with resource name and ID
    """
    # Implementation
    pass
```

### Error Handling

**Use structured error handling**:

```python
from google.ads.googleads.errors import GoogleAdsException
from error_handler import ErrorHandler, ErrorCategory

error_handler = ErrorHandler()

try:
    # API operation
    response = client.service.mutate(...)
except GoogleAdsException as ex:
    return error_handler.handle_google_ads_error(ex, context={
        "operation": "create_campaign",
        "customer_id": customer_id
    })
except Exception as ex:
    return error_handler.handle_generic_error(
        ex,
        ErrorCategory.UNKNOWN,
        "Unexpected error creating campaign"
    )
```

**Provide helpful error messages**:

```python
# Bad
raise ValueError("Invalid input")

# Good
raise ValueError(
    f"Invalid customer_id: '{customer_id}'. "
    "Customer ID must be 10 digits without hyphens (e.g., '1234567890')"
)
```

## Commit Message Convention

Use conventional commits format: `type(scope): description`

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring (no functionality change)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config)
- `perf`: Performance improvements
- `style`: Code style changes (formatting, no logic change)

### Scope

Optional, indicates the affected component:
- `campaign`: Campaign-related changes
- `keyword`: Keyword-related changes
- `auth`: Authentication
- `config`: Configuration
- `docs`: Documentation
- `mcp`: MCP tool registration

### Examples

```
feat(campaign): add support for Performance Max campaigns
fix(auth): resolve refresh token expiration issue
docs(readme): add ChatGPT integration instructions
refactor(manager): simplify error handling in campaign_manager
test(keyword): add unit tests for keyword validation
chore(deps): update google-ads to v25.1.0
```

### Message Body (Optional)

For complex changes, add a detailed description:

```
feat(bidding): implement portfolio bidding strategies

- Add BiddingStrategyManager class
- Support Target CPA, Target ROAS, Maximize Conversions
- Implement bid adjustment logic
- Add MCP tool registration

Closes #42
```

## Pull Request Process

### Before Submitting

1. **Create a feature branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**: Follow the development guidelines

3. **Test thoroughly**: Ensure your changes work correctly

4. **Commit with clear messages**: Use conventional commit format

5. **Update documentation**: Update README, docstrings, or other docs if needed

6. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Submitting a Pull Request

1. **Push to your fork**:
   ```bash
   git push origin feat/your-feature-name
   ```

2. **Create pull request** on GitHub

3. **Write a clear PR description**:
   - What does this PR do?
   - Why is this change needed?
   - How has it been tested?
   - Related issues (use "Closes #123" to auto-close)

4. **Fill out the PR template** (if one exists)

5. **Request review**: Tag relevant reviewers

### PR Template Example

```markdown
## Description
Brief description of changes

## Motivation and Context
Why is this change necessary?

## How Has This Been Tested?
- [ ] Tested with Claude Desktop
- [ ] Manual testing with test account
- [ ] Unit tests (if applicable)

## Types of Changes
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Related issues linked
```

### After Submission

- **Respond to feedback**: Address code review comments promptly
- **Make requested changes**: Push updates to the same branch
- **Be patient**: Maintainers will review as soon as possible
- **Celebrate**: Your contribution makes a difference!

## Testing

### Manual Testing Checklist

When testing MCP tools:

- [ ] Tool initializes correctly
- [ ] Parameters are validated properly
- [ ] API calls succeed with valid inputs
- [ ] Error handling works with invalid inputs
- [ ] Response format is correct (Markdown/JSON)
- [ ] Edge cases are handled gracefully
- [ ] No sensitive data is logged
- [ ] Performance is acceptable

### Testing with Claude Desktop

1. Update `claude_desktop_config.json` to point to your development version
2. Restart Claude Desktop
3. Test the tool with natural language queries
4. Verify the output matches expectations
5. Test error scenarios

### Integration Testing

Test with a Google Ads test account:
- Use a test account (not production)
- Verify API operations don't cause unintended changes
- Check rate limiting and quota usage

## Code Review Criteria

Reviewers will evaluate:

### Functionality
- Does the code work as intended?
- Are edge cases handled?
- Is error handling robust?

### Code Quality
- Is the code readable and maintainable?
- Are variable/function names descriptive?
- Is there unnecessary complexity?
- Are there code smells?

### Documentation
- Are docstrings clear and complete?
- Is the README updated if needed?
- Are complex sections commented?

### Security
- Are credentials handled securely?
- Is input validated?
- Are there potential vulnerabilities?

### Performance
- Is the code efficient?
- Are there unnecessary API calls?
- Is caching used appropriately?

### Testing
- Has the code been tested?
- Are test cases comprehensive?
- Are edge cases covered?

## Roadmap Alignment

The project follows a phased development roadmap. See [IMPLEMENTATION_PLAN.md](documentation/IMPLEMENTATION_PLAN.md) for details.

### Priority System

- **Priority 1**: Core infrastructure and essential tools (completed)
- **Priority 2**: Campaign and ad management tools (in progress)
- **Priority 3**: Advanced features and optimization tools (planned)

### Current Phase

Check the implementation plan to see:
- What's currently being worked on
- What's planned next
- Where contributions are most needed

### Proposing New Tools

When proposing a new tool:

1. Check if it's already in the roadmap
2. Verify it's not a duplicate
3. Explain the use case and value
4. Consider which phase it fits into
5. Discuss implementation approach

## Questions and Support

### Getting Help

- **Documentation**: Start with [README.md](README.md) and other docs
- **Issues**: Search [existing issues](https://github.com/johnoconnor0/google-ads-mcp/issues) for similar questions
- **Discussions**: Open a [GitHub discussion](https://github.com/johnoconnor0/google-ads-mcp/discussions) for general questions
- **Email**: For private matters, contact open-source@weblifter.com.au

### Where to Ask

- **"How do I...?"**: [GitHub Discussions](https://github.com/johnoconnor0/google-ads-mcp/discussions)
- **"I found a bug"**: [GitHub Issues](https://github.com/johnoconnor0/google-ads-mcp/issues)
- **"I have a feature idea"**: [GitHub Discussions](https://github.com/johnoconnor0/google-ads-mcp/discussions) or [Issues](https://github.com/johnoconnor0/google-ads-mcp/issues)
- **"How can I contribute?"**: This guide or [email us](mailto:open-source@weblifter.com.au)

### Community Guidelines

- Be respectful and constructive
- Help others when you can
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md) (if one exists)
- Assume good intentions

## Recognition

Contributors will be:
- Credited in release notes
- Listed in a CONTRIBUTORS file (if created)
- Mentioned in relevant documentation
- Appreciated by the community!

---

**Thank you for contributing to the Google Ads MCP Server!**

Your contributions help make Google Ads management more accessible and efficient for everyone.

---

**Last Updated**: December 17, 2025
