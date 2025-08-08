import csv
import datetime
import pandas as pd
import math

def safe_str(value):
    """
    Safely converts a value to string, returning an empty string for None or NaN.

    Parameters:
        value (any): The input value to be converted to a string.

    Returns:
        str: A safe string representation of the value or an empty string.
    """
    if value is None:
        return ""
    try:
        if math.isnan(value):
            return ""
    except:
        pass
    return str(value)


def is_safe_mmddyyyy(line):
    """
    Checks if the input string is a valid MM/DD/YYYY date.

    Parameters:
        line (str): The date string to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        datetime.datetime.strptime(line, "%m/%d/%Y")
        return True
    except (IndexError, ValueError, TypeError):
        return False


def is_valid_quantity(value):
    """
    Validates if the given value is a non-negative number (interpreted as quantity).

    Parameters:
        value (str | float | int): The quantity value to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        return int(float(value)) >= 0
    except (ValueError, TypeError):
        return False


def is_memo(row):
    """
    Determines if a row qualifies as a memo line based on QuickBooks export rules.

    Parameters:
        row (dict): The row dictionary from the TSV or Excel file.

    Returns:
        bool: True if it's a memo row, False otherwise.
    """
    return (
        row.get('Quantity', '') == '' and
        row.get('Product/Service', '') == '' and
        row.get('Product/service Description', '') != '' and
        row.get('SKU', '') == ''
    )


def remove_duplicates(rows):
    """
    Removes duplicate rows from a list of lists or dicts.

    Parameters:
        rows (list): A list of rows (each row is a list or dict).

    Returns:
        list: A list containing only unique rows.
    """
    seen = set()
    unique_rows = []
    for row in rows:
        row_tuple = tuple(row.items()) if isinstance(row, dict) else tuple(row)
        if row_tuple not in seen:
            seen.add(row_tuple)
            unique_rows.append(row)
    return unique_rows


def handle_file(input_path):
    """
    Reads, cleans, and processes a TSV or Excel (.xlsx) file of QuickBooks exports.
    Removes duplicates and separates memo lines.

    Parameters:
        input_path (str): Path to the input file (must be .xlsx or .tsv).

    Returns:
        tuple:
            - cleaned_rows (list): A list of cleaned data rows (list of values for Excel, dicts for TSV).
            - memos (list): A list of memo rows (only for TSV).
    """
    cleaned_rows = []
    memos = []

    if input_path.endswith(".xlsx"):
        df = pd.read_excel(input_path, skiprows=4)
        df.dropna(how="all", inplace=True)
        df.columns = [col.strip() for col in df.columns]

        for i, row in df.iterrows():
            quantity = row.get("Quantity", "")
            sku = str(row.get("SKU", "")).strip()
            category = str(row.get("Category", "")).strip()
            description = row.get("Product/service description", "")

            if is_valid_quantity(quantity) and sku != '':
                hcpcs_code = category.split()[0] if category else ''

                new_row = [
                    row.get("Date", ""),
                    row.get("Customer first name", ""),
                    safe_str(row.get("Customer middle name", "")),
                    row.get("Customer last name", ""),
                    safe_str(row.get("Account number", "")),
                    row.get("Customer ship street", ""),
                    row.get("Customer ship city", ""),
                    row.get("Customer ship state", ""),
                    row.get("Customer ship zip", ""),
                    row.get("Customer phone", ""),
                    row.get("Customer email", ""),
                    str(quantity).strip(),
                    category,
                    description,
                    sku,
                    hcpcs_code
                ]
                cleaned_rows.append(new_row)

        return remove_duplicates(cleaned_rows), memos

    elif input_path.endswith(".tsv"):
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            all_rows = list(reader)

        data_rows = all_rows[5:-4] if len(all_rows) > 9 else all_rows

        if not data_rows:
            print("⚠️ No data rows to process.")
            return [], []

        current_row = None

        for row in data_rows:
            date_val = row.get('Date', '')
            quantity_val = row.get('Quantity', '')

            if is_safe_mmddyyyy(date_val) and is_valid_quantity(quantity_val):
                if current_row:
                    if is_memo(current_row):
                        memos.append(current_row)
                    else:
                        cleaned_rows.append(current_row)
                current_row = row
            else:
                if current_row:
                    current_row['Product/Service Description'] = (
                        current_row.get('Product/Service Description', '') + ' ' + ' '.join(row.values()).strip()
                    )

        if current_row:
            if is_memo(current_row):
                memos.append(current_row)
            else:
                cleaned_rows.append(current_row)

        for row in cleaned_rows:
            category = row.get('Category', '')
            row['HCPCS'] = category.split()[0] if category else ''

        return remove_duplicates(cleaned_rows), memos

    else:
        raise ValueError("Unsupported file format. Only .tsv and .xlsx are supported.")
