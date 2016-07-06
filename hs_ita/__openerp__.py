# -*- coding: utf-8 -*-
{
    'name': 'HSIT IT Assets Management',
    'summary': 'IT Equipments, Assets, Hardware, Allocation Tracking',
    'description': """
        Track employees' and department's IT assets.""",
    'author': "HSIT",
    'website': "http://www.hscarbonfibre.com",
    'category': 'Hengshen Addons',
    'version': '0.1',
    'depends': ['hs_base', 'mail', 'hr'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}