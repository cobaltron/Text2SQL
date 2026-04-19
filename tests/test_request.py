import requests
import json
import time

print("Sending request to FastAPI generate-sql...")
try:
    response = requests.post(
        "http://127.0.0.1:8000/api/generate-sql", 
        json={"query": "Find number of order for each customer"},
        timeout=30
    )
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
