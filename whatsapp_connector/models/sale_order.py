import requests
import json
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Override Odoo's native sales confirmation to auto-trigger our WhatsApp actions."""
        res = super(SaleOrder, self).action_confirm()
        for record in self:
            try:
                _logger.info(f"Automated execution: triggering action_send_whatsapp for {record.name}")
                record.action_send_whatsapp()
            except Exception as e:
                _logger.error(f"Automated confirmation alert failed for {record.name}. Error: {str(e)}")
        return res

    def action_send_whatsapp(self):
        """Dispatches template notifications matching the exact Twilio sandbox settings layout."""
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
            raise UserError("Please completely configure your WhatsApp API Key (Account SID and Auth Token) before sending!")

        for record in self:
            raw_phone = record.partner_id.phone or record.partner_id.mobile
            if not raw_phone:
                raise UserError(f"The customer {record.partner_id.name} does not have a valid phone number.")

            phone = raw_phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not phone.startswith('+'):
                phone = f"+{phone}"

            payload = {
                "From": f"whatsapp:{sender_number.replace('whatsapp:', '')}",  
                "To": f"whatsapp:{phone}",
                "ContentSid": template_id, 
                "ContentVariables": json.dumps({
                    "1": str(record.partner_id.name or "Customer"),   
                    "2": str(record.name or "Order")                  
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
                _logger.info(f"--- Sending request to Twilio for {record.name} ---")
                response = requests.post(
                    target_url, 
                    data=payload, 
                    auth=(account_sid, auth_token), 
                    timeout=10
                )
                
                if response.status_code == 201:
                    _logger.info(f"--- Message for {record.name} sent successfully! ---")
                    
                    # Clean HTML layout string
                    chatter_body = f"✅ WhatsApp Notification Sent: Confirmation message sent successfully via Twilio to {phone}."
                    
                    # By passing subtype_xmlid='mail.mt_note' and message_type='comment', 
                    # Odoo naturally permits basic inline text formatting tags like <strong> without escaping!
                    record.message_post(
                        body=chatter_body,
                        message_type='comment',
                        subtype_xmlid='mail.mt_note'
                    )
                else:
                    _logger.error(f"Twilio Gateway rejected request: {response.text}")
                    raise UserError(f"Twilio Gateway Error ({response.status_code}): {response.text}")
                    
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    error_msg = f"{e.response.status_code} - {e.response.text}"
                raise UserError(f"Failed to deliver WhatsApp message via gateway. Error details: {error_msg}")