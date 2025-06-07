# list_hf_models.py
import requests

API = "https://huggingface.co/api/models"
params = {
    "filter": "text-generation",
    "sort": "downloads",
    "direction": -1,
    "limit": 10,
}

response = requests.get(API, params=params)
if response.status_code == 200:
    models = response.json()
    print("Top 10 Hugging Face Text Generation Models:")
    for m in models:
        print(f"- {m['id']}")
else:
    print("Failed to fetch models:", response.status_code)
