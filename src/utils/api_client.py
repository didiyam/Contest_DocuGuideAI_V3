import os
from openai import OpenAI

client = None

def get_openai_client():
    global client
    if client is None:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Check your .env file.")

        client = OpenAI(api_key=OPENAI_API_KEY)

    return client
