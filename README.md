# Quickbooks Invoice Fetcher
A Python app that lets you authenticate with QuickBooks Online, fetch invoices, and export them to a CSV.
=====================================

## Features
- Authenticate with QuickBooks Online using OAuth 2.0
- Fetch any number of invoices
- Export invoices to a CSV file
- Simple GUI interface with Tkinter
====================================

## Getting Started

### 1. Clone the repository
git clone https://github.com/elsenschild/automatic_ticket_generator.git
cd automatic_ticket_generator

### 2. Set up your environment
Install required packages
Terminal command: pip install -r requirements.txt

### 3. Create a .env file
In the project root, create a file named .env with the following:
CLIENT_ID=your_quickbooks_client_id
CLIENT_SECRET=your_quickbooks_client_secret

### 4. Ensure you have qb_tokens.txt file
This file should contain your access and refresh tokens, along with your QuickBooks realm ID, e.g.:
access_token=your_access_token
refresh_token=your_refresh_token
realm_id=your_realm_id

If you don’t have the token file qb_tokens.txt, you need to authorize the app with QuickBooks Online:
- Start the OAuth authorization server:
python oauth_quickbooks.py
- Open your browser and visit:
http://localhost:8000
- Click the link to connect your QuickBooks Online account and complete the authorization.
- After successful authorization, the app will save your tokens in qb_tokens.txt.
- Close the browser window and stop the authorization server (CTRL+C in terminal).

### 5. Run the invoice fetcher GUI
Once authorized, start the invoice fetcher GUI
Terminal: python fetch_invoices.py
This will open the GUI where you can enter how many invoices to fetch, view them, and export them as CSV.

