import frappe
import csv
import os
import openpyxl
from frappe.utils.file_manager import get_files_path

@frappe.whitelist()
def upload_bulk_items(parent, file_url):
    """
    Upload CSV or Excel (.xlsx) data into 'items_details' child table of Order Enquiry,
    automatically fetching Warehouse and warehouse_qty from Bin based on Item.
    """

    # Locate uploaded file
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_path = os.path.join(get_files_path(), os.path.basename(file_doc.file_name))

    if not os.path.exists(file_path):
        frappe.throw(f"File not found: {file_path}")

    parent_doc = frappe.get_doc('Order Enquiry', parent)
    count = 0

    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()

    def get_warehouse(item_code):
        bin_doc = frappe.get_all("Bin", filters={"item_code": item_code}, fields=["warehouse", "actual_qty"])
        if bin_doc:
            return bin_doc[0]["warehouse"], bin_doc[0]["actual_qty"]
        return "", 0

    # ---------------- CSV Upload ----------------
    if file_ext == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = row.get('item')
                item_name = row.get('item_name')
                quantity = row.get('quantity')
                actual_price = row.get('actual_price')

                warehouse, warehouse_qty = get_warehouse(item)

                if item_name:
                    parent_doc.append('items_details', {
                        'item': item,
                        'item_name': item_name,
                        'quantity': quantity,
                        'actual_price': actual_price,
                        'warehouse': warehouse,
                        'warehouse_qty': warehouse_qty
                    })
                    count += 1

    # ---------------- Excel Upload ----------------
    elif file_ext == '.xlsx':
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]
        expected_columns = {"item", "item_name", "quantity", "actual_price"}

        if not expected_columns.issubset(set(headers)):
            frappe.throw(f"Missing columns in Excel file. Expected: {', '.join(expected_columns)}")

        idx = {header: headers.index(header) for header in headers}

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            item_code = row[idx["item"]]
            item_name = row[idx["item_name"]]
            quantity = row[idx["quantity"]]
            actual_price = row[idx["actual_price"]]

            warehouse, warehouse_qty = get_warehouse(item_code)

            parent_doc.append('items_details', {
                'item': item_code,
                'item_name': item_name,
                'quantity': quantity,
                'actual_price': actual_price,
                'warehouse': warehouse,
                'warehouse_qty': warehouse_qty
            })
            count += 1
    else:
        frappe.throw("Unsupported file format. Please upload a .csv or .xlsx file.")

    parent_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return f"✅ Successfully uploaded {count} items with Warehouse info."
