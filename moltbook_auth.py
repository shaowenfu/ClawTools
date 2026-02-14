#!/usr/bin/env python3
"""
Moltbook Authentication Integration Example

This script demonstrates how to integrate "Sign in with Moltbook" 
authentication into your application.

Follow the official guide: https://moltbook.com/developers.md
"""

import os
import json
import requests
from typing import Optional, Dict, Any


class MoltbookAuth:
    """Moltbook Identity Verification Client"""
    
    def __init__(self, app_api_key: str, audience: str = None):
        """
        Initialize Moltbook auth client
        
        Args:
            app_api_key: Your Moltbook app API key (starts with moltdev_)
            audience: Your domain for audience verification (optional)
        """
        self.app_api_key = app_api_key
        self.audience = audience or "clawdhub.com"
        self.verify_url = "https://www.moltbook.com/api/v1/agents/verify-identity"
    
    def verify_identity_token(self, identity_token: str) -> Dict[str, Any]:
        """
        Verify a Moltbook identity token
        
        Args:
            identity_token: The identity token from X-Moltbook-Identity header
            
        Returns:
            Dict containing verification result and agent info if valid
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Moltbook-App-Key': self.app_api_key
        }
        
        payload = {
            'token': identity_token
        }
        
        # Add audience if specified
        if self.audience:
            payload['audience'] = self.audience
        
        try:
            response = requests.post(
                self.verify_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
    
    def is_valid_agent(self, identity_token: str) -> bool:
        """Check if identity token belongs to a valid agent"""
        result = self.verify_identity_token(identity_token)
        return result.get('valid', False)
    
    def get_agent_profile(self, identity_token: str) -> Optional[Dict[str, Any]]:
        """Get verified agent profile if token is valid"""
        result = self.verify_identity_token(identity_token)
        if result.get('valid'):
            return result.get('agent')
        return None


# Example usage
if __name__ == "__main__":
    # Get your app API key from environment
    app_key = os.environ.get('MOLTBOOK_APP_KEY')
    
    if not app_key:
        print("Please set MOLTBOOK_APP_KEY environment variable")
        print("Get your key at: https://moltbook.com/developers/dashboard")
        exit(1)
    
    # Initialize auth client
    auth = MoltbookAuth(app_key, audience="clawdhub.com")
    
    # Example identity token (this would come from X-Moltbook-Identity header)
    example_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    # Verify the token
    result = auth.verify_identity_token(example_token)
    
    if result.get('valid'):
        agent = result['agent']
        print(f"✅ Verified agent: {agent['name']}")
        print(f"   Karma: {agent['karma']}")
        print(f"   Owner: @{agent['owner']['x_handle']}")
    else:
        print(f"❌ Invalid token: {result.get('error', 'Unknown error')}")