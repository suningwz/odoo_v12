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
from odoo import models, exceptions, _

_logger = logging.getLogger(__name__)


class OrderFetchWizard(models.Model):
    _name = 'order.fetch.wizard'

    def find_customer_id(self, item, ids, partner_vals, main=False):
        cr = self._cr
        id_key = 'customer_id'
        pre_key = 'customer_'
        if main:
            id_key = 'id'
            pre_key = ''
        if item.get(id_key) and \
                str(item[id_key]) in ids:
            cr.execute("select id from res_partner "
                       "where magento_id=%s",
                       (str(item[id_key]),))
            res = cr.fetchone()
            return res and res[0] or None
        else:
            partner_vals['name'] = (item.get('firstname') or item.get(
                'customer_firstname') or "") + " " + (item.get(
                'lastname') or item.get('customer_lastname') or "")
            partner_vals['display_name'] = (item.get('firstname') or item.get(
                'customer_firstname') or "") + " " + (item.get(
                'lastname') or item.get('customer_lastname') or "")
            partner_vals['magento'] = True
            partner_vals['active'] = True
            partner_vals['customer'] = True
            partner_vals['magento_id'] = item.get(id_key)
            partner_vals['email'] = item.get('email')
            try:
                partner_vals['phone'] = item['custom_attributes'][0]['value']
            except:
                pass
            try:
                partner_vals['city'] = item['addresses'][0]['city']
                partner_vals['country_id'] = self.env['res.country'].search(
                    [('code', '=', item['addresses'][0]['country_id'])]).id
                partner_vals['zip'] = item['addresses'][0]['postcode']
                partner_vals['street'] = item['addresses'][0]['street'][0]
                partner_vals['street'] = item['addresses'][0]['street'][1]

            except:
                pass

            query_cols = self.fetch_query(partner_vals)
            query_str = "insert into res_partner (" + \
                        query_cols + ") values %s RETURNING id"
            cr.execute(query_str,
                       (tuple(partner_vals.values()),))
            res = cr.fetchone()
            return res and res[0] or None

    def fetch_query(self, vals):
        """constructing the query, from the provided column names"""
        query_str = ""
        if not vals:
            return
        for col in vals:
            query_str += " " + str(col) + ","
        return query_str[:-1]

    def fetch_orders(self):
        """Fetch products"""
        PartnerObj = self.env['res.partner']
        OrderObj = self.env['sale.order']
        ProductObj = self.env['product.product']
        cr = self._cr
        self.fetch_taxes()
        # url = '/rest/V1/products?searchCriteria[pageSize]=0'
        # we are fetching all the records without checking that
        # they already exist or not, because, if we try to setup a filter,
        # then the url may become too long and cause some other errors
        url = '/rest/V1/orders?searchCriteria=0'
        type = 'GET'
        order_list = self.env['magento.connector'].magento_api_call(headers={},
                                                                    url=url,
                                                                    type=type)
        try:
            items = order_list['items']

            cr.execute("select magento_id from sale_order "
                       "where magento_id is not null")
            orders = cr.fetchall()
            order_ids = [i[0] for i in orders] if orders else []

            cr.execute("select magento_id from res_partner "
                       "where magento_id is not null")
            partners = cr.fetchall()
            partner_ids = [i[0] for i in partners] if partners else []

            # need to fetch the complete required fields list
            # and their values
            cr.execute("select id from ir_model "
                       "where model='sale.order'")
            order_model = cr.fetchone()

            if not order_model:
                return
            cr.execute("select name from ir_model_fields "
                       "where model_id=%s and required=True "
                       " and store=True",
                       (order_model[0],))
            res = cr.fetchall()
            fields_list = [i[0] for i in res if res] or []
            order_vals = OrderObj.default_get(fields_list)

            cr.execute("select id from ir_model "
                       "where model='res.partner'")
            partner_model = cr.fetchone()

            if not partner_model:
                return
            cr.execute("select name from ir_model_fields "
                       "where model_id=%s and required=True"
                       " and store=True",
                       (partner_model[0],))
            res = cr.fetchall()
            fields_list = [i[0] for i in res if res] or []
            partner_vals = PartnerObj.default_get(fields_list)

            for i in items:
                if str(i['increment_id']) not in order_ids:

                    # this is a new order
                    # check the customer associated with the order, if the customer is new,
                    # then create a new customer, otherwise select existing record
                    customer_id = self.find_customer_id(i, partner_ids,
                                                        partner_vals,
                                                        main=False)
                    if i['customer_is_guest'] == 0:
                        partner_ids.append(str(i['customer_id']) if i['customer_id'] not in partner_ids else None)
                    order_vals['magento'] = True
                    order_vals['magento_id'] = str(i['increment_id'])
                    order_vals['partner_id'] = customer_id
                    order_vals['magento_status'] = i.get('state') \
                                                   or i.get('status')
                    order_vals['date_order'] = i.get(
                        'created_at')

                    order_line = []
                    prod_rec = []
                    for line in i['items']:
                        try:
                            custom_list = line['sku'].rsplit("-", len(
                                line['product_option']['extension_attributes'][
                                    'custom_options']))
                        except:
                            custom_list = line['sku'].rsplit("-", 0)

                        for val in custom_list:
                            tax_name = (self.env[
                                'account.tax'].search(
                                [('amount', '=',
                                  line['tax_percent']), (
                                     'magento', '=',
                                     True)])).ids if 'tax_percent' in line else []
                            if line['price'] != 0:
                                prod_rec = ProductObj.search(
                                    [('default_code', '=', val)], limit=1)
                            if not prod_rec:
                                continue
                            temp = {
                                'product_id': prod_rec.id,
                                'product_uom_qty': line['qty_ordered'],
                                'price_unit': line['price_incl_tax'] or 0,
                                'tax_id': [(6, 0, tax_name)],
                            }
                            order_line.append((0, 0, temp))
                        order_vals['order_line'] = order_line

                    ship_product_id = []
                    if i['shipping_amount']:
                        template_search = self.env[
                            'product.template']. \
                            search(
                            [('name', '=', 'Shipping Charge'),
                             ('type', '=', 'service')])
                        ship_tax = (self.env[
                            'account.tax'].search(
                            [('amount', '=', i['shipping_tax_amount']),
                             ('magento', '=', True)])).ids
                        ProductAccount = template_search._get_product_accounts()
                        if template_search:
                            product_search = self.env[
                                'product.product'].search(
                                [('product_tmpl_id', '=',
                                  template_search.id)])
                            ship = {
                                'name': 'Shipping Charge',
                                'product_id': product_search.id,
                                'product_uom_qty': 1,
                                'price_unit': i[
                                    'shipping_incl_tax'],
                                'tax_id': [
                                    (6, 0, ship_tax)],
                            }
                        else:
                            ship_product = self.env[
                                'product.product'].create(
                                {'name': 'Shipping Charge',
                                 'type': 'service'})
                            ProductAccount = ship_product.product_tmpl_id._get_product_accounts()
                            ship = {
                                'name': ship_product.name,
                                'product_id': ship_product.id,
                                'product_uom_qty': 1,
                                'price_unit': i[
                                    'shipping_incl_tax'],
                                'tax_id': [
                                    (6, 0, ship_tax)],
                            }
                        order_line.append((0, 0, ship))
                        ship_product_id.append(ship['product_id'])
                    order_vals['order_line'] = order_line

                    if 'message_follower_ids' in order_vals:
                        order_vals.pop('message_follower_ids')
                    order_vals['name'] = self.env['ir.sequence'].next_by_code(
                        'sale.order')
                    order_id = OrderObj.create(order_vals)
                    if order_id:
                        self._create_invoice_magento(order_id)
                        _logger.info("Order created with id %s", order_id.name)
                    else:
                        _logger.info("Unable to create order")
                else:
                    curent_order_id = OrderObj.search([('magento_id', '=', i['increment_id'])])
                    if i['status'] != curent_order_id['magento_status']:
                        curent_order_id['magento_status'] = i['status']
                        curent_order_id['date_order'] = i['created_at']
                    if self.env['account.invoice'].search([('origin', '=', curent_order_id.name)]):
                        self._create_invoice_magento(curent_order_id)


            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }

        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured 4 %s") % e)

    def fetch_taxes(self):
        cr = self._cr
        taxUrl = '/rest/V1/taxRates/search?searchCriteria=0'
        taxRates = self.env['magento.connector'].magento_api_call(headers={},
                                                                  url=taxUrl,
                                                                  type='GET')
        for tax_rate in taxRates['items']:
            cr.execute(
                """SELECT id FROM account_tax WHERE magento_id = '%s'""" %
                tax_rate['id'])
            rates = cr.fetchall()
            if not rates:
                tax_rate.update({
                    'magento_id': tax_rate['id'],
                    'name': tax_rate['code'],
                    'type_tax_use': 'sale',
                    'amount_type': 'percent',
                    'amount': tax_rate['rate'],
                    'magento': True,
                    'price_include': True,
                    'include_base_amount': True,
                    'tax_group_id': self.env['account.tax.group'].search([],
                                                                         limit=1).id,
                })
                self.env['account.tax'].create(tax_rate)

    def _create_invoice_magento(self, order_id):
        url = '/rest/V1/invoices?searchCriteria[filter_groups][0][filters][0][' \
              'field]=increment_id&searchCriteria[filter_groups][0][filters][0][' \
              'condition_type]=eq"&searchCriteria[filter_groups][0][filters][0][value]={id} '
        type = 'GET'
        config_url = url.replace('{id}', str(order_id.magento_id))
        check_invoice = self.env['magento.connector'].magento_api_call(headers={},
                                                                       url=config_url,
                                                                       type=type)
        if check_invoice.get('items'):
            # order_id.action_confirm()
            inv_id = order_id.action_invoice_create()
            inv = self.env['account.invoice'].search([('id', '=', inv_id)])
            inv.update({'magento': True, })
