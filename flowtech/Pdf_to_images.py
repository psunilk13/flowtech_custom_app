from pdf2image import convert_from_path
import frappe, os

@frappe.whitelist()
def auto_convert_pdfs(doc, method=None):
    """
    Automatically convert any uploaded PDFs in Technical Documents to images
    """
    changed = False

    for row in doc.if_any_technical_documents_upload_here:
        # Only convert if it's a PDF and not converted yet
        if row.file and row.file.lower().endswith('.pdf') and not row.pdf_pages:
            # Get File path
            file_doc = frappe.get_doc("File", {"file_url": row.file})
            file_path = os.path.join(frappe.get_site_path('public', 'files'), os.path.basename(file_doc.file_name))

            if os.path.exists(file_path):
                # Convert PDF to images
                pages = convert_from_path(file_path, dpi=150)
                image_urls = []

                for i, page in enumerate(pages, start=1):
                    image_filename = f"{os.path.splitext(file_doc.file_name)[0]}_page{i}.png"
                    image_path = os.path.join(frappe.get_site_path('public', 'files'), image_filename)
                    page.save(image_path, "PNG")
                    image_urls.append(f"/files/{image_filename}")

                # Store as comma-separated string
                row.pdf_pages = ','.join(image_urls)
                changed = True

    if changed:
        doc.save(ignore_permissions=True)
