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


class ProductsFetchWizard(models.Model):
    _name = 'update.stock.wizard'

    fetch_type = fields.Selection([
        ('to_odoo', 'Import stock status'),
        ('from_odoo', 'Export stock status')
    ], string="Operation Type")

    def update_stock_item(self):
        Connector = self.env['magento.connector']
        UpdateQtyWiz = self.env['stock.change.product.qty']
        default_location = None
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)],
                                                       limit=1)
        if warehouse:
            default_location = warehouse.lot_stock_id
        active_ids = self._context.get('active_ids')
        cr = self._cr
        if self.fetch_type == 'to_odoo':
            type = 'GET'
            url = "/rest/V1/products/{sku}?fields=price,extension_attributes"
            sku_list = self._get_product_list(active_ids)

            for item in sku_list:
                location_id = item.location_id
                if not location_id and default_location:
                    location_id = default_location
                elif not location_id:
                    continue
                if item.default_code:
                    product_url = url.replace("{sku}", item.default_code)
                    stock_item = Connector.magento_api_call(
                            headers={},
                            url=product_url,
                            type=type
                    )
                    try:
                        if stock_item.get('extension_attributes') and \
                                stock_item['extension_attributes'].get('stock_item'):
                            product_stock = stock_item['extension_attributes']['stock_item']
                            # updating qty on hand
                            inventory_wizard = UpdateQtyWiz.create({
                                'product_id': item.id,
                                'product_tmpl_id': item.product_tmpl_id.id,
                                'new_quantity': product_stock['qty'],
                                'location_id': location_id.id,
                            })
                            inventory_wizard.change_product_qty()
                            # updating unit price if changed
                            if stock_item['price'] != item.list_price:
                                cr.execute("update product_template set list_price=%s "
                                           "where id=%s",
                                           (stock_item['price'], item.product_tmpl_id.id))
                            logger.info("Successfully Updated %s", item.default_code)
                    except:
                        pass
            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }
        elif self.fetch_type == 'from_odoo':
            sku_list = self._get_product_list(active_ids)
            for product in sku_list:
                if product.type == 'product' and product.default_code:
                    try:
                        data = {
                            "product": {
                                "sku": product.default_code,
                                "price": product.list_price,
                                "extensionAttributes": {
                                    "stockItem": {
                                        "qty": product.qty_available,
                                        "isInStock": True
                                    }
                                }
                            },
                            "saveOptions": True
                        }
                        type = 'POST'
                        product_url = "/rest/V1/products"
                        stock_item = Connector.magento_api_call(
                            headers={'Content-Type': 'application/json'},
                            url=product_url,
                            type=type,
                            data=data
                        )

                    except:
                        pass
            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }
        return

    def _get_product_list(self, active_ids):
        sku_list = {}
        if self._context.get('active_model') == 'product.product':
            sku_list = self.env['product.product'].search([
                ('magento_id', '!=', None),
                ('id', 'in', active_ids)
            ])
        if self._context.get('active_model') == 'product.template':
            sku_list = self.env['product.product'].search([
                ('magento_id', '!=', None),
                ('product_tmpl_id', 'in', active_ids)
            ])
        return sku_list