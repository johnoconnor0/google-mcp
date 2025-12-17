#!/usr/bin/env python3
"""
Google Ads API OAuth2 Token Generator

This script helps you generate a refresh token for the Google Ads API.
Run this once to get your refresh token, then use it in the MCP server configuration.

Usage:
    python generate_refresh_token.py

Requirements:
    pip install google-auth-oauthlib
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import sys

# Google Ads API OAuth scope
SCOPES = ['https://www.googleapis.com/auth/adwords']


def main():
    print("=" * 70)
    print("Google Ads API - OAuth2 Refresh Token Generator")
    print("=" * 70)
    print()
    print("This script will help you generate a refresh token for the Google Ads API.")
    print("You'll need your OAuth2 Client ID and Client Secret from Google Cloud Console.")
    print()
    print("If you don't have these yet:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a project (or select existing)")
    print("3. Enable the Google Ads API")
    print("4. Create OAuth 2.0 credentials (Desktop app type)")
    print()
    print("=" * 70)
    print()
    
    # Get credentials from user
    client_id = input("Enter your OAuth2 Client ID: ").strip()
    if not client_id:
        print("Error: Client ID is required")
        sys.exit(1)
    
    client_secret = input("Enter your OAuth2 Client Secret: ").strip()
    if not client_secret:
        print("Error: Client Secret is required")
        sys.exit(1)
    
    print()
    print("Starting OAuth2 flow...")
    print("A browser window will open for authorization.")
    print()
    
    try:
        # Create OAuth2 flow
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            },
            scopes=SCOPES
        )
        
        # Run the OAuth flow
        credentials = flow.run_local_server(port=0)
        
        print()
        print("=" * 70)
        print("SUCCESS! Here are your credentials:")
        print("=" * 70)
        print()
        print(f"Client ID:      {client_id}")
        print(f"Client Secret:  {client_secret}")
        print(f"Refresh Token:  {credentials.refresh_token}")
        print()
        print("=" * 70)
        print()
        print("IMPORTANT: Save these credentials securely!")
        print()
        print("Use these to initialize the Google Ads MCP server in Claude Desktop.")
        print("Example initialization message:")
        print()
        print(f"""
Initialize my Google Ads connection with:
- Developer Token: YOUR_DEVELOPER_TOKEN
- Client ID: {client_id}
- Client Secret: {client_secret}
- Refresh Token: {credentials.refresh_token}
- Login Customer ID: YOUR_MCC_ID (optional)
        """.strip())
        print()
        print("=" * 70)
        
    except Exception as e:
        print()
        print(f"Error during OAuth flow: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Verify your Client ID and Client Secret are correct")
        print("2. Make sure you have the Google Ads API enabled in your project")
        print("3. Check that you created 'Desktop app' type credentials")
        print("4. Ensure the redirect URI includes http://localhost")
        sys.exit(1)


if __name__ == "__main__":
    main()
