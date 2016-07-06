# -*- coding: utf-8 -*-
{
    'name': "HSIT PTS - Composite Material Semi Product",

    'summary': """
        HSIT Production Traceability -- Composite Material Semi Product""",

    'description': """
        manage the data of semi product for prepreg, fabric, resin, sizing
    """,

    'author': "HSIT",
    'website': "http://www.hscarbonfibre.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hengshen Addons',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hs_base', 'hs_pts', 'mail', 'barcodes', 'resource'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'report/prepreg_label.xml',
        'views/plan_workflow.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}