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

import logging
from odoo import models, fields, exceptions, _

logger = logging.getLogger(__name__)


class SaleOrderMagento(models.Model):
    _inherit = 'sale.order'

    magento_id = fields.Char(string="Magento Id", readonly=True,
                             store=True)
    magento = fields.Boolean(string="Magento", readonly=True, store=True,
                             help="This order is created from magento.")
    magento_status = fields.Char(string="Magento status", readonly=True)
    magento_order_date = fields.Datetime(string="Magento Order Date")



class CustomerMagento(models.Model):
    _inherit = 'res.partner'

    magento = fields.Boolean(string="Magento", readonly=True, store=True,
                             help="This customer is created from magento."
                             )
    magento_id = fields.Char(string="Magento id",   store=True)
