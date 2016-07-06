# -*- coding: utf-8 -*-
{
    'name': "HSIT Production Traceability System Apps Base",

    'summary': """
        HSIT Production Traceability System Apps Common Library """,

    'description': """menu register.
    """,

    'author': "HSIT",
    'website': "http://www.hscarbonfibre.com",
    'category': 'Hengshen Addons',
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}