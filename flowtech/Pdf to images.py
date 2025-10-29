from pdf2image import convert_from_path
import frappe, os

def convert_pdfs_before_save(doc, method=None):
    """
    Convert PDFs to images immediately before saving the document.
    """
    changed = False

    for row in doc.if_any_technical_documents_upload_here:
        if row.file and row.file.lower().endswith('.pdf') and not row.pdf_pages:
            # Get file path
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

    # No need to save again here, since we're in before_save
