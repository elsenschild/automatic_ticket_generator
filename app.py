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
    try:
        auth_code = request.args.get("code")
        realm_id = request.args.get("realmId")

        if not auth_code or not realm_id:
            return "<h2>❌ Missing 'code' or 'realmId' in the URL. QuickBooks may have rejected the redirect.</h2>", 400

        session["realm_id"] = realm_id

        # Exchange auth code for tokens
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

        # Debug output
        print("Token response status:", token_response.status_code)
        print("Token response body:", token_response.text)

        if token_response.status_code == 200:
            tokens = token_response.json()
            session["access_token"] = tokens["access_token"]
            session["refresh_token"] = tokens["refresh_token"]
            return "<h2>✅ Connected to QuickBooks! You can close this window.</h2>"
        else:
            return f"<h2>❌ Token request failed:<br><pre>{token_response.text}</pre></h2>", 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<h2>❌ Exception during callback:<br><pre>{str(e)}</pre></h2>", 500
