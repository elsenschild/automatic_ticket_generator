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
    print("Hello")
    try:
        auth_code = request.args.get("code")
        realm_id = request.args.get("realmId")    
        print("Received callback")
        print("Auth code:", auth_code)
        print("Realm ID:", realm_id)

        if not auth_code or not realm_id:
            return "<h2>❌ Missing 'code' or 'realmId' in callback URL.</h2>", 400

        session["realm_id"] = realm_id

        import base64
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()

        token_response = requests.post(
            BASE_TOKEN_URL,
            headers={
                "Accept": "application/json",
                "Authorization": f"Basic {b64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": REDIRECT_URI,
            },
        )
        print("Status:", token_response.status_code)
        print("Response body:", token_response.text)
        if token_response.status_code == 200:
            tokens = token_response.json()
            session["access_token"] = tokens["access_token"]
            session["refresh_token"] = tokens["refresh_token"]
            return "<h2>✅ Connected to QuickBooks! You can close this window.</h2>"
        else:
            return f"<h2>❌ Failed to get tokens:<br><pre>{token_response.text}</pre></h2>", 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<h2>❌ Exception during callback:<br><pre>{str(e)}</pre></h2>", 500

@app.route("/debug")
def debug():
    return f"REDIRECT_URI: {REDIRECT_URI}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # use 5051 if 5000 is taken
    app.run(debug=True, host="0.0.0.0", port=port)
