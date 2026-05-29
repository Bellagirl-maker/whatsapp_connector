{
    'name': 'Twilio WhatsApp Auto', 
    'version': '19.0.1.0.0',         
    'summary': 'Automated WhatsApp alerts for Sales Orders and Invoices.',
    'description': """
Twilio WhatsApp Automation Connector
====================================
This module seamlessly integrates Odoo with the Twilio WhatsApp API to send real-time notifications.
* Automatically sends an order confirmation message when a Sales Order is confirmed.
* Automatically sends a billing alert message when a Customer Invoice is validated (posted).
* Provides a manual 'Send WhatsApp' button inside Sales Orders.
* Logs delivery confirmations cleanly inside the Odoo document Chatter.
    """,
    'author': 'Bella Tech',
    'category': 'Sales/CRM',
    
    'images': [
        'static/description/banner.png'
    ],
    
    'depends': ['base', 'sale_management', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 49.00,                 
    'currency': 'EUR',               
    'license': 'LGPL-3',   
    'support': 'bellatech.odoo@gmail.com', 
}