# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hide Margin of Sale',
    'version': '12.0.0.0.0',
    'author': 'Electricidad ESTURAO',
    'maintainer': 'Electricidad ESTURAO',
    'complexity': 'easy',
    'depends': ['sale_margin'],
    'license': 'AGPL-3',
    'category': 'Sale',
    'summary': 'Hide or show sales margin as needed',
    'images': ['static/description/icon.png',
               'static/description/ventas_checkbox.jpg',
               'static/description/ventas_con_margen.jpg',
               'static/description/ventas_sin_margen.jpg'
    ],
    'data': [
        'views/ee_sale_margin_checkbox_views.xml',
        'views/ee_sale_margin_margin_views.xml',
        'views/ee_sale_margin_sale_margin_sale_order_line_form_views.xml',
        'views/ee_sale_margin_sale_margin_sale_order_line_views.xml',
    ],
    'website': 'https://www.esturao.com/ee-sale-margin',
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
