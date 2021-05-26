# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
{
    'name': 'Odoo Magento 2.3 Connector',
    'version': '12.0.1.0.0',
    'summary': 'Synchronize data between Odoo and Magento',
    'description': 'Synchronize data between Odoo and Magento',
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'sale_management', 'stock'],
    'website': 'https://cybrosys.com',
    'data': ['security/ir.model.access.csv',
             'data/magento_data.xml',
             'views/views.xml',
             'views/products_view.xml',
             'views/orders_view.xml',
             'views/invoice_view.xml',
             'views/invoice_stock_move_view.xml',
             'wizard/fetch_products_wiz.xml',
             'wizard/fetch_orders_wiz.xml',
             'wizard/fetch_customers_wiz.xml',
             'wizard/update_stock.xml',
             ],
    'images': ['static/description/banner.png'],         
    'license': 'OPL-1',
    'price': 49,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
