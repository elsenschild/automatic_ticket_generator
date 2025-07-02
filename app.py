from flask import Flask, redirect, request, session, render_template
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
ENVIRONMENT = os.getenv("ENVIRONMENT", "sandbox")

BASE_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
BASE_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

SCOPE = "com.intuit.quickbooks.accounting openid profile email phone address"

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/connect")
def connect():
    query_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "state": "random_csrf_token_here",
    }
    return redirect(f"{BASE_AUTH_URL}?{urlencode(query_params)}")

@app.route("/callback")
def callback():
    auth_code = request.args.get("code")
    realm_id = request.args.get("realmId")

    if not auth_code or not realm_id:
        return "<h2>Missing code or realm ID. Did QuickBooks redirect with valid params?</h2>", 400

    session["realm_id"] = realm_id

    token_response = requests.post(
        BASE_TOKEN_URL,
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {requests.auth._basic_auth_str(CLIENT_ID, CLIENT_SECRET)}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
        },
    )

    if token_response.status_code == 200:
        tokens = token_response.json()
        session["access_token"] = tokens["access_token"]
        session["refresh_token"] = tokens["refresh_token"]
        return "<h2>✅ Connected to QuickBooks! You can close this window.</h2>"
    else:
        return f"<h2>❌ Failed to connect: {token_response.text}</h2>", 400
