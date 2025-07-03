import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
API_BASE_URL = "https://sandbox-quickbooks.api.intuit.com"

def load_tokens():
    tokens = {}
    try:
        with open("qb_tokens.txt", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    tokens[key.strip()] = value.strip()
    except FileNotFoundError:
        return {}
    return tokens

def fetch_invoices(tokens, invoice_num=10):
    access_token = tokens.get("access_token")
    realm_id = tokens.get("realm_id")
    if not access_token or not realm_id:
        return []

    url = f"{API_BASE_URL}/v3/company/{realm_id}/query"
    query = f"SELECT * FROM Invoice MAXRESULTS {invoice_num}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/text"
    }

    response = requests.get(url, headers=headers, params={"query": query})
    if response.status_code == 200:
        return response.json().get("QueryResponse", {}).get("Invoice", [])
    else:
        print("Error:", response.status_code, response.text)
        return []
