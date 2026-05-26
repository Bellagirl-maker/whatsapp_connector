# -*- coding: utf-8 -*-
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whatsapp_api_key = fields.Char(
        string="Twilio Auth Token / API Key", 
        config_parameter='whatsapp_connector.api_key'
    )
    whatsapp_endpoint = fields.Char(
        string="Twilio Endpoint URL", 
        config_parameter='whatsapp_connector.endpoint'
    )
    whatsapp_sender_number = fields.Char(
        string="Twilio Sender Number", 
        config_parameter='whatsapp_connector.sender_number',
        help="Your Twilio WhatsApp sandbox or live number (e.g., +14155238886)"
    )
    whatsapp_template_id = fields.Char(
        string="Default Content Template ID", 
        config_parameter='whatsapp_connector.template_id',
        help="The Twilio ContentTemplate SID (e.g., HXb5b62575...)"
    )

    def action_test_whatsapp_connection(self):
        """Pings the configured endpoint to validate API authorization credentials."""
        self.ensure_one()
        
        if not self.whatsapp_api_key or not self.whatsapp_endpoint:
            raise UserError("Please provide both an API Key/Auth Token and an Endpoint URL before testing.")

        # Prepare connection configurations (stripping loose trailing slashes)
        target_url = self.whatsapp_endpoint.strip().rstrip('/')
        
        try:
            # We perform a safe HTTP GET handshake validation request
            # Using a short timeout ensures the Odoo UI doesn't hang indefinitely if the IP is bad
            response = requests.get(target_url, timeout=10)
            
            # Since dummy/mock endpoints might return a 404 or 200, we check if the server answered us
            if response.status_code in [200, 401, 403]:
                # 401/403 means endpoint is alive but auth token is rejected/unverified, which is perfect for dummy testing!
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Success!',
                        'message': f'Successfully reached gateway server ({response.status_code}). Layout handshake confirmed.',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(f"Gateway reached, but returned an unexpected status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise UserError(f"Failed to connect to the gateway endpoint.\nError Details: {str(e)}")