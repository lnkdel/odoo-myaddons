# -*- coding: utf-8 -*-
{
    'name': "HSIT Employee Directory",
    'summary': 'Jobs, Departments, Employees Details',
    'description': """
Extents the "hr application".
=============================

Add unique "Badge No" field to "hr.employee".
Add "display_name" and set as the default Name of "hr.employee".
Add "Other Departments" field to "hr.employee".

    """,
    'author': "HSIT",
    'website': "http://www.hscarbonfibre.com",
    'category': 'Hengshen Addons',
    'version': '0.1',
    'depends': ['hs_base', 'hr'],
    'data': [
        # 'security/ir.model.access.csv',
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