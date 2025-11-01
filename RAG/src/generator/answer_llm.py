import os
import requests
from src.config.settings import LLM_MODEL, HF_API_TOKEN
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Use HF token from .env
HF_API_TOKEN = os.environ.get("HUGGINGFACEHUB_API_TOKEN")

MODEL_NAME = LLM_MODEL  # e.g., "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"

# Hugging Face API endpoint for chat-based completions
API_URL = "https://router.huggingface.co/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}


class AnswerGenerator:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        if not HF_API_TOKEN:
            print("❌ Hugging Face API token not found. Check your .env file.")
        else:
            print(f"✅ Hugging Face token found. Ready to query {self.model_name}")

    def generate_answer(self, prompt: str) -> str:
        if not HF_API_TOKEN:
            return ("Error: Hugging Face API token missing. "
                    "Please add HUGGINGFACEHUB_API_TOKEN to your .env file.")

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP error: {e}")
            return f"Error generating answer: {e}"
        except Exception as e:
            print(f"❌ Other error: {e}")
            return f"Error generating answer: {e}"


class FallbackAnswerGenerator:
    """Fallback generator if no HF token is available."""
    def generate_answer(self, prompt: str) -> str:
        return ("I understand your question, but I'm currently running in fallback mode. "
                "Please set your HUGGINGFACEHUB_API_TOKEN in the .env file to enable full AI responses.")


def get_answer_generator():
    if HF_API_TOKEN:
        return AnswerGenerator()
    else:
        print("⚠️ Using fallback generator (no API key)")
        return FallbackAnswerGenerator()


