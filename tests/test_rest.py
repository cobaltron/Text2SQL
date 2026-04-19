import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

prompt = "Write a basic postgres query"

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
data = {
    "contents": [{"parts":[{"text": prompt}]}]
}
print("Sending REST request...")
start = time.time()
resp = requests.post(url, json=data)
end = time.time()
print(f"Time taken: {end-start:.2f} seconds")
print(resp.status_code)
