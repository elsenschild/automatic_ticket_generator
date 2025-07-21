import os
import tempfile
from datetime import datetime
from ticket_info import TicketInfo  # Your dataclass
from fill_pdf import fill_pdf      # Your PDF fill function
import fitz  # PyMuPDF

# --- PDF Utility Functions --- #

def flatten_pdf(path):
    """
    Flatten form fields in a PDF so filled values become static content.
    """
    doc = fitz.open(path)
    for page in doc:
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                widget.update()
        page.wrap_contents()

    flat_path = path.replace(".pdf", "_flat.pdf")
    doc.save(flat_path, incremental=False, deflate=True)
    return flat_path

def format_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y").strftime("%m%d%Y")
    except Exception:
        return "unknown_date"

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).rstrip()

def same_order(order1, order2):
    return all(order1[i] == order2[i] for i in range(9))

def group_orders(orders):
    grouped = []
    i = 0
    while i < len(orders):
        j = i + 1
        base = orders[i][:10]  # Shared patient/order info
        units = [orders[i][10]]
        hcodes = [orders[i][11]]
        descriptions = [orders[i][12]]
        icodes = [orders[i][13]]

        while j < len(orders) and same_order(orders[i], orders[j]):
            units.append(orders[j][10])
            hcodes.append(orders[j][11])
            descriptions.append(orders[j][12])
            icodes.append(orders[j][13])
            j += 1

        group = base + [units, hcodes, descriptions, icodes]
        grouped.append(group)
        i = j

    return grouped

def create_ticket_from_group(row):
    if len(row) < 14:
        raise ValueError("Each row in a group must have at least 14 columns.")
    return TicketInfo(
        PatientFirstName=row[0],
        PatientLastName=row[1],
        AccountNum=row[2],
        StreetAddress=row[3],
        City=row[4],
        State=row[5],
        Zip=row[6],
        Date=row[7],
        Telephone=row[8],
        EmailAddress=row[9],
        Units=row[10],
        HCodes=row[11],
        CodeDescriptions=row[12],
        ICodes=row[13]
    )

def generate_previews(grouped_orders, pdf_template_path, progress_callback):
    """
    Generate temporary flattened PDFs for preview. Returns list of (path, group).
    """
    preview_pairs = []

    for index, group in enumerate(grouped_orders):
        ticket = create_ticket_from_group(group)
        temp_path = os.path.join(tempfile.gettempdir(), f"preview_{index}.pdf")
        fill_pdf(ticket, pdf_template_path, temp_path)
        flat_path = flatten_pdf(temp_path)
        preview_pairs.append((flat_path, group))

        if progress_callback:
            progress = ((index + 1) / len(grouped_orders)) * 100
            progress_callback(progress)

    return preview_pairs

def generate_tickets(order, pdf_template_path, output_dir="output"):
    """
    Fill and save final tickets into the specified output folder.
    """
    os.makedirs(output_dir, exist_ok=True)
    try:
        ticket = create_ticket_from_group(order)
    except ValueError as e:
        print(f"Skipping group  due to error: {e}")
    
    name = f"{ticket.PatientFirstName}_{ticket.PatientLastName}"
    filename = f"{sanitize_filename(name)}_{format_date(ticket.Date)}.pdf"
    output_path = os.path.join(output_dir, filename)
    fill_pdf(ticket, pdf_template_path, output_path)
