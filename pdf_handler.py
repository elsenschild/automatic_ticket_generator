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

    Args:
        path (str): Path to the PDF file.
    
    Returns: 
        str: Path to the flattened PDF file.
    """
    doc = fitz.open(path)

    for page in doc:
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                # Ensure appearance is generated for all fields, especially checkboxes
                if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    widget.field_value = widget.field_value  # Force assignment
                widget.update()
        page.wrap_contents()

    flat_path = path.replace(".pdf", "_flat.pdf")
    doc.save(flat_path, incremental=False, deflate=True)
    return flat_path


def format_date(date_str):
    """
    Format a date string into a human-readable format.

    Args:
        date_str (str): Date string in the format 'YYYY-MM-DD'.

    Returns:
        str: Formatted date string in the format 'Month Day, Year'.
    """
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y").strftime("%m%d%Y")
    except Exception:
        return "unknown_date"


def sanitize_filename(name):
    """
    Sanitize a string to create a safe filename.

    Removes any characters that are not alphanumeric, spaces, underscores, or hyphens.
    Trailing whitespace is also removed.

    Args:
        name (str): The original filename or string to sanitize.

    Returns:
        str: A cleaned version of the string safe to use as a filename.
    """
    return "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).rstrip()


def same_order(order1, order2):
    """ Checks if two rows in the invoice tsv are a part of the same ticket. 

    Args:
        order1 (list): The first row of the invoice tsv being examined.
        order2 (list): The second row of the invoice tsv being examined.
    
    Returns: 
        bool: True if the two rows are a part of the same ticket, False otherwise.
    """
    return all(order1[i] == order2[i] for i in range(10))


def group_orders(orders):
    """ Groups rows in the invoice csv file by their first 10 fields to combine all the data from one order together

    Args:
        orders: A list of 13 entries from each invoice

    Returns: 
        list: A list of lists, where each sublist contains all the data from one order
    """
    grouped = []
    i = 0
    while i < len(orders):
        j = i + 1
        base = orders[i][:11]  # Shared patient/order info
        units = [orders[i][11]]
        hcodes = [orders[i][12]]
        descriptions = [orders[i][13]]
        icodes = [orders[i][14]]

        while j < len(orders) and same_order(orders[i], orders[j]):
            units.append(orders[j][11])
            hcodes.append(orders[j][12])
            descriptions.append(orders[j][13])
            icodes.append(orders[j][14])
            j += 1

        group = base + [units, hcodes, descriptions, icodes]
        grouped.append(group)
        i = j

    return grouped


def create_ticket_from_group(row):
    """
    Create a ticket from a group of orders.

    Args:
        row: One row from the inputed tsv file.
    
    Returns: 
        dict (TicketInfo): A dictionary containing the ticket information.
    """
    if len(row) < 15:
        raise ValueError("Each row in a group must have at least 15 columns.")
    
    # Ensure blank or NaN email and middle initial stays as an empty string
    middle_intial = row[2]
    if not middle_intial or str(middle_intial).strip().lower() == "nan":
        middle_intial = ""
    email = row[10]
    if not email or str(email).strip().lower() == "nan":
        email = ""

    return TicketInfo(
        Date=row[0],
        PatientFirstName=row[1],
        PatientMiddleIntial=middle_intial,
        PatientLastName=row[3],
        AccountNum=row[4],
        StreetAddress=row[5],
        City=row[6],
        State=row[7],
        Zip=row[8],
        Telephone=row[9],
        EmailAddress=email,
        Units=row[11],
        HCodes=row[12],
        CodeDescriptions=row[13],
        ICodes=row[14]
    )

def generate_previews(grouped_orders, pdf_template_path, progress_callback):
    """
    Generate temporary flattened PDFs for preview. Returns list of (path, group).

    Args:
        grouped_orders (list): List of groups of invoices combined into a single order.
        pdf_template_path (str): Path to PDF template ticket file.
        progress_callback (function): Function to call with progress updates.

    Returns:
        list: List of tuples containing the path to the temporary preview PDF and the corresponding group of orders
    """
    preview_pairs = []

    for index, group in enumerate(grouped_orders):
        ticket = create_ticket_from_group(group)
        temp_path = os.path.join(tempfile.gettempdir(), f"preview_{index}.pdf")
        fill_pdf(ticket, pdf_template_path, temp_path, flatten=True)
        flat_path = flatten_pdf(temp_path)
        preview_pairs.append((flat_path, group, ticket.EmailAddress))

        if progress_callback:
            progress = ((index + 1) / len(grouped_orders)) * 100
            progress_callback(progress)

    return preview_pairs

def generate_tickets(orders, pdf_template_path, output_dir="output"):
    """
    Fill and save final tickets into the specified output folder.
    """
    for order in orders:
        os.makedirs(output_dir, exist_ok=True)
        try:
            ticket = create_ticket_from_group(order)
        except ValueError as e:
            print(f"Skipping group  due to error: {e}")
        
        name = f"{ticket.PatientLastName}, {ticket.PatientFirstName}"
        subfolder = "emailed" if ticket.EmailAddress else "mailed"
        filename = f"{sanitize_filename(name)} delivery ticket {format_date(ticket.Date)}.pdf"
        folder_path = os.path.join(output_dir, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        output_path = os.path.join(folder_path, filename)
        fill_pdf(ticket, pdf_template_path, output_path)