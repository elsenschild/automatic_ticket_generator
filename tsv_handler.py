"""
TSV Handler Module

Provides utility functions to clean and validate TSV data exported from QuickBooks.
Functions handle broken rows, strip quotes, validate dates and quantities, and 
extract meaningful ticket data for downstream processing.
"""
import csv
import datetime

def is_safe_mmddyyyy(line):
    """
    Check if a string is a valid date in MM/DD/YYYY format.

    Args:
        line (str): The string to validate.

    Returns:
        bool: True if the string is a valid date, False otherwise.
    """
    try:
        datetime.datetime.strptime(line, "%m/%d/%Y")
        return True
    except (IndexError, ValueError):
        return False

def is_valid_quantity(value):
    """
    Check if a value can be interpreted as a non-negative integer quantity.

    Args:
        value (str): The value to validate.

    Returns:
        bool: True if the value is a valid quantity, False otherwise.
    """
    try:
        return int(float(value)) >= 0
    except ValueError:
        return False
    
def del_quotes(rows):
    """
    Remove surrounding double quotes from field 13 of each row if present.

    Args:
        rows (list[list[str]]): A list of TSV data rows.

    Returns:
        list[list[str]]: Cleaned rows with quotes removed from the specified field.
    """
    new_rows = []
    for _, row in enumerate(rows):
        if len(row) > 11 and len(row[13]) > 1:
            if row[13][0] == '"' and row[13][-1] == '"':
                row[13] = row[13][1:-1]  # remove leading/trailing quote
        new_rows.append(row)
    return new_rows

def get_HCPCS_code(row):
    """
    Extract only the HCPCS code portion from field 11 of a row (before any spaces).

    Args:
        row (list[str]): A single TSV data row.

    Returns:
        list[str]: The updated row with a trimmed HCPCS code in field 11.
    """
    row[11] = row[11].split(' ')[0]
    return row

def is_memo(row):
    """
    Determine if a given row is a memo row based on field structure.

    A memo row typically has:
    - Length of 15
    - Fields 11, 12, and 14 are empty
    - Field 13 is not empty

    Args:
        row (list[str]): A single TSV data row.

    Returns:
        bool: True if the row matches the memo pattern, False otherwise.
    """
    if len(row) == 15:
        if row[11] == '' and row[12] == '' and len(row[13]) != '' and row[14] == '':
            return True
        return False
    return False

def handle_tsv(input_path):
    """
    Process and clean a TSV file exported from QuickBooks.

    - Strips metadata lines.
    - Reconstructs broken rows.
    - Filters for rows with valid quantities and HCPCS codes.
    - Separates out memo rows.
    - Cleans up newlines and quotes.

    Args:
        input_path (str): Path to the TSV file.

    Returns:
        tuple: (cleaned_rows, memos)
            - cleaned_rows (list[list[str]]): Valid item rows for ticket generation.
            - memos (list[list[str]]): Extracted memo rows.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        lines = list(reader)

    # Remove the first 5 and last 4 lines (usually metadata/junk). Do not need the headers on the 5th line.
    data_lines = lines[5:-4]

    if not data_lines:
        print("⚠️ No lines to process after trimming.")
        return

    # Extract header and start working on data
    fixed_lines = []
    current_row = []
    memos = []
    i=0
    for row in data_lines:
        if len(row) > 9:
            if current_row:
                if is_memo(current_row):
                    memos.append(current_row)
                elif (len(current_row) == 14 and is_valid_quantity(current_row[10])):
                    if get_HCPCS_code(current_row) not in fixed_lines:
                        fixed_lines.append(get_HCPCS_code(current_row))
                current_row = []
            current_row = row
        else:
            # Combine broken row
            if current_row and len(row) > 0:
                current_row = current_row[:-1] + [current_row[-1] + ' ' + row[0]] + row[1:]
            else:
                current_row = []
        i += 1
    # Append last row if valid
    if current_row and len(current_row) == 13 and is_valid_quantity(current_row[9]):
        fixed_lines.append(get_HCPCS_code(current_row))

    # Clean up newlines and quotes
    cleaned_rows = [[cell.replace('\n', '') for cell in line] for line in del_quotes(fixed_lines)]

    return cleaned_rows, memos