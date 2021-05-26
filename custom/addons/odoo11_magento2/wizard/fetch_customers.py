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


class CustomerFetchWizard(models.Model):
    _name = 'customer.fetch.wizard'
    _inherit = 'order.fetch.wizard'

    def fetch_customers(self):
        """Fetch products"""
        PartnerObj = self.env['res.partner']
        cr = self._cr
        url = '/rest/V1/customers/search?searchCriteria=0'
        type = 'GET'
        customer_list = self.env['magento.connector'].magento_api_call(headers={}, url=url, type=type)
        try:
            items = customer_list['items']

            cr.execute("select magento_id from res_partner "
                       "where magento_id is not null")
            partners = cr.fetchall()
            partner_ids = [i[0] for i in partners] if partners else []

            # need to fetch the complete required fields list
            # and their values

            cr.execute("select id from ir_model "
                       "where model='res.partner'")
            partner_model = cr.fetchone()

            if not partner_model:
                return
            cr.execute("select name from ir_model_fields "
                       "where model_id=%s and required=True "
                       " and store=True",
                       (partner_model[0], ))
            res = cr.fetchall()
            fields_list = [i[0] for i in res if res] or []
            partner_vals = PartnerObj.default_get(fields_list)

            for i in items:
                if str(i['id']) not in partner_ids:

                    customer_id = self.find_customer_id(
                            i,
                            partner_ids,
                            partner_vals,
                            main=True
                    )

                    if customer_id:
                        _logger.info("Customer is created with id %s", customer_id)
                    else:
                        _logger.info("Unable to create order")
            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }

        except Exception as e:
            _logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)
