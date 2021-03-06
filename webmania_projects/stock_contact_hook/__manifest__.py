# encoding: utf-8
##############################################################################
#
#    Localisation marocaine module for OpenERP, Localisation marocaine, Les bases
#    Copyright (C) 2014 (<http://www.example.org>) Anonym
#
#    This file is a part of Localisation marocaine
#
#    Localisation marocaine is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Localisation marocaine is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Contact stock',
    'version': '12.0',
    'author': 'Abdelmajid Elhamdaoui',
    'category': 'stock',
    'summary': 'Contact warehouse,',
    'description': """
Driver sale order and stock picking
    """,
    'website': 'elhamdaouiabdelmajid@gmail.com',
    'images': [],
    'depends': ['select_customer_warehouse'],
    'data': [
        'security/security.xml',
        'views/views.xml',
        'reports/reports.xml',
    ],
    "qweb": [
    ],
    'demo': [

    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
