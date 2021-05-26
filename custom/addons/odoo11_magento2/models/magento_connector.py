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
import json
from odoo import models, fields, api, exceptions, _
logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    logger.info("Unable to import requests, please install it with pip install requests")


class MagentoConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    access_token = fields.Char(string="Access Token")
    magento_host = fields.Char(string="Magento Host")

    @api.model
    def get_values(self):
        res = super(MagentoConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        access_token = ICPSudo.get_param('odoo11_magento2.access_token')
        magento_host = ICPSudo.get_param('odoo11_magento2.magento_host')

        res.update(
            access_token=access_token,
            magento_host=magento_host,
        )
        return res

    @api.multi
    def set_values(self):
        super(MagentoConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("odoo11_magento2.access_token", self.access_token)
        ICPSudo.set_param("odoo11_magento2.magento_host", self.magento_host)


class MagentoConnect(models.Model):
    _name = 'magento.connector'

    def magento_api_call(self, **kwargs):
        """
        We will be running the api calls from here
        :param kwargs: dictionary with all the necessary parameters,
        such as url, header, data,request type, etc
        :return: response obtained for the api call
        """
        if not kwargs:
            # no arguments passed
            return

        ICPSudo = self.env['ir.config_parameter'].sudo()
        # fetching access token from settings
        try:
            access_token = ICPSudo.get_param('odoo11_magento2.access_token')
        except:
            access_token = False
            pass
        # fetching host name
        try:
            magento_host = ICPSudo.get_param('odoo11_magento2.magento_host')
        except:
            magento_host = False
            pass
        if not access_token or not magento_host:
            raise exceptions.Warning(_('Please check the magento configurations!'))
            return

        type = kwargs.get('type') or 'GET'

        complete_url = 'http://'+magento_host+kwargs.get('url')
        logger.info("%s", complete_url)
        headers = kwargs.get('headers')
        headers['Authorization'] = 'Bearer ' + access_token

        data = json.dumps(kwargs.get('data')) if kwargs.get('data') else None
        try:
            res = requests.request(type, complete_url, headers=headers, data=data)
            items = json.loads(res.text)

            return items
        except Exception as e:
            logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured 5 %s") %e)
        return
