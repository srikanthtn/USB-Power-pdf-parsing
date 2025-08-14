#!/usr/bin/env python3
"""
Simple script to test if Gemini API key is working
"""

import os
import requests
import json

def check_gemini_api_key():
    """Test if Gemini API key is working"""
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable is NOT set")
        print("Please set it with: set GEMINI_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:8]}...{api_key[-4:]}")
    
    # Test the API with a simple request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Say 'Hello, Gemini is working!' and nothing else."
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 50
        }
    }
    
    try:
        print("🔄 Testing Gemini API connection...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            message = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"✅ Gemini API is working! Response: {message}")
            return True
        else:
            print(f"❌ Gemini API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_environment_variables():
    """Check all relevant environment variables"""
    print("🔍 Checking environment variables...")
    print("-" * 50)
    
    # Check GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ GEMINI_API_KEY: {gemini_key[:8]}...{gemini_key[-4:]}")
    else:
        print("❌ GEMINI_API_KEY: NOT SET")
    
    # Check LLM_PROVIDER
    llm_provider = os.getenv("LLM_PROVIDER", "gemini (default)")
    print(f"ℹ️  LLM_PROVIDER: {llm_provider}")
    
    # Check other potential API keys
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"✅ GROQ_API_KEY: {groq_key[:8]}...{groq_key[-4:]}")
    else:
        print("❌ GROQ_API_KEY: NOT SET")
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print(f"✅ OPENROUTER_API_KEY: {openrouter_key[:8]}...{openrouter_key[-4:]}")
    else:
        print("❌ OPENROUTER_API_KEY: NOT SET")
    
    together_key = os.getenv("TOGETHER_API_KEY")
    if together_key:
        print(f"✅ TOGETHER_API_KEY: {together_key[:8]}...{together_key[-4:]}")
    else:
        print("❌ TOGETHER_API_KEY: NOT SET")
    
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct (default)")
    print(f"ℹ️  OLLAMA_MODEL: {ollama_model}")
    
    print("-" * 50)

def main():
    """Main function"""
    print("🚀 Gemini API Key Checker")
    print("=" * 50)
    
    # Check environment variables first
    check_environment_variables()
    print()
    
    # Test Gemini API
    if check_gemini_api_key():
        print("\n🎉 Your Gemini API key is working perfectly!")
        print("You can now use the RAG pipeline with Gemini.")
    else:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure you have a valid Google AI Studio account")
        print("2. Get your API key from https://makersuite.google.com/app/apikey")
        print("3. Set it with: set GEMINI_API_KEY=your_key_here")
        print("4. Or use a different provider: set LLM_PROVIDER=ollama")

if __name__ == "__main__":
    main()
