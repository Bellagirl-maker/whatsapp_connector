import requests
import json
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """Override Odoo's native invoice posting validation to auto-trigger a WhatsApp billing alert."""
        res = super(AccountMove, self).action_post()
        for record in self:
            if record.move_type == 'out_invoice':
                try:
                    _logger.info(f"Automated Billing Action: triggering action_send_invoice_whatsapp for {record.name}")
                    record.action_send_invoice_whatsapp()
                except Exception as e:
                    _logger.error(f"Automated invoice WhatsApp alert failed for {record.name}. Error: {str(e)}")
        return res

    def action_send_invoice_whatsapp(self):
        """Dispatches an invoice notification matching the Twilio sandbox layout."""
        param_obj = self.env['ir.config_parameter'].sudo()
        
        api_key = (param_obj.get_param('whatsapp_connector.api_key') or '').strip()
        endpoint = (param_obj.get_param('whatsapp_connector.endpoint') or 'https://api.twilio.com').strip()
        sender_number = (param_obj.get_param('whatsapp_connector.sender_number') or '').strip()
        template_id = (param_obj.get_param('whatsapp_connector.template_id') or '').strip()

        if not template_id:
            template_id = 'HXb5b62575e6e4ff6129ad7c8efe1f983e'
        if not sender_number or sender_number == '+12402379750':
            sender_number = '+14155238886'

        if not api_key:
            raise UserError("Please configure your WhatsApp API Key before validating invoices!")

        for record in self:
            raw_phone = record.partner_id.phone or record.partner_id.mobile
            if not raw_phone:
                continue

            phone = raw_phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not phone.startswith('+'):
                phone = f"+{phone}"

            payload = {
                "From": f"whatsapp:{sender_number.replace('whatsapp:', '')}",  
                "To": f"whatsapp:{phone}",
                "ContentSid": template_id, 
                "ContentVariables": json.dumps({
                    "1": str(record.partner_id.name or "Customer"),       
                    "2": f"Invoice {record.name or 'Draft'}"             
                }) 
            }
            
            if 'AC' in api_key and ':' in api_key:
                account_sid = api_key.split(':')[0].strip()
                auth_token = api_key.split(':')[1].strip()
            else:
                account_sid = api_key.strip()
                auth_token = api_key.strip()

            base_url = endpoint
            if '/2010-04-01' in base_url:
                base_url = base_url.split('/2010-04-01')[0]
            
            target_url = f"{base_url}/2010-04-01/Accounts/{account_sid}/Messages.json"
            
            try:
                response = requests.post(target_url, data=payload, auth=(account_sid, auth_token), timeout=10)
                if response.status_code == 201:
                    _logger.info(f"--- Invoice WhatsApp message for {record.name} sent successfully! ---")
                    
                    # Clean HTML layout string
                    chatter_body = f"✅ WhatsApp Invoice Notification Sent: Billing summary sent successfully via Twilio to {phone}."
                    
                    # Pass the raw string directly with note subtypes
                    record.message_post(
                        body=chatter_body,
                        message_type='comment',
                        subtype_xmlid='mail.mt_note'
                    )
                else:
                    _logger.error(f"Twilio Invoice Notification rejected: {response.text}")
            except Exception as e:
                _logger.error(f"Failed to deliver invoice WhatsApp message. Error: {str(e)}")