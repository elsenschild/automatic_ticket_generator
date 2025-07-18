import tkinter as tk
from ticket_app import TicketApp 
from dotenv import load_dotenv

load_dotenv()
if __name__ == "__main__":
    root = tk.Tk()
    app = TicketApp(root)
    root.mainloop()