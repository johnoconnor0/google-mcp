# Google Ads MCP Server

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![MCP SDK](https://img.shields.io/badge/MCP-1.1.0%2B-purple)
![Google Ads API](https://img.shields.io/badge/Google%20Ads%20API-v17%2B-red)
![Status](https://img.shields.io/badge/status-Active%20Development-orange)

A comprehensive Model Context Protocol (MCP) server for Google Ads API integration, enabling AI assistants like Claude, ChatGPT, and Gemini to analyze, manage, and optimize Google Ads campaigns through natural language conversations.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
  - [Current Features (v1)](#current-features-v1)
  - [Roadmap (v2)](#roadmap-v2)
- [Quick Start](#quick-start)
- [Setup & Installation](#setup--installation)
  - [Prerequisites](#prerequisites)
  - [Google Ads API Setup](#google-ads-api-setup)
  - [Server Installation](#server-installation)
  - [AI Integration](#ai-integration)
- [MCP Tool Reference](#mcp-tool-reference)
  - [v1 Tools (10 Current Tools)](#v1-tools-10-current-tools)
  - [v2 Roadmap (161 Planned Tools)](#v2-roadmap-161-planned-tools)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)
- [Citation](#citation)
- [Support & Resources](#support--resources)

## Overview

The Google Ads MCP Server transforms how you interact with Google Ads by providing a natural language interface powered by Model Context Protocol. Instead of navigating complex dashboards or writing custom API code, you can analyze campaigns, optimize keywords, and manage budgets through simple conversations with AI assistants.

**What is MCP?**

Model Context Protocol (MCP) is an open standard that enables AI assistants to securely connect with external data sources and tools. This server implements MCP to bridge AI assistants with the Google Ads API.

**Key Benefits:**

- **Natural Language Interface**: Ask questions and give commands in plain English
- **Multi-Platform Support**: Works with Claude Desktop, ChatGPT, Gemini, and other MCP-compatible AI assistants
- **Comprehensive Coverage**: From basic reporting to advanced campaign management
- **Secure**: OAuth 2.0 authentication with best-practice credential management
- **Extensible**: Modular architecture supporting 161 planned tools across 14 functional domains

## Features

### Current Features (v1)

The current stable release (v1) provides 10 essential tools for Google Ads analysis and management:

**Analysis & Reporting**
- List all accessible Google Ads accounts
- Campaign performance analysis with filtering and date ranges
- Keyword performance tracking (quality scores, positions, conversions)
- Search terms discovery (actual queries triggering ads)
- Ad group performance metrics
- Google's AI-powered optimization recommendations

**Campaign Management**
- Update campaign daily budgets
- Pause or enable campaigns
- Execute custom GAQL queries for advanced analysis

### Roadmap (v2)

The v2 roadmap expands the server to 161 tools across 14 functional domains, covering approximately 85% of the Google Ads API surface area for campaign management and optimization.

**Planned Capabilities:**

| Domain | Tools | Description |
|--------|-------|-------------|
| **Campaign Management** | 23 | Create, update, delete campaigns (all 9 types) |
| **Ad & Creative Management** | 18 | Responsive Search Ads, Display, Video, Performance Max |
| **Keyword Management** | 15 | Bulk operations, negative keywords, match types |
| **Bidding & Optimization** | 12 | Portfolio strategies, bid adjustments, automation |
| **Audience Management** | 14 | Remarketing, Customer Match, custom audiences |
| **Conversion Tracking** | 11 | Setup, offline imports, attribution |
| **Advanced Reporting** | 25 | Geographic, demographic, competitive insights |
| **Batch Operations** | 8 | Bulk uploads, mass updates, CSV import/export |
| **Extensions & Assets** | 12 | Sitelinks, callouts, structured snippets |
| **Shopping & PMax** | 10 | Product feeds, Performance Max campaigns |
| **Local & App Campaigns** | 8 | Store visits, app installs, local inventory |
| **Automation** | 10 | Automated rules, smart bidding, scripts integration |
| **Insights & Analytics** | 8 | Forecasting, auction insights, change history |
| **Labels & Organization** | 7 | Campaign labels, asset groups, organization |

**Total: 161 tools** covering end-to-end campaign lifecycle management.

See [IMPLEMENTATION_PLAN.md](documentation/IMPLEMENTATION_PLAN.md) for the complete roadmap.

## Quick Start

Get up and running in 5 minutes:

### Prerequisites

- Python 3.8 or higher
- Google Ads account with active campaigns
- Google Ads API Developer Token ([apply here](https://developers.google.com/google-ads/api/docs/get-started/dev-token))

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/johnoconnor0/google-ads-mcp.git
   cd google-ads-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate OAuth credentials** (see [Google Ads API Setup](#google-ads-api-setup) for details):
   ```bash
   python generate_refresh_token.py
   ```

4. **Configure Claude Desktop** (or your preferred AI assistant):

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

   ```json
   {
     "mcpServers": {
       "google-ads": {
         "command": "python",
         "args": ["/absolute/path/to/google_ads_mcp.py"],
         "env": {}
       }
     }
   }
   ```

5. **Restart Claude Desktop** and start asking questions about your Google Ads accounts!

### First Steps

Once configured, try these commands in Claude Desktop:

```
"Initialize my Google Ads connection with these credentials..."
"Show me all my Google Ads accounts"
"Analyze campaign performance for the last 30 days"
"Which keywords have the lowest quality scores?"
```

See [Usage Examples](#usage-examples) for more.

## Setup & Installation

### Prerequisites

#### Required

- **Python**: Version 3.8 or higher
  ```bash
  python --version  # Should output 3.8 or higher
  ```

- **Google Ads Account**: Active account with campaigns
- **Google Ads API Access**: Developer token (may take 24-48 hours for approval)
- **OAuth 2.0 Credentials**: Client ID and Client Secret from Google Cloud Console

#### Optional

- **MCC Account**: For managing multiple client accounts
- **Redis**: For distributed caching (optional, defaults to in-memory cache)

### Google Ads API Setup

#### Step 1: Apply for Developer Token

1. Sign in to your Google Ads account
2. Navigate to **Tools & Settings** → **Setup** → **API Center**
3. Apply for a developer token
4. Wait for approval (typically 24-48 hours)
5. **Important**: Test developer tokens work immediately but have limitations

**Resource**: [Google Ads API Developer Token Guide](https://developers.google.com/google-ads/api/docs/get-started/dev-token)

#### Step 2: Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Ads API**:
   - Navigation → **APIs & Services** → **Library**
   - Search for "Google Ads API"
   - Click "Enable"
4. Create OAuth credentials:
   - **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - Choose **Desktop app** as application type
   - Name your OAuth client (e.g., "Google Ads MCP Server")
   - Click **Create**
5. **Download** your credentials or copy:
   - **Client ID** (ends with `.apps.googleusercontent.com`)
   - **Client Secret**

**Resource**: [OAuth 2.0 Setup Guide](https://developers.google.com/google-ads/api/docs/oauth/overview)

#### Step 3: Generate Refresh Token

Use the provided utility script to generate a refresh token:

```bash
python generate_refresh_token.py
```

**What this script does**:
1. Opens a browser for Google authorization
2. You grant access to your Google Ads account
3. Generates a **refresh token** (long-lived credential)
4. Displays the refresh token to copy

**Alternative manual method**:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = 'your-client-id.apps.googleusercontent.com'
CLIENT_SECRET = 'your-client-secret'
SCOPES = ['https://www.googleapis.com/auth/adwords']

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=SCOPES
)

credentials = flow.run_local_server(port=0)
print(f"Refresh Token: {credentials.refresh_token}")
```

**Important**: Store your refresh token securely! It provides ongoing access to your Google Ads account.

### Server Installation

#### Install Python Dependencies

**Option 1: Install from requirements.txt** (recommended):

```bash
pip install -r requirements.txt
```

**Option 2: Manual installation**:

```bash
pip install google-ads>=25.0.0 mcp>=1.1.0 httpx>=0.27.0 pydantic>=2.0.0 google-auth-oauthlib>=1.0.0
```

**Optional dependencies** (for advanced features):

```bash
# Caching with Redis
pip install redis>=5.0.0

# Export and reporting
pip install openpyxl>=3.1.2 reportlab>=4.0.0 matplotlib>=3.8.0
```

#### Verify Installation

```bash
python -c "import google.ads.googleads, mcp, httpx, pydantic; print('All dependencies installed successfully!')"
```

### AI Integration

The Google Ads MCP Server can be integrated with multiple AI platforms:

#### Claude Desktop Integration

**Recommended for**: Most users, easiest setup

1. **Locate configuration file**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add MCP server configuration**:

   ```json
   {
     "mcpServers": {
       "google-ads": {
         "command": "python",
         "args": ["/absolute/path/to/google_ads_mcp.py"],
         "env": {}
       }
     }
   }
   ```

   Replace `/absolute/path/to/google_ads_mcp.py` with the actual file path.

3. **Restart Claude Desktop** for changes to take effect

4. **Initialize the connection** in Claude:
   ```
   Initialize my Google Ads connection with these credentials:
   - Developer Token: YOUR_DEV_TOKEN
   - Client ID: YOUR_CLIENT_ID.apps.googleusercontent.com
   - Client Secret: YOUR_CLIENT_SECRET
   - Refresh Token: YOUR_REFRESH_TOKEN
   - Login Customer ID: YOUR_MCC_ID (optional, only if using MCC)
   ```

**Resources**:
- [Claude Desktop MCP Documentation](https://github.com/anthropics/claude-desktop)
- [QUICKSTART.md](documentation/QUICKSTART.md)

#### ChatGPT Integration

**Status**: Experimental (MCP support via third-party tools)

ChatGPT does not natively support MCP as of December 2025. However, integration is possible via:

**Option 1: MCP Bridge** (if available)
- Use an MCP-to-OpenAI API bridge
- Configure the bridge to expose Google Ads MCP tools as OpenAI functions
- Access via ChatGPT Plus with plugin support

**Option 2: Custom GPT with API Wrapper**
- Create a web API wrapper around the MCP server
- Build a Custom GPT with function calling to your API
- Configure authentication and endpoints

**Option 3: Use Claude Code or API**
- Run the MCP server with Claude Code (CLI)
- Use Claude API to access the MCP tools programmatically
- Integrate results into your ChatGPT workflow

**Note**: As ChatGPT's MCP support evolves, this section will be updated with native integration instructions.

#### Gemini Integration

**Status**: Experimental (MCP support via third-party tools)

Google's Gemini does not natively support MCP as of December 2025. However, integration is possible via:

**Option 1: Vertex AI Function Calling**
- Deploy the MCP server as a Google Cloud Function or Cloud Run service
- Use Vertex AI's function calling with Gemini
- Map MCP tools to Gemini function definitions

**Option 2: LangChain Integration**
- Use LangChain to create a bridge between Gemini and MCP tools
- Define MCP tools as LangChain tools
- Create a Gemini agent with MCP tool access

**Option 3: Custom Integration**
- Build a REST API wrapper around the MCP server
- Use Gemini API with function calling
- Map Google Ads operations to function definitions

**Resources**:
- [Vertex AI Function Calling](https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/function-calling)
- [Gemini API Documentation](https://ai.google.dev/docs)

#### Other MCP-Compatible Platforms

The server works with any MCP-compatible client. See the [MCP Documentation](https://modelcontextprotocol.io) for integration guides.

## MCP Tool Reference

### v1 Tools (10 Current Tools)

The current stable release provides these tools:

---

#### 1. `google_ads_initialize`

**Description**: Initialize API connection with OAuth credentials.

**Parameters**:
```json
{
  "developer_token": "string (required)",
  "client_id": "string (required)",
  "client_secret": "string (required)",
  "refresh_token": "string (required)",
  "login_customer_id": "string (optional)"
}
```

**Example**:
```
Initialize with:
- Developer Token: abc123...
- Client ID: 123456789.apps.googleusercontent.com
- Client Secret: xyz789...
- Refresh Token: 1//abc...
- Login Customer ID: 1234567890 (only for MCC accounts)
```

**Returns**: Confirmation message with API version and accessibility check

---

#### 2. `google_ads_list_accounts`

**Description**: List all accessible Google Ads accounts.

**Parameters**:
```json
{
  "response_format": "markdown | json (default: markdown)"
}
```

**Example**:
```
"Show me all my Google Ads accounts"
"List accounts in JSON format"
```

**Returns**: Account list with customer IDs, names, and descriptive names

---

#### 3. `google_ads_campaign_performance`

**Description**: Get comprehensive campaign metrics with filtering and date ranges.

**Parameters**:
```json
{
  "customer_id": "string (required, 10 digits no hyphens)",
  "date_range": "TODAY | YESTERDAY | LAST_7_DAYS | LAST_30_DAYS | etc. (default: LAST_30_DAYS)",
  "campaign_status": "ENABLED | PAUSED | REMOVED (optional)",
  "min_cost": "number (optional, in account currency)",
  "limit": "number (default: 50, max: 100)",
  "response_format": "markdown | json (default: markdown)"
}
```

**Example**:
```
"Show campaign performance for the last 30 days for account 1234567890"
"Find campaigns with at least $100 in spend this month"
"Show only enabled campaigns for account 1234567890"
```

**Returns**: Campaign metrics including impressions, clicks, cost, conversions, CTR, CPC, conversion rate

---

#### 4. `google_ads_keyword_performance`

**Description**: Analyze keyword-level performance with quality scores and positions.

**Parameters**:
```json
{
  "customer_id": "string (required)",
  "campaign_id": "string (optional)",
  "date_range": "string (default: LAST_30_DAYS)",
  "min_impressions": "number (optional)",
  "limit": "number (default: 50)",
  "response_format": "markdown | json"
}
```

**Example**:
```
"Analyze keyword performance for campaign 12345"
"Show keywords with quality score below 5"
"Find keywords with the highest cost per conversion"
```

**Returns**: Keyword metrics including quality score, average position, impressions, clicks, cost, conversions

---

#### 5. `google_ads_search_terms`

**Description**: Get actual search queries that triggered your ads.

**Parameters**:
```json
{
  "customer_id": "string (required)",
  "campaign_id": "string (optional)",
  "date_range": "string (default: LAST_30_DAYS)",
  "min_impressions": "number (default: 10)",
  "limit": "number (default: 50)",
  "response_format": "markdown | json"
}
```

**Example**:
```
"What search terms triggered my ads in the last 30 days?"
"Find high-impression search terms with low CTR"
"Show search terms for campaign 67890"
```

**Returns**: Search term, match type, impressions, clicks, cost, conversions, CTR

---

#### 6. `google_ads_ad_group_performance`

**Description**: Analyze ad group-level metrics.

**Parameters**:
```json
{
  "customer_id": "string (required)",
  "campaign_id": "string (optional)",
  "date_range": "string (default: LAST_30_DAYS)",
  "limit": "number (default: 50)",
  "response_format": "markdown | json"
}
```

**Example**:
```
"Show ad group performance for all campaigns"
"Find best-performing ad groups in campaign 12345"
```

**Returns**: Ad group metrics including impressions, clicks, cost, conversions, CTR, CPC

---

#### 7. `google_ads_recommendations`

**Description**: Get Google's AI-powered optimization suggestions.

**Parameters**:
```json
{
  "customer_id": "string (required)",
  "recommendation_types": "array of strings (optional)",
  "limit": "number (default: 20)",
  "response_format": "markdown | json"
}
```

**Example**:
```
"Show optimization recommendations for account 1234567890"
"What does Google suggest for improving my campaigns?"
```

**Returns**: Recommendation type, impact estimate, suggested changes, rationale

---

#### 8. `google_ads_update_campaign_budget`

**Description**: Modify campaign daily budget.

**Parameters**:
```json
{
  "customer_id": "string (required)",
  "campaign_id": "string (required)",
  "budget_amount_micros": "number (required, in micros)"
}
```

**Budget conversion**: Multiply your budget by 1,000,000
- $10.00 = 10,000,000 micros
- $50.50 = 50,500,000 micros
- $100.00 = 100,000,000 micros

**Example**:
```
"Set campaign 12345 budget to $75 per day"
"Increase budget for campaign 67890 to 100,000,000 micros ($100)"
```

**Returns**: Confirmation with old and new budget values

---

#### 9. `google_ads_update_campaign_status`

**Description**: Pause or enable campaigns.

**Parameters**:
```json
{
  "customer_id": "string (required)",
  "campaign_id": "string (required)",
  "status": "ENABLED | PAUSED (required)"
}
```

**Example**:
```
"Pause campaign 12345"
"Enable campaign 67890"
```

**Returns**: Confirmation with new status

---

#### 10. `google_ads_custom_query`

**Description**: Execute custom GAQL (Google Ads Query Language) queries.

**Parameters**:
```json
{
  "customer_id": "string (required)",
  "query": "string (required, valid GAQL query)",
  "response_format": "markdown | json"
}
```

**Example**:
```
"Execute this GAQL query: SELECT campaign.name, metrics.clicks FROM campaign WHERE metrics.impressions > 1000"
```

**Resources**:
- [GAQL Query Builder](https://developers.google.com/google-ads/api/fields/latest/overview_query_builder)
- [GAQL Documentation](https://developers.google.com/google-ads/api/docs/query/overview)

**Returns**: Query results in requested format

---

### v2 Roadmap (161 Planned Tools)

The v2 implementation expands the server to 161 tools across 14 domains. Below is a summary of planned capabilities.

#### Campaign Management (23 tools)

**Creation & Configuration**:
- Create campaigns (all 9 types: Search, Display, Shopping, Video, Performance Max, App, Local, Smart, Demand Gen)
- Configure networks, locations, languages, start/end dates
- Set up budgets (standard, shared, portfolio)
- Configure bidding strategies

**Updates & Optimization**:
- Modify campaign settings (name, networks, targeting)
- Update location and language targeting
- Manage device bid adjustments
- Configure ad scheduling (dayparting)
- Add campaign-level exclusions

**Management**:
- Campaign experiments and A/B testing
- Campaign labels and organization
- Campaign deletion and archival

**Status**: Priority 2 - In active development

---

#### Ad & Creative Management (18 tools)

**Ad Creation**:
- Responsive Search Ads (RSA) - up to 15 headlines, 4 descriptions
- Expanded Text Ads (legacy)
- Responsive Display Ads
- Image ads (Display Network)
- Video ads (YouTube, TrueView)
- Performance Max asset groups

**Ad Optimization**:
- Ad copy testing and analysis
- Ad strength tracking
- Creative asset management
- Ad preview and testing

**Status**: Priority 2 - Planned

---

#### Keyword Management (15 tools)

**Keyword Operations**:
- Bulk keyword addition (CSV import)
- Keyword updates (match types, bids, status)
- Keyword deletion
- Negative keyword management
- Negative keyword lists (shared)

**Keyword Research & Analysis**:
- Keyword forecasting
- Keyword suggestions
- Match type optimization
- Quality score tracking and improvement

**Status**: Priority 2 - Planned

---

#### Bidding & Optimization (12 tools)

**Bidding Strategies**:
- Portfolio bidding strategies (Target CPA, Target ROAS, Maximize Conversions)
- Bid adjustments (device, location, demographics, audiences, time-of-day)
- Manual bidding configuration
- Smart Bidding setup and monitoring

**Optimization**:
- Automated rules and triggers
- Bid simulation and forecasting
- Performance optimization suggestions

**Status**: Priority 2 - Planned

---

#### Audience Management (14 tools)

**Audience Creation**:
- Remarketing lists
- Customer Match audience uploads
- Custom audiences (interests, behaviors)
- Similar audiences (lookalikes)
- In-market and affinity audiences

**Audience Targeting**:
- Apply audiences to campaigns/ad groups
- Audience bid adjustments
- Exclusion lists
- Audience performance tracking

**Status**: Priority 3 - Planned

---

#### Conversion Tracking (11 tools)

**Setup & Configuration**:
- Create conversion actions
- Configure conversion tracking tags
- Import offline conversions
- Set up call tracking

**Attribution & Analysis**:
- Multi-touch attribution models
- Conversion value rules
- Conversion lift studies
- Cross-device conversion tracking

**Status**: Priority 3 - Planned

---

#### Advanced Reporting (25 tools)

**Specialized Reports**:
- Geographic performance (country, region, city, postal code)
- Demographic reports (age, gender, household income)
- Time-based analysis (hour of day, day of week)
- Device performance breakdown
- Auction insights (competitive analysis)
- Landing page performance
- Call metrics and call tracking
- Video performance (YouTube)
- Shopping performance (product groups)

**Report Customization**:
- Custom report builder
- Period-over-period comparison
- Trend analysis
- Export to Excel/PDF/CSV
- Scheduled reports

**Status**: Priority 2-3 - Partially planned

---

#### Batch Operations (8 tools)

**Bulk Operations**:
- Batch campaign creation
- Bulk keyword uploads (CSV)
- Mass ad group creation
- Bulk status changes
- Batch budget updates

**Import/Export**:
- Google Ads Editor CSV import
- Export campaigns to CSV
- Bulk change history

**Status**: Priority 3 - Planned

---

#### Extensions & Assets (12 tools)

**Extension Types**:
- Sitelink extensions
- Callout extensions
- Call extensions
- Location extensions
- Price extensions
- Structured snippet extensions
- Promotion extensions
- App extensions

**Management**:
- Extension performance tracking
- Asset library management
- Extension scheduling
- Extension bid adjustments

**Status**: Priority 3 - Planned

---

#### Shopping & Performance Max (10 tools)

**Shopping Campaigns**:
- Product feed management
- Product group creation
- Shopping campaign optimization
- Merchant Center integration

**Performance Max**:
- Asset group creation
- Audience signals
- Performance tracking
- Budget optimization

**Status**: Priority 3 - Planned

---

#### Local & App Campaigns (8 tools)

**Local Campaigns**:
- Store visits tracking
- Local inventory ads
- Location-based bidding
- Call tracking

**App Campaigns**:
- App install campaigns
- App engagement campaigns
- Deep link configuration
- In-app event tracking

**Status**: Priority 3 - Planned

---

#### Automation (10 tools)

**Automated Rules**:
- Create custom rules
- Schedule automated tasks
- Trigger-based actions
- Rule performance tracking

**Smart Features**:
- Smart Bidding automation
- Automated extensions
- Dynamic ad customization
- AI-powered optimization

**Status**: Priority 3 - Planned

---

#### Insights & Analytics (8 tools)

**Forecasting**:
- Budget forecasting
- Conversion forecasting
- Seasonal trend analysis
- Growth projections

**Competitive Analysis**:
- Auction insights
- Competitive benchmarking
- Market share analysis

**Change History**:
- Account change log
- Performance change attribution
- Rollback capabilities

**Status**: Priority 3 - Planned

---

#### Labels & Organization (7 tools)

**Labels**:
- Campaign labels
- Ad group labels
- Keyword labels
- Ad labels

**Organization**:
- Folder structure management
- Resource organization
- Bulk label operations

**Status**: Priority 3 - Planned

---

For the complete implementation plan with technical details, see [IMPLEMENTATION_PLAN.md](documentation/IMPLEMENTATION_PLAN.md).

## Usage Examples

### Claude Desktop Conversations

#### Account Overview

```
User: "Show me all my Google Ads accounts"

Claude: [Calls google_ads_list_accounts]
I can see you have 3 accessible Google Ads accounts:
1. Account 123-456-7890 (My Business)
2. Account 234-567-8901 (E-commerce Store)
3. Account 345-678-9012 (Client ABC)
```

#### Campaign Analysis

```
User: "Analyze campaign performance for the last 30 days for my main account"

Claude: [Calls google_ads_campaign_performance with customer_id="1234567890"]
Here's the performance for your campaigns over the last 30 days:

Top Performers:
- Brand Campaign: $1,245 spent, 523 conversions, $2.38 CPA
- Shopping Campaign: $2,100 spent, 312 conversions, $6.73 CPA

Needs Attention:
- Generic Keywords: $850 spent, 12 conversions, $70.83 CPA (consider pausing)
```

#### Keyword Optimization

```
User: "Show me keywords with quality score below 5 for campaign 12345"

Claude: [Calls google_ads_keyword_performance with filtering]
Found 8 keywords with quality scores below 5:

1. "cheap widgets" - QS: 3, Avg Pos: 4.2, $145 spent
   Suggestion: Improve ad relevance or pause
2. "buy widgets online" - QS: 4, Avg Pos: 3.8, $98 spent
   Suggestion: Create dedicated ad group with tailored ad copy
...
```

#### Budget Management

```
User: "Increase the budget for campaign 67890 to $150 per day"

Claude: [Calls google_ads_update_campaign_budget with budget_amount_micros=150000000]
Budget updated successfully:
- Campaign: Summer Sale 2025
- Old Budget: $100.00/day
- New Budget: $150.00/day
- Effective: Immediately
```

#### Search Terms Discovery

```
User: "What search terms are triggering my ads with high impressions but low CTR?"

Claude: [Calls google_ads_search_terms with analysis]
Found 15 search terms with >1000 impressions and CTR <1%:

High Priority:
1. "free widgets" - 5,234 impressions, 0.3% CTR
   Recommendation: Add as negative keyword
2. "how to make widgets" - 3,421 impressions, 0.5% CTR
   Recommendation: Add as negative keyword (informational intent)
```

### Programmatic Usage

If integrating directly with the MCP server programmatically:

```python
from mcp import ClientSession
import asyncio

async def analyze_campaigns():
    async with ClientSession() as session:
        # Initialize connection
        await session.call_tool("google_ads_initialize", {
            "developer_token": "YOUR_TOKEN",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_SECRET",
            "refresh_token": "YOUR_REFRESH_TOKEN"
        })

        # Get campaign performance
        result = await session.call_tool("google_ads_campaign_performance", {
            "customer_id": "1234567890",
            "date_range": "LAST_7_DAYS",
            "response_format": "json"
        })

        print(result)

asyncio.run(analyze_campaigns())
```

## Configuration

### Configuration File (config.yaml)

The v2 server supports configuration via YAML files:

```yaml
authentication:
  method: oauth2  # or service_account
  developer_token: ${GOOGLE_ADS_DEVELOPER_TOKEN}
  client_id: ${GOOGLE_ADS_CLIENT_ID}
  client_secret: ${GOOGLE_ADS_CLIENT_SECRET}
  refresh_token: ${GOOGLE_ADS_REFRESH_TOKEN}
  login_customer_id: ${GOOGLE_ADS_LOGIN_CUSTOMER_ID}  # Optional MCC

performance:
  cache:
    backend: memory  # Options: memory, redis, none
    ttl:
      accounts: 3600      # 1 hour
      campaigns: 300      # 5 minutes
      keywords: 300       # 5 minutes
      search_terms: 600   # 10 minutes
    redis_url: redis://localhost:6379/0  # If using Redis
    max_size: 1000  # For memory cache

  connection_pool:
    size: 10
    timeout: 30

  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_size: 10

error_handling:
  retry:
    enabled: true
    max_attempts: 3
    backoff_strategy: exponential  # linear, exponential
    initial_delay: 1
    max_delay: 30

  alerts:
    webhook_url: https://your-webhook.com/alerts
    email: admin@example.com

  log_errors: true

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: json  # json, text
  file: /var/log/google-mcp/server.log
  console: true

features:
  batch_operations: true
  auto_recommendations: true
  advanced_reporting: true
  conversion_tracking: true
  audience_management: true

api_version: v17  # Google Ads API version
default_page_size: 50
character_limit: 25000  # MCP response size limit
```

### Environment Variables

Override configuration with environment variables:

```bash
# Authentication
export GOOGLE_ADS_DEVELOPER_TOKEN="your-token"
export GOOGLE_ADS_CLIENT_ID="your-client-id"
export GOOGLE_ADS_CLIENT_SECRET="your-secret"
export GOOGLE_ADS_REFRESH_TOKEN="your-refresh-token"
export GOOGLE_ADS_LOGIN_CUSTOMER_ID="1234567890"  # Optional

# Performance
export GOOGLE_MCP_CACHE_BACKEND="redis"
export GOOGLE_MCP_REDIS_URL="redis://localhost:6379/0"

# Logging
export GOOGLE_MCP_LOG_LEVEL="DEBUG"
export GOOGLE_MCP_LOG_FILE="/var/log/google-mcp.log"
```

### Feature Flags

Enable or disable features:

```yaml
features:
  batch_operations: true      # Bulk operations support
  auto_recommendations: true  # Google AI recommendations
  advanced_reporting: true    # 25+ specialized reports
  conversion_tracking: true   # Conversion management
  audience_management: true   # Remarketing, Customer Match
```

### Caching Options

**Memory Cache** (default, no setup required):
- Fast, in-process caching
- No external dependencies
- Limited to single process

**Redis Cache** (recommended for production):
- Distributed caching across processes
- Persistent cache across restarts
- Supports clustering

**No Cache**:
- Disable caching for testing or debugging

## Architecture

### Project Structure

```
google-mcp/
├── google_ads_mcp.py              # Main MCP server (v1) - 10 tools
├── google_ads_mcp_v2.py           # Enhanced server (v2) - 161 planned tools
├── generate_refresh_token.py      # OAuth token generation utility
│
├── Infrastructure Managers
├── auth_manager.py                # OAuth authentication & token management
├── config_manager.py              # Configuration loading (YAML/JSON)
├── cache_manager.py               # Caching layer (Memory/Redis)
├── error_handler.py               # Error handling & retry logic
├── logger.py                      # Structured logging
├── response_handler.py            # Response formatting & streaming
├── query_optimizer.py             # GAQL query optimization
│
├── Domain Managers
├── campaign_manager.py            # Campaign creation & management
├── ad_group_manager.py            # Ad group operations
├── ad_manager.py                  # Ad creation & management
├── keyword_manager.py             # Keyword operations
├── bidding_strategy_manager.py    # Bidding strategy configuration
├── audience_manager.py            # Audience management
├── conversion_manager.py          # Conversion tracking
├── automation_manager.py          # Automated rules
├── batch_operations_manager.py    # Bulk operations
├── extensions_manager.py          # Ad extensions
├── labels_manager.py              # Label management
├── shopping_pmax_manager.py       # Shopping & Performance Max
├── local_app_manager.py           # Local & app campaigns
├── insights_manager.py            # Analytics & insights
├── reporting_manager.py           # Advanced reporting
│
├── MCP Tool Registrations
├── mcp_tools_campaigns.py         # Campaign tools
├── mcp_tools_ad_groups.py         # Ad group tools
├── mcp_tools_ads.py               # Ad tools
├── mcp_tools_keywords.py          # Keyword tools
├── mcp_tools_bidding.py           # Bidding tools
├── mcp_tools_audiences.py         # Audience tools
├── mcp_tools_conversions.py       # Conversion tools
├── mcp_tools_automation.py        # Automation tools
├── mcp_tools_batch.py             # Batch operation tools
├── mcp_tools_extensions.py        # Extension tools
├── mcp_tools_shopping_pmax.py     # Shopping/PMax tools
├── mcp_tools_local_app.py         # Local/App tools
├── mcp_tools_insights.py          # Insights tools
├── mcp_tools_reporting.py         # Reporting tools
│
├── Configuration
├── config.yaml                    # Server configuration
├── config.example.yaml            # Configuration template
├── requirements.txt               # Python dependencies
│
├── Documentation
├── README.md                      # This file
├── SECURITY.md                    # Security policy
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # MIT License
├── CITATION.cff                   # Citation information
├── CODEOWNERS                     # Code ownership
├── documentation/                 # Additional documentation
│   ├── QUICKSTART.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── EXECUTIVE_SUMMARY.md
│   └── ...
│
└── .claude/                       # Claude Code configuration
    ├── claude_project.json
    └── CLAUDE.md
```

### Manager Module Pattern

Each domain manager follows this pattern:

```python
class CampaignManager:
    """Handles campaign-related operations."""

    def __init__(self, client: GoogleAdsClient, config: Config):
        self.client = client
        self.config = config

    def create_campaign(...) -> dict:
        """Create a new campaign."""
        # Validation
        # API operation
        # Error handling
        # Response formatting
```

### MCP Tool Registration System

Tools are registered using FastMCP:

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("google_ads_mcp")

@mcp.tool()
def google_ads_create_campaign(request: CampaignCreateRequest) -> dict:
    """Create a new Google Ads campaign."""
    manager = CampaignManager(client, config)
    return manager.create_campaign(**request.dict())
```

### Data Flow

1. **AI Assistant** sends natural language request
2. **MCP Server** receives tool call with parameters
3. **Manager Module** validates input and executes API operation
4. **Google Ads API** processes the request
5. **Response Handler** formats the result (Markdown/JSON)
6. **MCP Server** returns the formatted response
7. **AI Assistant** presents the result to the user

## Troubleshooting

### Common Errors

#### "Client not initialized" Error

**Cause**: The Google Ads client hasn't been initialized with credentials.

**Solution**:
```
Initialize my Google Ads connection with these credentials:
- Developer Token: YOUR_TOKEN
- Client ID: YOUR_CLIENT_ID
- Client Secret: YOUR_SECRET
- Refresh Token: YOUR_REFRESH_TOKEN
```

#### "Invalid customer ID" Error

**Cause**: Customer ID format is incorrect.

**Solution**: Ensure customer IDs are:
- 10 digits
- Without hyphens
- Example: `1234567890` (correct), `123-456-7890` (wrong)

#### "Authentication failed" Error

**Causes and solutions**:

1. **Developer token invalid**:
   - Verify token in Google Ads API Center
   - Ensure token is approved (not test-only)

2. **OAuth credentials incorrect**:
   - Regenerate refresh token
   - Verify Client ID and Client Secret

3. **Token expired**:
   - Refresh tokens can expire after prolonged inactivity
   - Generate a new refresh token

4. **Wrong login_customer_id**:
   - Only use `login_customer_id` for MCC accounts
   - Verify the MCC ID is correct

#### "Insufficient permissions" Error

**Causes**:
- Your Google account doesn't have access to the Google Ads account
- Developer token has limited access level
- OAuth scope doesn't include Google Ads API

**Solution**:
1. Verify account access in Google Ads
2. Ensure OAuth scope is `https://www.googleapis.com/auth/adwords`
3. Check developer token access level

#### Rate Limiting

**Cause**: Exceeded Google Ads API rate limits.

**Solutions**:
- Reduce request frequency
- Use smaller date ranges
- Enable caching (Memory or Redis)
- Implement request throttling

**Google Ads API Limits**:
- 15,000 operations per day (test accounts)
- Higher limits for production accounts
- Contact Google for increased limits

### Debug Logging

Enable debug logging for troubleshooting:

**v1 (google_ads_mcp.py)**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**v2 (config.yaml)**:
```yaml
logging:
  level: DEBUG
  console: true
  file: /tmp/google-mcp-debug.log
```

### Testing Connections

Test your setup manually:

```python
from google.ads.googleads.client import GoogleAdsClient

credentials = {
    "developer_token": "YOUR_TOKEN",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_SECRET",
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "use_proto_plus": True
}

client = GoogleAdsClient.load_from_dict(credentials)
customer_service = client.get_service("CustomerService")
accessible_customers = customer_service.list_accessible_customers()
print(f"Accessible customers: {accessible_customers.resource_names}")
```

### Getting Help

If you're still stuck:

1. **Check existing issues**: [GitHub Issues](https://github.com/johnoconnor0/google-ads-mcp/issues)
2. **Review documentation**: [Google Ads API Docs](https://developers.google.com/google-ads/api/docs)
3. **Create an issue**: Provide error messages, logs, and steps to reproduce
4. **Contact support**: See [Support & Resources](#support--resources)

## Advanced Topics

### Multi-Account (MCC) Management

**What is MCC?**

MCC (My Client Center) is a Google Ads manager account that lets you manage multiple client accounts from a single interface.

**Setup**:
1. Create an MCC account at [ads.google.com/mcc](https://ads.google.com/mcc)
2. Link client accounts to your MCC
3. Use MCC customer ID as `login_customer_id` during initialization

**Usage**:
```
Initialize with:
- Login Customer ID: 1234567890 (your MCC ID)
- ...other credentials...

Then access client accounts:
"Analyze campaigns for client account 2345678901"
"List all accounts under my MCC"
```

**Benefits**:
- Single authentication for multiple accounts
- Centralized reporting across clients
- Efficient bulk operations

### Performance Optimization

**Caching Strategies**:

1. **Memory Cache**: Fast, but limited to single process
2. **Redis Cache**: Distributed, persistent, recommended for production
3. **Selective Caching**: Cache expensive queries, refresh on mutations

**Best Practices**:
- Use date range filters to reduce data volume
- Apply `limit` parameters to control result size
- Enable caching for frequently accessed data
- Use batch operations for bulk changes

### Custom GAQL Queries

GAQL (Google Ads Query Language) enables advanced custom queries.

**Query Structure**:
```sql
SELECT
  resource.field1,
  resource.field2,
  metrics.metric1
FROM resource_name
WHERE conditions
ORDER BY field
LIMIT n
```

**Example - Find top-performing keywords**:
```sql
SELECT
  ad_group_criterion.keyword.text,
  metrics.clicks,
  metrics.conversions,
  metrics.cost_micros
FROM keyword_view
WHERE
  metrics.impressions > 100
  AND campaign.status = 'ENABLED'
ORDER BY metrics.conversions DESC
LIMIT 20
```

**Resources**:
- [Query Builder](https://developers.google.com/google-ads/api/fields/latest/overview_query_builder)
- [Query Validator](https://developers.google.com/google-ads/api/docs/query/validate)
- [GAQL Grammar](https://developers.google.com/google-ads/api/docs/query/grammar)

### Batch Operations

Efficiently make bulk changes using batch operations (v2 feature):

**Benefits**:
- Reduce API calls (1 batch vs. 100 individual calls)
- Faster execution
- Lower quota usage

**Use Cases**:
- Bulk keyword uploads
- Mass campaign creation
- Batch budget updates
- Bulk status changes

## API Reference

### Google Ads API

- **Documentation**: [Google Ads API Docs](https://developers.google.com/google-ads/api/docs)
- **Reference**: [API Reference](https://developers.google.com/google-ads/api/reference)
- **Field Guide**: [Field Reference](https://developers.google.com/google-ads/api/fields/latest/overview)
- **Release Notes**: [What's New](https://developers.google.com/google-ads/api/docs/release-notes)

### GAQL Resources

- **Query Builder**: [Interactive Query Builder](https://developers.google.com/google-ads/api/fields/latest/overview_query_builder)
- **Query Validator**: [Validate Queries](https://developers.google.com/google-ads/api/docs/query/validate)
- **Query Grammar**: [GAQL Grammar Reference](https://developers.google.com/google-ads/api/docs/query/grammar)

### MCP Protocol

- **Specification**: [MCP Specification](https://modelcontextprotocol.io/specification)
- **Documentation**: [MCP Docs](https://modelcontextprotocol.io)
- **GitHub**: [MCP GitHub](https://github.com/modelcontextprotocol)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute**:
- Report bugs or request features via [GitHub Issues](https://github.com/johnoconnor0/google-ads-mcp/issues)
- Submit pull requests for bug fixes or new features
- Improve documentation
- Share usage examples and tips

**Development workflow**:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.

## Security

Security is a top priority. Please see [SECURITY.md](SECURITY.md) for:

- Security policy and supported versions
- How to report vulnerabilities
- Security best practices
- Credential management guidelines

**Quick security tips**:
- Never commit credentials to version control
- Use environment variables for secrets
- Rotate OAuth tokens regularly
- Enable 2FA on Google Ads accounts
- Monitor API access logs

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

```
MIT License

Copyright (c) 2025 John O'Connor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

## Citation

If you use this software in your research or project, please cite it:

**APA Format**:
```
O'Connor, J. (2025). Google Ads MCP Server (Version 1.0.0) [Computer software].
https://github.com/johnoconnor0/google-ads-mcp
```

**BibTeX**:
```bibtex
@software{oconnor_google_mcp_2025,
  author = {O'Connor, John},
  title = {Google Ads MCP Server},
  year = {2025},
  version = {1.0.0},
  url = {https://github.com/johnoconnor0/google-ads-mcp}
}
```

See [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

## Support & Resources

### Documentation

- **Quick Start**: [QUICKSTART.md](documentation/QUICKSTART.md)
- **Implementation Plan**: [IMPLEMENTATION_PLAN.md](documentation/IMPLEMENTATION_PLAN.md)
- **Executive Summary**: [EXECUTIVE_SUMMARY.md](documentation/EXECUTIVE_SUMMARY.md)
- **Claude Instructions**: [.claude/CLAUDE.md](.claude/CLAUDE.md)

### Google Ads Resources

- **Google Ads API**: [Documentation](https://developers.google.com/google-ads/api/docs)
- **Developer Token**: [Apply Here](https://developers.google.com/google-ads/api/docs/get-started/dev-token)
- **OAuth Setup**: [OAuth Guide](https://developers.google.com/google-ads/api/docs/oauth/overview)
- **Support**: [Google Ads API Support](https://developers.google.com/google-ads/api/support)

### MCP Resources

- **MCP Documentation**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Claude Desktop**: [Claude Desktop Docs](https://claude.ai/desktop)
- **MCP GitHub**: [github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)

### Community & Support

- **GitHub Issues**: [Report issues or request features](https://github.com/johnoconnor0/google-ads-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/johnoconnor0/google-ads-mcp/discussions)
- **Email**: open-source@weblifter.com.au

### Related Projects

- **Claude Desktop**: AI assistant with MCP support
- **MCP Servers**: [Awesome MCP Servers](https://github.com/modelcontextprotocol/servers)
- **Google Ads Scripts**: [Scripts Library](https://developers.google.com/google-ads/scripts)

---

**Version**: 1.0.0
**Last Updated**: December 17, 2025
**Author**: John O'Connor
**License**: MIT

**Star this repository** if you find it useful!
