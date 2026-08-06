import frappe
from frappe import _
import requests

WHATSAPP_SOURCE = "WhatsApp"
WHATSAPP_PHONE_NUMBER_ID = "1269335696258495"
WHATSAPP_ACCESS_TOKEN = "EAAOdxd27ryMBSAIxYAIObC5Oak82qDhLAZAWrDBp3VaRxoeLfZBd0hjZBZC58pck0FcWBV2DFfd8GqWcoE9XwuD1hKQpuD5qldoYN0rT2EsNts8AE7O0ZC00wPEpkhbRLvXqJp0j5rpmrwPTsNy9jJzJaclBaakeowwgbtkZCwmRgcoEcmeejrApqe0mhOyAZDZD"
@frappe.whitelist()
def create_whatsapp_message(
    reference_doctype: str,
    reference_name: str,
    to: str,
    template_name: str = None,
    template_variables: str = None, # JSON encoded list
    message_body: str = None,
):
    """
    API Endpoint to send a WhatsApp message from Helpdesk.
    It sends the message via Meta Graph API.
    """
    
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    to = to.replace("+", "").replace(" ", "")
    if message_body:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message_body
            }
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en"
                },
                "components": []
            }
        }
        
        if template_variables:
            import json
            variables = json.loads(template_variables)
            if variables:
                parameters = [{"type": "text", "text": str(v)} for v in variables]
                payload["template"]["components"].append({
                    "type": "body",
                    "parameters": parameters
                })
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
    except Exception as e:
        error_msg = f"API Error: {str(e)}\n"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f"Response: {e.response.text}\n"
        error_msg += frappe.get_traceback()
        frappe.log_error(title="Helpdesk WhatsApp API Error", message=error_msg)
        
    return None
