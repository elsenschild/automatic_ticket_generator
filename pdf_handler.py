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
    return all(order1[i] == order2[i] for i in range(9))


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
    """
    Create a ticket from a group of orders.

    Args:
        row: One row from the inputed tsv file.
    
    Returns: 
        dict (TicketInfo): A dictionary containing the ticket information.
    """
    if len(row) < 14:
        raise ValueError("Each row in a group must have at least 14 columns.")
    return TicketInfo(
        Date=row[0],
        PatientFirstName=row[1],
        PatientLastName=row[2],
        AccountNum=row[3],
        StreetAddress=row[4],
        City=row[5],
        State=row[6],
        Zip=row[7],
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
        fill_pdf(ticket, pdf_template_path, temp_path)
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
        print("Order:", order)
        try:
            ticket = create_ticket_from_group(order)
        except ValueError as e:
            print(f"Skipping group  due to error: {e}")
        
        name = f"{ticket.PatientFirstName}_{ticket.PatientLastName}"
        if ticket.EmailAddress == "":
            folder = "mailed"
        else:
            folder = "emailed"
        filename = f"{folder}/{sanitize_filename(name)}_{format_date(ticket.Date)}.pdf"
        output_path = os.path.join(output_dir, filename)
        fill_pdf(ticket, pdf_template_path, output_path)