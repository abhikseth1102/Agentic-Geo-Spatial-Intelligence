import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the API key from your .env file
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("No API key found. Please add GOOGLE_API_KEY to your .env file.")
    exit(1)

genai.configure(api_key=api_key)

print(f"Checking available models for key: {api_key[:8]}... (make sure this is your NEW key!)")
print("-" * 45)
print("Active Models Available for Text Generation:")
print("-" * 45)

try:
    # Iterate through all available models on the server
    for model in genai.list_models():
        # We only care about models that can power your LangChain agents (text generation)
        if 'generateContent' in model.supported_generation_methods:
            print(model.name)
except Exception as e:
    print(f"\nAPI Error: Could not fetch models.")
    print("This usually means your API key is invalid or has been revoked by Google.")
    print(f"Error details: {e}")
