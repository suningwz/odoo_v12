# -*- coding: utf-8 -*-
{
    'name': "Addarissa Auto",
    'summary': """Record Addarissa Auto Information""",
    'author': "Driss El mouedden",
    'company': 'Webmania Solutions',
    'website': "https://www.webmania.ma",
    'category': 'Extra Tools',
    'version': '12.0.1.0.0',
    'depends': ['base','sale','fleet'],
    'data': [
        'views/product_views.xml',
        'views/fleet_vehicle_views.xml',
        'reports/sale_report_inherit.xml',
    ],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}