# Ticket Generator

A desktop Python application for generating delivery tickets from QuickBooks TSV exports, previewing them as PDFs, and optionally sending them for signature via Dropbox Sign.

---

## Features

- Generate formatted delivery ticket PDFs from TSV data
- Preview tickets directly in the app
- Request e-signatures via Dropbox Sign
- Restrict editing to only specific signature fields
- Automatically handles multi-order grouping
- Designed for compatibility with PyInstaller (Windows one-file executables)

---

## Requirements

- Python 3.8 or higher
- Windows 10+ (tested)
- [Dropbox Sign API Key](https://app.hellosign.com/api/applications)

---

## Installation

1. **Clone or download the repository**  
   ```bash
   git clone https://github.com/your-username/ticket_generator.git
   cd ticket_generator
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv buildenv311
   buildenv311\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file**
   ```dotenv
   DROPBOX_SIGN_API_KEY=your_api_key_here
   ```

---

## Usage

Run the application:

```bash
python main.py
```

Then:
- Load a `.tsv` export from QuickBooks
- Review and group ticket data
- Preview individual tickets
- Send for e-signature using your Dropbox Sign account

---

## Development Tips

- PDF logic is managed in `pdf_handler.py`
- Dropbox Sign fields are defined in `send_to_docusign()` within `ticket_app.py`
- Temporary previews are stored in the `tdemp/` folder

---

## Packaging with PyInstaller

To create a standalone `.exe`:

```bash
pyinstaller --clean --onefile main.py --icon "assets\ticket_icon.ico" --add-data "assets\delivery_ticket_template.pdf;assets" --add-data "assets\qb_instructions.png;assets" --add-binary "assets\poppler;poppler_bin" --paths "buildenv311\Lib\site-packages" --collect-all pandas --collect-all numpy --collect-all dropbox_sign --collect-all pdf2image --collect-all PyMuPDF --collect-all dotenv --collect-all PIL --collect-all requests --collect-all openpyxl --hidden-import dropbox_sign.apis --hidden-import dropbox_sign.models --hidden-import pkg_resources --hidden-import setuptools --collect-submodules pkg_resources --collect-submodules setuptools
```

---
## 👤 Author

Emily Light
