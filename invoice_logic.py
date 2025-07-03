import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
API_BASE_URL = "https://sandbox-quickbooks.api.intuit.com"

def fetch_invoices(tokens, invoice_num=10):
    access_token = tokens["access_token"]
    realm_id = tokens["realm_id"]
    url = f"{API_BASE_URL}/v3/company/{realm_id}/query"
    query = f"SELECT * FROM Invoice STARTPOSITION 1 MAXRESULTS {invoice_num}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/text"
    }
    response = requests.get(url, headers=headers, params={"query": query})
    
    print(f"[DEBUG] Request URL: {response.url}")
    print(f"[DEBUG] Status code: {response.status_code}")
    print(f"[DEBUG] Response text: {response.text}")

    if response.status_code == 401 and "Token expired" in response.text:
        # handle token refresh (if you do)
        pass

    if response.status_code == 200:
        data = response.json()
        invoices = data.get("QueryResponse", {}).get("Invoice", [])
        print(f"[DEBUG] Number of invoices found: {len(invoices)}")
        return invoices
    else:
        print(f"[ERROR] Failed to fetch invoices: {response.status_code} {response.text}")
        return []
