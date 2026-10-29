"""Gemini helper using the current Google Gen AI SDK (`google-genai`).

The older `google-generativeai` package is replaced by `google-genai`.
"""

from google import genai

SYSTEM_PROMPT = (
    "You are an agriculture, water and food-security advisor for Andhra Pradesh "
    "and Telangana, India. Give practical, specific advice. Use the district data "
    "in the context when relevant, say when you are unsure, and keep answers "
    "under 300 words unless asked for more."
)


def setup_ai(api_key: str):
    """Return a Gemini client, or None when no key is configured."""
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def ask_ai(client, model: str, context: str, question: str) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXT\n{context}\n\nQUESTION\n{question}"
    response = client.models.generate_content(model=model, contents=prompt)
    return (response.text or "").strip() or "No answer was returned. Please try rephrasing."
