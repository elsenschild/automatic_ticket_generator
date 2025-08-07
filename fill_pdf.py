import fitz  # PyMuPDF

def flatten_once(lst):
    """Flatten a list of lists into a single list.
    
    Args:
        list (list): A list of lists found in a invoice.

    Returns:
        A single list of items.
    """
    flat = []
    for el in lst:
        if isinstance(el, list):
            flat.extend(el)
        else:
            flat.append(el)
    return flat

def fill_pdf(ticket, template_path, output_path):
    """Fill a PDF template with data from a ticket and save it to a file.

    Args:
        ticket (dict): A dictionary containing the data to fill the template.
        template_path (str): The path to the PDF template.
        output_path (str): The path to save the filled PDF.
    
    Returns:
        None
    """
    doc = fitz.open(template_path)
    data = ticket.__dict__.copy()
    data["PatientName"] = f"{ticket.PatientLastName}. {ticket.PatientFirstName} ".strip()

    # Flatten HCodes list (one level) and get first word of each code string
    if "HCodes" in data and isinstance(data["HCodes"], list):
        data["Hcodes"] = flatten_once(data["HCodes"])
    else:
        data["HCodes"] = []

    list_fields = {
        "CodeDescription": "CodeDescriptions",
        "Code": "HCodes",
        "Item": "ICodes",
        "Units": "Units"
    }

    for page in doc:
        widgets = page.widgets()
        if not widgets:
            continue

        for widget in widgets:
            field_name = widget.field_name

            # Special fields
            if field_name == "Delivery":
                widget.field_value = "Yes"
                widget.update()
                continue

            if field_name in ("ServDate", "Date"):
                if data.get("Date"):
                    widget.field_value = str(data["Date"])
                    widget.update()
                continue

            # Scalar fields (non-list)
            if field_name in data and not isinstance(data[field_name], list):
                widget.field_value = str(data[field_name])
                widget.update()
                continue

            # List fields (like Units0, Code0, etc.)
            for prefix, data_key in sorted(list_fields.items(), key=lambda x: -len(x[0])):
                if field_name.startswith(prefix):
                    index_str = field_name[len(prefix):]
                    if index_str.isdigit():
                        idx = int(index_str)
                        if data_key in data and idx < len(data[data_key]):
                            value = data[data_key][idx]
                            if data_key == "Units":
                                try:
                                    value = str(int(float(value)))  # Convert "4.00" to "4"
                                except Exception:
                                    value = str(value)
                            else:
                                value = str(value)
                            widget.field_value = value
                            widget.update()
                    break

        page.wrap_contents()

    doc.save(output_path, deflate=True)
