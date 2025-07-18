import tkinter as tk
import os
from tkinter import messagebox, filedialog
from instructions_window import show_instructions
from tsv_handler import handle_tsv
from pdf_handler import generate_tickets, generate_previews
from pdf2image import convert_from_path
from PIL import Image, ImageTk
from dropbox_sign import ApiClient, Configuration, apis, models
from dropbox_sign.rest import ApiException
from tkinter.simpledialog import askstring
from dropbox import send_signature_request


class TicketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Ticket Generator")

        self.data_path = ""
        self.pdf_path = os.path.join(os.path.dirname(__file__), "assets", "delivery_ticket_template.pdf")
        self.status_label = None

        self.setup_welcome_screen()

    def hide_all_frames(self):
        for frame in [getattr(self, attr) for attr in dir(self) if attr.endswith("_frame")]:
            try:
                frame.pack_forget()
            except:
                pass

    def setup_welcome_screen(self):
        self.hide_all_frames()
        self.welcome_frame = tk.Frame(self.root)
        self.welcome_frame.pack(padx=20, pady=20)

        tk.Label(self.welcome_frame, text="Welcome to the PDF Ticket Generator!", font=("Arial", 14)).pack(pady=(10, 5))
        tk.Label(self.welcome_frame, text="Follow the steps to generate tickets from your TSV file.", font=("Arial", 10)).pack(pady=(0, 15))

        tk.Button(self.welcome_frame, text="See instructions to extract claims from Quickbook", command=lambda: show_instructions(self.root)).pack(pady=(0, 5))
        tk.Button(self.welcome_frame, text="Continue", command=self.show_csv_screen).pack(pady=(0, 5))

    def show_main_ui(self):
        self.hide_all_frames()
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=10)

        tk.Button(self.main_frame, text="Generate Tickets", command=self.generate).pack(pady=20)
        tk.Button(self.main_frame, text="Back to Load Data", command=self.show_csv_screen)
        tk.Button(self.main_frame, text="Back to Welcome", command=self.back_to_welcome).pack(pady=(0, 10))

        self.status_label = tk.Label(self.main_frame, text="", fg="green", font=("Arial", 10))
        self.status_label.pack()

    def show_csv_screen(self):
        self.hide_all_frames()
        self.csv_frame = tk.Frame(self.root)
        self.csv_frame.pack(pady=10)

        tk.Label(self.csv_frame, text="Load the QuickBook TSV File", font=("Arial", 12)).pack(pady=(0, 10))
        self.status_label = tk.Label(self.csv_frame, text="", fg="green", font=("Arial", 10))
        self.status_label.pack(pady=10)

        tk.Button(self.csv_frame, text="Select Quickbook File", command=self.load_qb_data_tsv).pack(pady=5)
        tk.Button(self.csv_frame, text="Next", command=self.show_main_ui).pack(pady=(20, 5))
        tk.Button(self.csv_frame, text="Back to Welcome", command=self.back_to_welcome).pack(pady=5)

    def back_to_welcome(self):
        self.hide_all_frames()
        self.welcome_frame.pack()

    def load_qb_data_tsv(self):
        path = filedialog.askopenfilename(filetypes=[("TSV files", "*.tsv")])
        if path:
            self.data_path = path
            filename = os.path.basename(self.data_path)
            self.status_label.config(text=f"Quickbook TSV(s) Loaded. Loaded: {filename}")

    def generate(self):
        if not self.data_path or not self.pdf_path:
            messagebox.showerror("Missing Files", "Please select TSV and PDF template.")
            return

        orders, _ = handle_tsv(self.data_path)
        orders.sort(key=lambda o: o[2].lower())
        self.orders_for_preview = orders

        self.preview_data = generate_previews(orders, self.pdf_path)
        pdf_paths = [p[0] for p in self.preview_data]
        self.preview_tickets(pdf_paths)

    def load_pdf_images(self, pdf_path):
        pages = convert_from_path(pdf_path, dpi=150)
        first_page = pages[0]
        w_percent = 800 / float(first_page.size[0])
        h_size = int(float(first_page.size[1]) * w_percent)
        first_page = first_page.resize((800, h_size), Image.ANTIALIAS)
        self.preview_images = [ImageTk.PhotoImage(first_page)]

    def next_ticket(self):
        if self.current_pdf_index + 1 < len(self.pdf_paths):
            self.current_pdf_index += 1
            self.load_pdf_images(self.pdf_paths[self.current_pdf_index])
            self.show_current_image()

    def prev_ticket(self):
        if self.current_pdf_index > 0:
            self.current_pdf_index -= 1
            self.load_pdf_images(self.pdf_paths[self.current_pdf_index])
            self.show_current_image()

    def remove_ticket(self):
        if not self.pdf_paths or not self.preview_data:
            return

        confirm = messagebox.askyesno("Remove Ticket", f"Are you sure you want to remove ticket {self.current_pdf_index + 1}?")
        if not confirm:
            return

        del self.pdf_paths[self.current_pdf_index]
        del self.preview_data[self.current_pdf_index]

        if not self.pdf_paths:
            messagebox.showinfo("Done", "All tickets removed.")
            self.preview_window.destroy()
            return

        if self.current_pdf_index >= len(self.pdf_paths):
            self.current_pdf_index = len(self.pdf_paths) - 1

        self.load_pdf_images(self.pdf_paths[self.current_pdf_index])
        self.show_current_image()

    def choose_output_directory(self):
        return filedialog.askdirectory(title="Choose folder to save tickets")

    def save_all_tickets(self):
        if not self.orders_for_preview:
            messagebox.showerror("Error", "No orders loaded")
            return

        output_dir = self.choose_output_directory()
        if not output_dir:
            return

        orders_remaining = [group for _, group in self.preview_data]
        generate_tickets(orders_remaining, self.pdf_path, output_dir)
        messagebox.showinfo("Saved", f"All tickets saved to:\n{output_dir}")

    def show_current_image(self):
        self.preview_label.config(image=self.preview_images[0])
        self.page_label.config(
            text=f"Ticket {self.current_pdf_index + 1} of {len(self.pdf_paths)}"
        )

    def send_to_docusign(self):
        if not self.pdf_paths:
            messagebox.showerror("Error", "No tickets available to send.")
            return

        signer_name = askstring("Signer Name", "Enter recipient's full name:")
        signer_email = askstring("Signer Email", "Enter recipient's email address:")
        current_pdf_path = self.pdf_paths[self.current_pdf_index]

        try:
            request_id = send_signature_request(
                signer_name=signer_name,
                signer_email=signer_email,
                pdf_path=current_pdf_path
            )

            if "Error:" in str(request_id):
                messagebox.showerror("Error", request_id)
            else:
                messagebox.showinfo("Success", f"Sent to {signer_email}.\nRequest ID:\n{request_id}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def preview_tickets(self, pdf_paths):
        if not pdf_paths:
            messagebox.showerror("Error", "No PDFs to preview.")
            return

        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Preview Tickets")
        self.preview_window.geometry("850x900")
        self.preview_window.configure(bg="#f5f5f5")
        self.preview_window.focus_set()

        self.pdf_paths = pdf_paths
        self.current_pdf_index = 0
        self.preview_images = []
        self.current_page = 0

        header = tk.Label(self.preview_window, text="PDF Ticket Preview",
                          font=("Segoe UI", 14, "bold"), bg="#f5f5f5")
        header.pack(pady=(15, 10))

        canvas_frame = tk.Frame(self.preview_window)
        canvas_frame.pack(expand=True, fill="both", padx=10)

        self.canvas = tk.Canvas(canvas_frame, bg="#f5f5f5", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.image_container = tk.Frame(self.canvas, bg="#f5f5f5")
        self.canvas.create_window((0, 0), window=self.image_container, anchor="nw")

        self.preview_label = tk.Label(self.image_container, bg="#f5f5f5")
        self.preview_label.pack(pady=10)

        def resize_canvas(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.image_container.bind("<Configure>", resize_canvas)

        self.page_label = tk.Label(self.preview_window, font=("Segoe UI", 10), bg="#f5f5f5")
        self.page_label.pack(pady=(0, 10))

        btn_frame = tk.Frame(self.preview_window, bg="#f5f5f5")
        btn_frame.pack(pady=15)

        def styled_button(text, command):
            return tk.Button(
                btn_frame,
                text=text,
                command=command,
                font=("Segoe UI", 10),
                bg="#d0e7ff",                # Pale blue background
                fg="#003366",                # Text color
                activebackground="#b5d9ff",  # On hover
                activeforeground="#002244",
                highlightbackground="#d0e7ff",  # For macOS border
                relief="raised",             # Can try "groove", "flat", "ridge"
                bd=1,
                padx=10,
                pady=5
            )

        styled_button("⟨ Prev", self.prev_ticket).pack(side=tk.LEFT, padx=5)
        styled_button("Next ⟩", self.next_ticket).pack(side=tk.LEFT, padx=5)
        styled_button("🗑 Remove", self.remove_ticket).pack(side=tk.LEFT, padx=5)
        styled_button("💾 Save All", self.save_all_tickets).pack(side=tk.LEFT, padx=5)
        styled_button("✉️ Send to DocuSign", self.send_to_docusign).pack(side=tk.LEFT, padx=5)

        self.preview_window.bind("<Left>", lambda event: self.prev_ticket())
        self.preview_window.bind("<Right>", lambda event: self.next_ticket())

        self.load_pdf_images(self.pdf_paths[self.current_pdf_index])
        self.show_current_image()
