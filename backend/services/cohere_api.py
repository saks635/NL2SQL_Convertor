# services/cohere_api.py
from dotenv import load_dotenv
import os
import cohere

load_dotenv()

co = cohere.Client(os.getenv("COHERE_API_KEY"))

def call_cohere(prompt):
    """
    Sends a prompt to the Cohere API and returns the generated SQL query.
    """
    response = co.generate(
        model='command-r-plus',
        prompt=prompt,
        max_tokens=200,
        temperature=0.3
    )
    return response.generations[0].text.strip()