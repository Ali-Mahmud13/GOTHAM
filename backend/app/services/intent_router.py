import re
from typing import Literal
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import sys
import os

# Ensure config can be imported from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import config

class IntentRouter:
    def __init__(self):
        # Booking keywords in English and Urdu
        self.booking_pattern = re.compile(
            r'\b(?:book|cancel|reschedule|appointment|slot|availability|اپوائنٹمنٹ|ملاقات|وقت لینا|کینسل|ری شیڈول)\b',
            re.IGNORECASE
        )
        
        # Medical keywords to force general intent
        self.medical_pattern = re.compile(
            r'\b(?:pain|blood|sugar|pressure|bp|gd|assess|check|symptom|medicine|treatment|dr|doctor|patient|p0)\b',
            re.IGNORECASE
        )

        self.llm = ChatGroq(
            temperature=0,
            model_name=config.MODEL_NAME,
            api_key=config.GROQ_API_KEY
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a healthcare application.
            Determine if the user's message is primarily trying to manage an appointment (booking intent) or anything else (general intent).
            Respond with EXACTLY ONE WORD: either "booking" or "general"."""),
            ("user", "{message}")
        ])

        self.chain = self.prompt | self.llm

    def classify(self, message: str) -> Literal["booking", "general"]:
        # Stage A: Fast Regex checking
        is_booking_keyword = bool(self.booking_pattern.search(message))
        is_medical_keyword = bool(self.medical_pattern.search(message))
        
        # If obvious booking and not an obvious medical check
        if is_booking_keyword and not is_medical_keyword:
            return "booking"
            
        # If obvious medical and not an obvious booking
        if is_medical_keyword and not is_booking_keyword:
            return "general"
            
        # Stage B: LLM Fallback for ambiguous cases
        try:
            response = self.chain.invoke({"message": message})
            intent = response.content.strip().lower()
            if intent in ["booking", "general"]:
                return intent
        except Exception as e:
            print(f"Intent router LLM error: {e}")
            
        # Default to general
        return "general"

intent_router = IntentRouter()
