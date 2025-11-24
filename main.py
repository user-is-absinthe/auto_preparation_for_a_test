# main_openai.py
from openai import OpenAI
from config import OPENROUTER_API_KEY, MODEL, BASE_URL

client = OpenAI(
    base_url=BASE_URL,
    api_key=OPENROUTER_API_KEY
)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": "Привет! Напиши короткий стих о программировании."}
    ]
)

print(response.choices[0].message.content)
