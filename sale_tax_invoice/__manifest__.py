# -*- coding: utf-8 -*-
{
    'name': "Sale Tax invoice",
    'version': "15.0.1.0",
    'summary': """
        tax invoice""",

    'description': """
              """,
    'author': "Smart Do.",
    'company': "Smart Do.",
    'category': 'Sales',
    'depends': ['sale'],
    'live_test_url': 'https://youtu.be/RN2ha0Ttlo8',
    'data': [
        'security/ir.model.access.csv',
        #'data/salary_rule.xml',
        'wizard/tax_generator.xml',
        'report/final_invoice_report.xml',
        'report/reports.xml',
        'views/account_move.xml',
        

            ],
    'website': "https://smartdo-tech.com/",
    'images': ['static/description/eos.jpg'],
    'support':"info@smartdo-tech.com",
    'auto_install': False,
    'installable': True,
    
}