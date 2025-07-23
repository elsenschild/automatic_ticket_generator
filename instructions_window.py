# instructions_window.py

import tkinter as tk
from PIL import Image, ImageTk
import requests
import io

instructions = (
    "1. Log into Quickbooks, go to Reports --> Custom Reports.\n"
    "2. Press \"Edit\" on 'Delivery Ticket Report'.\n"
    "3. Above the report, enter the date range for the orders you want to extract.\n"
    "4. Click the square with the arrow in it in the top right corner of the report.\n"
    "5. Press 'Export to Excel'.\n"
    "6. Open the file in Excel or Google Sheets.\n"
    "7. Press 'File' -> 'Export' --> 'TSV'.\n"
    "9. Upload the file to this app by pressing the 'Select Quickbooks File' button."
)

def load_image_from_github(url):
    """ Load an image from a GitHub repository.
    
    Args: 
        url: The URL of the image on GitHub.

    Returns:
        A PIL Image object.
    """
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))

def show_instructions(root):
    """ Show the instructions in a new window.

    Args: 
        root: The root window of the application.

    Returns:
        None
    """
    instruction_window = tk.Toplevel(root)
    instruction_window.title("Steps to Extract Quickbook Orders")
    instruction_window.geometry("700x700")

    instruction_frame = tk.Frame(instruction_window, padx=20, pady=20)
    instruction_frame.pack(fill="both", expand=True)

    tk.Label(
        instruction_frame,
        text="Steps to Extract Quickbook Orders",
        font=("Arial", 14, "bold")
    ).pack(pady=(0, 10))

    try:
        img = load_image_from_github(
            "https://raw.githubusercontent.com/elsenschild/automatic_ticket_generator/main/assets/qb_instructions.png"
        )
        img.thumbnail((680, 380))  # Keeps aspect ratio
        tk_img = ImageTk.PhotoImage(img)
        label = tk.Label(instruction_frame, image=tk_img)
        label.image = tk_img  # prevent garbage collection
        label.pack()
    except Exception as e:
        tk.Label(instruction_frame, text="Failed to load image:", fg="red").pack()

    text_box = tk.Text(instruction_frame, wrap="word", font=("Arial", 10), height=12)
    text_box.insert("1.0", instructions)
    text_box.config(state="disabled")
    text_box.pack(fill="both", expand=True)

    tk.Button(instruction_frame, text="Close", command=instruction_window.destroy).pack(pady=10)

