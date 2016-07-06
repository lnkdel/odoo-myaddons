# -*- coding: utf-8 -*-
{
    'name': 'HSIT IT Management - Duty',
    'summary': 'IT Management, Duty record',
    'description': """
        Duty record""",
    'author': "HSIT",
    'website': "http://www.hscarbonfibre.com",
    'category': 'Hengshen Addons',
    'version': '0.1',
    'depends': ['hs_base', 'hs_itm', 'mail'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}