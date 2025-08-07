import tkinter as tk
import os
import threading
from tkinter import messagebox, filedialog
from instructions_window import show_instructions
from tsv_handler import handle_file
from pdf_handler import generate_tickets, generate_previews, group_orders
from pdf2image import convert_from_path
from PIL import Image, ImageTk
from dropbox_sign import ApiClient, Configuration, apis, models
from dropbox_sign.rest import ApiException
from tkinter import ttk
from tkinter.simpledialog import askstring
from dropbox import send_signature_request
import sys

class TicketApp:
    def __init__(self, root):
        """ 
        Initialize the TicketApp GUI application.

        Args:
            root (tk.Tk): The root Tkinter window passed in from the main script.
        """
        self.root = root
        self.root.title("PDF Ticket Generator")

        self.data_path = ""
        self.pdf_path = os.path.join(os.path.dirname(__file__), "assets", "delivery_ticket_template.pdf")
        self.status_label = None

        self.setup_welcome_screen()

    def hide_all_frames(self):
        """
        Hide all frame widgets in the application.

        This method loops through all attributes of the class that end with '_frame'
        and calls `pack_forget()` on each, effectively hiding them from view.
        Useful when switching between different UI screens.
        """
        for frame in [getattr(self, attr) for attr in dir(self) if attr.endswith("_frame")]:
            try:
                frame.pack_forget()
            except:
                pass

    def setup_welcome_screen(self):
        """
        Set up and display the welcome screen.

        This screen introduces the user to the application and provides
        buttons to view instructions or continue to the Excel/TSV upload screen.
        """
        self.hide_all_frames()
        self.welcome_frame = tk.Frame(self.root)
        self.welcome_frame.pack(padx=20, pady=20)

        tk.Label(self.welcome_frame, text="Welcome to the PDF Ticket Generator!", font=("Arial", 14)).pack(pady=(10, 5))
        tk.Label(self.welcome_frame, text="Follow the steps to generate tickets from your Excel file.", font=("Arial", 10)).pack(pady=(0, 15))

        tk.Button(self.welcome_frame, text="See instructions to extract claims from Quickbook", command=lambda: show_instructions(self.root)).pack(pady=(0, 5))
        tk.Button(self.welcome_frame, text="Continue", command=self.show_excel_screen).pack(pady=(0, 5))

    def show_main_ui(self):
        """
        Set up and display the main UI screen.

        Provides options to generate tickets and navigate back to data loading
        or the welcome screen. Also shows the status label for feedback.
        """
        self.hide_all_frames()
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=10)

        tk.Button(self.main_frame, text="Generate Tickets", command=self.generate).pack(pady=20)
        tk.Button(self.main_frame, text="Back to Load Data", command=self.show_excel_screen)
        tk.Button(self.main_frame, text="Back to Welcome", command=self.back_to_welcome).pack(pady=(0, 10))

        self.status_label = tk.Label(self.main_frame, text="", fg="green", font=("Arial", 10))
        self.status_label.pack()

    def show_excel_screen(self):
        """
        Set up and display the excel upload screen.

        Allows the user to select a QuickBooks Excel file for processing,
        and provides navigation to the next step or back to the welcome screen.
        """
        self.hide_all_frames()
        self.excel_frame = tk.Frame(self.root)
        self.excel_frame.pack(pady=10)

        tk.Label(self.excel_frame, text="Load the QuickBook Excel File", font=("Arial", 12)).pack(pady=(0, 10))
        self.status_label = tk.Label(self.excel_frame, text="", fg="green", font=("Arial", 10))
        self.status_label.pack(pady=10)

        tk.Button(self.excel_frame, text="Select Quickbook File", command=self.load_qb_data_excel).pack(pady=5)
        tk.Button(self.excel_frame, text="Next", command=self.show_main_ui).pack(pady=(20, 5))
        tk.Button(self.excel_frame, text="Back to Welcome", command=self.back_to_welcome).pack(pady=5)

    def back_to_welcome(self):
        """
        Return to the welcome screen by hiding all frames and showing the welcome frame.
        """
        self.hide_all_frames()
        self.welcome_frame.pack()

    def load_qb_data_excel(self):
        """
        Prompt the user to select a QuickBooks excel file.

        Sets the selected file path to `self.data_path` and updates the status label
        to confirm the file was loaded.
        """
        path = filedialog.askopenfilename(
            filetypes=[("QuickBooks files", "*.tsv *.xlsx *.xls"), ("All Files", "*.*")])
        if path:
            self.data_path = path
            filename = os.path.basename(self.data_path)
            self.status_label.config(text=f"Quickbook Data file(s) Loaded. Loaded: {filename}")
    
    def _show_preview_and_close_loader(self, pdf_paths):
        """
        Close the loading window and display the preview of generated PDF tickets.

        Args:
            pdf_paths (list[str]): List of file paths to the generated preview PDFs.
        """
        self.loading_window.destroy()
        self.preview_tickets(pdf_paths)

    def _generate_in_background_with_progress(self):
        """
        Generate preview tickets in a background thread while updating progress UI.

        - Processes the loaded Excel/TSV file,
        - Groups and sorts orders,
        - Generates previews with a progress callback,
        - Displays the preview once done.

        On failure, shows an error message and closes the loader window.
        """
        orders, _ = handle_file(self.data_path)
        orders.sort(key=lambda o: o[2].lower())
        self.orders_for_preview = orders
        try:
            orders, _ = handle_file(self.data_path)
            orders.sort(key=lambda o: o[2].lower())
            self.orders_for_preview = orders
 
            grouped = group_orders(orders)
            grouped.sort(key=lambda g: g[1])

            def update_progress(progress):
                # Update the progress bar value
                self.root.after(0, lambda: self.progress_var.set(progress))
                # Update the percentage label text, rounding to int for display
                self.root.after(0, lambda: self.progress_label.config(text=f"{int(progress)}%"))

            self.preview_data = generate_previews(grouped, self.pdf_path, progress_callback=update_progress)

            pdf_paths = [p[0] for p in self.preview_data]
            self.root.after(0, lambda: self._show_preview_and_close_loader(pdf_paths))

        except Exception as e:
            self.root.after(0, lambda e=e: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.loading_window.destroy)

    def generate(self):
        """
        Start the ticket generation process.

        Verifies required files are selected, then opens a loading window
        with a progress bar and starts background ticket generation.
        """
        if not self.data_path or not self.pdf_path:
            messagebox.showerror("Missing Files", "Please select Excel/TSV and PDF template.")
            return
        
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Generating Tickets...")
        self.loading_window.geometry("300x120")
        self.loading_window.resizable(False, False)
        self.loading_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent closing

        tk.Label(self.loading_window, text="Generating tickets, please wait...").pack(pady=(10, 5))

        # Progress bar widget
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.loading_window, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=(5, 10), fill='x', padx=20)

        # Percentage label
        self.progress_label = tk.Label(self.loading_window, text="0%")
        self.progress_label.pack(pady=(0, 10))

        # Start generation in background
        threading.Thread(target=self._generate_in_background_with_progress).start()

    def resource_path(self, relative_path):
        """
        Get the absolute path to a resource, whether running as a script or as a PyInstaller bundle.

        Parameters:
            relative_path (str): The relative path to the resource (e.g., 'assets/image.png').

        Returns:
            str: The absolute path to the resource file.
        """
        try: 
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def load_pdf_images(self, pdf_path):
        """
        Load the first page of a PDF file as a resized preview image.

        Converts the first page of the specified PDF to an image,
        resizes it to fit within 600px width, and stores it in `self.preview_images`.
        
        Args:
            pdf_path (str): Path to the PDF file to preview.
        """
        poppler_bin_path = self.resource_path('assets/poppler/Library/bin')
        pages = convert_from_path(pdf_path, dpi=150)
        first_page = pages[0]
        max_width = 600
        w_percent = max_width / float(first_page.size[0])
        h_size = int(float(first_page.size[1]) * w_percent)
        first_page = first_page.resize((max_width, h_size), Image.Resampling.LANCZOS)
        self.preview_images = [ImageTk.PhotoImage(first_page)]

    def next_ticket(self):
        """
        Navigate to the next ticket in the preview list.

        Loops back to the first ticket if the end is reached.
        Loads and displays the corresponding preview image.
        """
        if self.current_pdf_index + 1 < len(self.pdf_paths):
            self.current_pdf_index += 1
        else:
            self.current_pdf_index = 0
        self.load_pdf_images(self.pdf_paths[self.current_pdf_index])
        self.show_current_image()

    def prev_ticket(self):
        """
        Navigate to the previous ticket in the preview list.

        Loops to the last ticket if the beginning is passed.
        Loads and displays the corresponding preview image.
        """
        if self.current_pdf_index > 0:
            self.current_pdf_index -= 1
        else: 
            self.current_pdf_index = len(self.pdf_paths) - 1
        self.load_pdf_images(self.pdf_paths[self.current_pdf_index])
        self.show_current_image()

    def remove_ticket(self):
        """
        Remove the currently previewed ticket from the list.

        Prompts for confirmation. If confirmed, deletes the current ticket
        from both `self.pdf_paths` and `self.preview_data`.

        Closes the preview window if no tickets remain.
        """
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
        """
        Open a dialog for the user to choose a directory to save tickets.

        Returns:
            str: The selected directory path, or an empty string if cancelled.
        """
        return filedialog.askdirectory(title="Choose folder to save tickets")

    def save_all_tickets(self):
        """
        Save all remaining tickets to a user-selected directory.

        Validates that orders are loaded and prompts for output folder.
        Uses the ticket template to generate and save final PDF tickets.
        """
        if not self.orders_for_preview:
            messagebox.showerror("Error", "No orders loaded")
            return

        output_dir = self.choose_output_directory()
        if not output_dir:
            return

        orders_remaining = [group for _, group, _ in self.preview_data]
        generate_tickets(orders_remaining, self.pdf_path, output_dir)
        messagebox.showinfo("Saved", f"All tickets saved to:\n{output_dir}")

    def show_current_image(self):
        """
        Display the currently loaded preview image in the preview UI.

        Updates both the image and the page label showing current index.
        """
        self.preview_label.config(image=self.preview_images[0])
        self.preview_label.image = self.preview_images[0]  # keep reference
        self.page_label.config(
            text=f"Ticket {self.current_pdf_index + 1} of {len(self.pdf_paths)}"
        )
        self.preview_label.update_idletasks()  # Force update

    def send_to_docusign(self):
        """
        Send the currently previewed ticket PDF for signature via Dropbox Sign.

        - Retrieves the ticket info and signer email from the preview data.
        - Prompts the user for the signer's name (and email if missing).
        - Calls `send_signature_request()` with the signer info and PDF path.
        - Displays a success or error message based on the result.
        
        If required data is missing or invalid, displays appropriate error dialogs.
        """
        if not self.pdf_paths:
            messagebox.showerror("Error", "No tickets available to send.")
            return

        # Get the TicketInfo object for the current ticket
        try:
            _, ticket_info, signer_email = self.preview_data[self.current_pdf_index]
            signer_name = "John Doe"
            if signer_name is None:
                # User clicked "Cancel"
                messagebox.showinfo("Cancelled", "Signature request cancelled.")
                return

            signer_name = signer_name.strip()

            
        except Exception as e:
            messagebox.showerror("Error", f"Could not extract ticket info: {e}")
            return

        if not signer_email:
            signer_email = askstring("Missing Email", "Enter recipient's email address:")
            if not signer_email:
                return

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
        """
        Launch a new window to preview, navigate, delete, save, or send tickets.

        Args:
            pdf_paths (list[str]): List of file paths to generated preview PDFs.

        Creates a scrollable preview interface with:
        - PDF image display,
        - Page navigation controls (Next, Prev),
        - Save and remove buttons,
        - Option to send to Dropbox Sign.

        Also binds arrow keys for easier navigation.
        """
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
