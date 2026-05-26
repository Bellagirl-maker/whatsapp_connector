# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WhatsAppService(models.AbstractModel):
    _name = 'whatsapp.connector.service'
    _description = 'Universal WhatsApp Gateway Connector Service'

    @api.model
    def send_whatsapp_message(self, recipient_number, message_body=None, template_variables=None):
        """
        Universal method to dispatch WhatsApp messages via Twilio API.
        :param recipient_number: String (e.g., '+233241234567')
        :param message_body: String (Optional fallback text body)
        :param template_variables: Dict or List (Optional parameters for Twilio Content Templates)
        """
        # 1. Fetch saved system credentials from Phase 2 data persistence layer
        param_obj = self.env['ir.config_parameter'].sudo()
        api_key = param_obj.get_param('whatsapp_connector.api_key')
        endpoint = param_obj.get_param('whatsapp_connector.endpoint')
        sender = param_obj.get_param('whatsapp_connector.sender_number')
        template_id = param_obj.get_param('whatsapp_connector.template_id')

        # 2. Prevent execution if core configurations are completely missing
        if not api_key or not endpoint or not sender:
            _logger.error("WhatsApp Send Failed: Missing API gateway configuration credentials.")
            raise UserError("WhatsApp gateway is not configured. Please check your settings panel.")

        # 3. Clean and format numbers for WhatsApp routing ecosystem
        # Twilio requires 'whatsapp:' prefix for both sender and receiver identifiers
        formatted_sender = f"whatsapp:{sender.strip()}" if not sender.startswith('whatsapp:') else sender.strip()
        formatted_recipient = f"whatsapp:{recipient_number.strip()}" if not recipient_number.strip().startswith('whatsapp:') else recipient_number.strip()

        # 4. Construct standard Twilio payload API endpoint URL
        # Normalizes: https://api.twilio.com/2010-04-01/Accounts/{Your_Account_SID}/Messages.json
        target_url = endpoint.strip().rstrip('/')
        if not target_url.endswith('Messages.json'):
            # Fallback if raw endpoint URL is provided without API message routing endpoints
            if 'Messages.json' not in target_url:
                target_url = f"{target_url}/Messages.json"

        # 5. Build dynamic messaging payload packet headers/body
        payload = {
            'From': formatted_sender,
            'To': formatted_recipient,
        }

        # Handle Template vs Raw text body conditional parsing switches
        if template_id and template_variables:
            payload['ContentSid'] = template_id
            payload['ContentVariables'] = str(template_variables) # Twilio expects stringified JSON object values
        elif message_body:
            payload['Body'] = message_body
        else:
            raise UserError("Cannot send message: Both message body and template references are empty.")

        # Extract Account SID from the Token/Key string (Twilio uses SID as Username in basic auth)
        # Assuming format contains account SID or uses standard token mapping structures
        account_sid = api_key.split(':')[0] if ':' in api_key else api_key

        try:
            _logger.info(f"Sending WhatsApp message to {formatted_recipient} via gateway...")
            
            # Execute actual HTTP POST transaction packet request
            response = requests.post(
                target_url,
                data=payload,
                auth=(account_sid, api_key),
                timeout=15
            )

            # 6. Evaluate HTTP transmission results status blocks
            if response.status_code in [200, 201]:
                _logger.info(f"WhatsApp message successfully queued via Twilio SID: {response.json().get('sid')}")
                return True
            else:
                _logger.error(f"WhatsApp Gateway Rejected Packet: Status {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            _logger.error(f"WhatsApp Service Gateway Network Crash Exception: {str(e)}")
            return False