"""
Main entry point for the Ticket Generator application.

This script initializes the Tkinter root window, loads environment variables,
and starts the TicketApp GUI.

Usage:
    python main.py
"""

import tkinter as tk
from ticket_app import TicketApp 
from dotenv import load_dotenv

load_dotenv()
if __name__ == "__main__":
    root = tk.Tk()
    app = TicketApp(root)
    root.mainloop()