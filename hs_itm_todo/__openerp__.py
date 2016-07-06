# -*- coding: utf-8 -*-
{
    'name': 'HSIT IT Management - ToDo',
    'summary': 'IT Management, ToDo Tasks, Planing。。。',
    'description': """
        Track IT employees' ToDo Tasks.""",
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
        'data/data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}