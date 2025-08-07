import csv
import datetime
import pandas as pd
import math


def safe_str(value):
    if value is None:
        return ""
    try:
        if math.isnan(value):
            return ""
    except:
        pass
    return str(value)




def is_safe_mmddyyyy(line):
    try:
        datetime.datetime.strptime(line, "%m/%d/%Y")
        return True
    except (IndexError, ValueError, TypeError):
        return False


def is_valid_quantity(value):
    try:
        return int(float(value)) >= 0
    except (ValueError, TypeError):
        return False


def is_memo(row):
    """
    Identify memo rows based on these conditions:
    - 'Quantity' empty
    - 'Product/Service' empty
    - 'Product/service description' not empty
    - 'SKU' empty
    """
    return (
        row.get('Quantity', '') == '' and
        row.get('Product/Service', '') == '' and
        row.get('Product/service Description', '') != '' and
        row.get('SKU', '') == ''
    )


def handle_file(input_path):
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
                zip_code = row.get("Customer ship zip", "")
                zip_str = str(zip_code).zfill(5) if pd.notna(zip_code) and str(zip_code).strip() != '' else ''


                hcpcs_code = category.split()[0] if category else ''


                cleaned_rows.append([
                    row.get("Date", ""),
                    row.get("Customer first name", ""),
                    row.get("Customer last name", ""),
                    safe_str(row.get("Account number", "")),
                    row.get("Customer ship street", ""),
                    row.get("Customer ship city", ""),
                    row.get("Customer ship state", ""),
                    zip_str,
                    row.get("Customer phone", ""),
                    row.get("Customer email", ""),
                    str(quantity).strip(),
                    category,
                    description,
                    sku,
                    hcpcs_code
                ])
        return cleaned_rows, memos


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


        return cleaned_rows, memos


    else:
        raise ValueError("Unsupported file format. Only .tsv and .xlsx are supported.")





