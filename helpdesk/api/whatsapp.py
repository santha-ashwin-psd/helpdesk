import frappe
from frappe import _
import requests

WHATSAPP_SOURCE = "WhatsApp"
WHATSAPP_PHONE_NUMBER_ID = "1269335696258495"
WHATSAPP_ACCESS_TOKEN = "EAAOdxd27ryMBSIHizRynHVzBhPZARbAXjkUiVB9GfiytEGJeoKwQSWuI4wMkcCwCFKsrZBzN6grT2krMFfW1EKLkCCnUykpjIqRWL4ZAYMmZC0OS7JyqhUvNXYcNSLcSx4qOLnJyDhds7rnjxXBlIRGSLlPdUrqVZCUPH3ZCyGSH01BnBDOYeH5MrcxKfUhAZDZD"

@frappe.whitelist()
def create_whatsapp_message(
    reference_doctype: str,
    reference_name: str,
    message: str,
    to: str,
    content_type: str = "text",
):
    """
    API Endpoint to send a WhatsApp message from Helpdesk.
    It sends the message via Meta Graph API and creates a WhatsApp Message record.
    """
    
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to.replace("+", "").replace(" ", ""),
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Helpdesk WhatsApp API Error")
        
    # Ensure the doctype is installed before logging
    if frappe.db.exists("DocType", "WhatsApp Message"):
        doc = frappe.new_doc("WhatsApp Message")
        doc.update(
            {
                "reference_doctype": reference_doctype,
                "reference_name": reference_name,
                "message": message,
                "to": to,
                "content_type": content_type,
            }
        )
        doc.insert(ignore_permissions=True)
        return doc.name

    return None
