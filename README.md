# Google Ads MCP Server - Setup Guide

A comprehensive Model Context Protocol server for Google Ads API integration, providing powerful tools for campaign analysis, optimization, and management.

## Features

### Analysis Tools
- **List Accounts** - View all accessible Google Ads accounts
- **Campaign Performance** - Comprehensive metrics with filtering and date ranges
- **Keyword Performance** - Quality scores, positions, and conversion data
- **Search Terms Report** - Discover actual queries triggering your ads
- **Ad Group Performance** - Group-level metrics and analysis
- **Recommendations** - Google's AI-powered optimization suggestions

### Management Tools
- **Update Campaign Budget** - Adjust daily budget allocations
- **Pause/Enable Campaigns** - Control campaign status
- **Custom GAQL Queries** - Execute advanced custom queries

## Prerequisites

### 1. Google Ads API Access

You need:
- **Developer Token** - Apply at https://developers.google.com/google-ads/api/docs/get-started/dev-token
- **Google Ads Account** - Active account with campaigns
- **OAuth2 Credentials** - Client ID and Client Secret

### 2. OAuth2 Setup

#### Step 1: Create OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Ads API**
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Choose "Desktop app" as application type
6. Save your **Client ID** and **Client Secret**

#### Step 2: Generate Refresh Token

You need to generate a refresh token using the OAuth2 flow. Here's a Python script to help:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

# Your OAuth2 credentials
CLIENT_ID = 'your-client-id.apps.googleusercontent.com'
CLIENT_SECRET = 'your-client-secret'

# Google Ads API scope
SCOPES = ['https://www.googleapis.com/auth/adwords']

# Run OAuth flow
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

Save this as `generate_token.py` and run it. It will open a browser for authorization and print your refresh token.

**Install required package first:**
```bash
pip install google-auth-oauthlib
```

## Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install google-ads mcp httpx pydantic
```

### Step 2: Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

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

Replace `/absolute/path/to/google_ads_mcp.py` with the actual path to the server file.

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop for the changes to take effect.

## Usage

### Initial Setup

When you first interact with Claude Desktop after installing the MCP server, initialize the connection with your credentials:

```
Initialize my Google Ads connection with these credentials:
- Developer Token: INSERT_YOUR_DEV_TOKEN
- Client ID: INSERT_YOUR_CLIENT_ID.apps.googleusercontent.com
- Client Secret: INSERT_YOUR_CLIENT_SECRET
- Refresh Token: INSERT_YOUR_REFRESH_TOKEN
- Login Customer ID: INSERT_YOUR_MCC_ID (optional, only if using MCC)
```

Claude will call the `google_ads_initialize` tool and confirm the connection.

### Example Queries

Once initialized, you can ask Claude things like:

#### Account Overview
```
"Show me all my Google Ads accounts"
"List all accessible accounts"
```

#### Campaign Analysis
```
"Show campaign performance for the last 30 days for account 1234567890"
"Which campaigns spent the most in the last week?"
"Show me only enabled campaigns with at least $100 in spend"
```

#### Keyword Optimization
```
"Analyze keyword performance for campaign 12345"
"Show me keywords with quality score below 5"
"Which keywords have the highest cost per conversion?"
```

#### Search Terms Discovery
```
"Get search terms report for the last 30 days"
"What search queries are triggering my ads?"
"Find search terms with high impressions but low CTR"
```

#### Budget Management
```
"Increase budget for campaign 12345 to $100 per day"
"Pause campaign 67890"
"Enable campaign 54321"
```

#### Advanced Analysis
```
"Show me Google's optimization recommendations"
"Compare ad group performance across all campaigns"
"Find keywords with average position worse than 3"
```

#### Custom Queries
```
"Execute this GAQL query: SELECT campaign.name, metrics.clicks FROM campaign"
```

## Available Tools

### 1. google_ads_initialize
Initialize API connection with OAuth credentials.

**Parameters:**
- `developer_token` (required)
- `client_id` (required)
- `client_secret` (required)
- `refresh_token` (required)
- `login_customer_id` (optional) - MCC account ID

### 2. google_ads_list_accounts
List all accessible Google Ads accounts.

**Parameters:**
- `response_format` - "markdown" or "json"

### 3. google_ads_campaign_performance
Get comprehensive campaign metrics.

**Parameters:**
- `customer_id` (required) - Account ID without hyphens
- `date_range` - TODAY, YESTERDAY, LAST_7_DAYS, LAST_30_DAYS, etc.
- `campaign_status` - Filter by ENABLED, PAUSED, or REMOVED
- `min_cost` - Minimum cost threshold
- `limit` - Max results (default: 50)
- `response_format` - "markdown" or "json"

### 4. google_ads_keyword_performance
Analyze keyword-level performance.

**Parameters:**
- `customer_id` (required)
- `campaign_id` (optional)
- `date_range` (default: LAST_30_DAYS)
- `min_impressions` (optional)
- `limit` (default: 50)
- `response_format`

### 5. google_ads_search_terms
Get actual search queries triggering ads.

**Parameters:**
- `customer_id` (required)
- `campaign_id` (optional)
- `date_range` (default: LAST_30_DAYS)
- `min_impressions` (default: 10)
- `limit` (default: 50)
- `response_format`

### 6. google_ads_ad_group_performance
Analyze ad group metrics.

**Parameters:**
- `customer_id` (required)
- `campaign_id` (optional)
- `date_range` (default: LAST_30_DAYS)
- `limit` (default: 50)
- `response_format`

### 7. google_ads_recommendations
Get Google's AI-powered recommendations.

**Parameters:**
- `customer_id` (required)
- `recommendation_types` (optional) - Filter by type
- `limit` (default: 20)
- `response_format`

### 8. google_ads_update_campaign_budget
Modify campaign daily budget.

**Parameters:**
- `customer_id` (required)
- `campaign_id` (required)
- `budget_amount_micros` (required) - Amount in micros (multiply by 1,000,000)

**Example:** To set $50/day budget: `budget_amount_micros = 50000000`

### 9. google_ads_update_campaign_status
Pause or enable campaigns.

**Parameters:**
- `customer_id` (required)
- `campaign_id` (required)
- `status` - "ENABLED" or "PAUSED"

### 10. google_ads_custom_query
Execute custom GAQL queries.

**Parameters:**
- `customer_id` (required)
- `query` (required) - GAQL query string
- `response_format`

**Use Query Builder:** https://developers.google.com/google-ads/api/fields/latest/overview_query_builder

## Tips & Best Practices

### Date Ranges
Use predefined ranges for consistency:
- `TODAY` - Current day
- `YESTERDAY` - Previous day
- `LAST_7_DAYS` - Last week
- `LAST_14_DAYS` - Last 2 weeks
- `LAST_30_DAYS` - Last month (default)
- `LAST_90_DAYS` - Last quarter
- `THIS_MONTH` - Month to date
- `LAST_MONTH` - Previous month

### Customer IDs
Always provide customer IDs **without hyphens**:
- ✓ Correct: `1234567890`
- ✗ Wrong: `123-456-7890`

### Response Formats
- Use **markdown** (default) for readable reports and summaries
- Use **json** for programmatic processing or exporting data

### Performance Optimization
- Use `limit` parameter to control result size
- Apply filters (`min_cost`, `min_impressions`, etc.) to reduce data
- Start with smaller date ranges for faster responses

### Budget Updates
Budgets are in **micros** (1/1,000,000 of currency unit):
- $10.00 = 10,000,000 micros
- $50.50 = 50,500,000 micros
- $100.00 = 100,000,000 micros

### MCC Account Access
If you manage multiple client accounts through an MCC:
1. Use your MCC's customer ID as `login_customer_id` during initialization
2. Use individual client account IDs in tool calls
3. Claude can analyze data across all accessible accounts

## Troubleshooting

### "Client not initialized" Error
Make sure you call `google_ads_initialize` first before using any other tools.

### "Invalid customer ID" Error
Ensure customer IDs are:
- 10 digits
- Without hyphens
- For the correct account

### "Authentication failed" Error
Check:
- Developer token is valid and approved
- OAuth credentials are correct
- Refresh token hasn't expired (regenerate if needed)
- Correct login_customer_id for MCC access

### "Insufficient permissions" Error
Verify:
- Your Google account has access to the Google Ads account
- Developer token has appropriate access level
- OAuth scope includes Google Ads API

### Rate Limiting
The Google Ads API has rate limits. If you hit them:
- Reduce the frequency of requests
- Use smaller date ranges
- Apply more filters to reduce data volume

## GAQL Resources

For writing custom queries:
- **Query Builder**: https://developers.google.com/google-ads/api/fields/latest/overview_query_builder
- **Query Validator**: https://developers.google.com/google-ads/api/docs/query/validate
- **GAQL Documentation**: https://developers.google.com/google-ads/api/docs/query/overview
- **Field Reference**: https://developers.google.com/google-ads/api/fields/latest/overview

## Security Notes

- **Never commit credentials** to version control
- Store credentials securely (use environment variables or secrets manager)
- Rotate OAuth tokens regularly
- Use MCC accounts for managing multiple clients
- Review API access logs periodically

## Support

For issues with:
- **This MCP Server**: Check the code and documentation above
- **Google Ads API**: https://developers.google.com/google-ads/api/support
- **Developer Token**: https://support.google.com/google-ads/contact/api_support
- **OAuth**: https://developers.google.com/identity/protocols/oauth2

## License

This MCP server is provided as-is for use with Claude Desktop and the Google Ads API.

## Version

- **Version**: 1.0.0
- **Google Ads API Version**: v17+
- **MCP SDK Version**: 1.1.0+
- **Last Updated**: November 2025
