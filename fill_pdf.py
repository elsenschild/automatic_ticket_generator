import fitz  # PyMuPDF

def flatten_once(lst):
    flat = []
    for el in lst:
        if isinstance(el, list):
            flat.extend(el)
        else:
            flat.append(el)
    return flat

def fill_pdf(ticket, template_path, output_path, flatten=True):
    doc = fitz.open(template_path)
    data = ticket.__dict__.copy()
    data["PatientName"] = f"{ticket.PatientLastName}, {ticket.PatientFirstName}".strip()

    if "HCodes" in data and isinstance(data["HCodes"], list):
        data["HCodes"] = flatten_once(data["HCodes"])
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

            # Handle Delivery checkbox (and any checkboxes)
            if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX and field_name == "Delivery":
                widget.field_value = "Yes"
                widget.update()
                
                # Manually draw checkmark over checkbox bounds
                rect = widget.rect
                checkmark = "✔"  # Or use "X" or whatever you want

                page.insert_textbox(
                    rect,
                    checkmark,
                    fontsize=12,
                    align=1,  # Centered
                )
                continue

            if field_name in ("ServDate", "Date"):
                if data.get("Date"):
                    widget.field_value = str(data["Date"])
                    widget.update()
                continue

            if field_name in data and not isinstance(data[field_name], list):
                widget.field_value = str(data[field_name])
                widget.update()
                continue

            for prefix, data_key in sorted(list_fields.items(), key=lambda x: -len(x[0])):
                if field_name.startswith(prefix):
                    index_str = field_name[len(prefix):]
                    if index_str.isdigit():
                        idx = int(index_str)
                        if data_key in data and idx < len(data[data_key]):
                            value = data[data_key][idx]
                            if data_key == "Units":
                                try:
                                    value = str(int(float(value)))
                                except Exception:
                                    value = str(value)
                            widget.field_value = str(value)
                            widget.update()
                    break

        page.wrap_contents()

    if flatten:
        READONLY_FLAG = 1 << 0  # read-only bit
        for page in doc:
            widgets = page.widgets()
            if widgets:
                for widget in widgets:
                    current_flags = widget.field_flags or 0
                    widget.field_flags = current_flags | READONLY_FLAG
                    widget.update()
            page.wrap_contents()

    doc.save(output_path, deflate=True)
