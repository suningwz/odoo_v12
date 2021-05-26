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

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    magento = fields.Boolean(string="Magento", readonly=True, store=True,
                             help="This invoice is created from magento.")
    magento_id = fields.Integer(string="Magento Id")
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist', string='Pricelist',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id_account_invoice_pricelist(self):
        result = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id and self.type in ('out_invoice', 'out_refund') \
                and self.partner_id.property_product_pricelist:
            self.pricelist_id = self.partner_id.property_product_pricelist
        return result

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        values = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        if invoice.pricelist_id:
            values.update({
                'pricelist_id': invoice.pricelist_id.id,
            })
        return values


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('product_id', 'quantity', 'uom_id')
    def _onchange_product_id_account_invoice_pricelist(self):
        if not self.invoice_id.pricelist_id or not self.invoice_id.partner_id:
            return
        product = self.product_id.with_context(
            lang=self.invoice_id.partner_id.lang,
            partner=self.invoice_id.partner_id.id,
            quantity=self.quantity,
            date_order=self.invoice_id.date_invoice,
            pricelist=self.invoice_id.pricelist_id.id,
            uom=self.uom_id.id,
            fiscal_position=(
                self.invoice_id.partner_id.property_account_position_id.id)
        )
        self.price_unit = self.env['account.tax']._fix_tax_included_price(
            product.price, product.taxes_id, self.invoice_line_tax_ids)

    @api.multi
    def update_from_pricelist(self):

        for line in self.filtered(lambda r: r.invoice_id.state == 'draft'):
            line._onchange_product_id_account_invoice_pricelist()


class AccountTax(models.Model):
    _inherit = 'account.tax'

    magento = fields.Boolean(string="Magento", readonly=True)
    magento_id = fields.Char(string="Magento Id")


class AccountTaxRate(models.Model):
    _name = 'account.tax.rate'

    magento_id = fields.Char()
    tax_country_id = fields.Char()
    rate = fields.Float()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    magento_id = fields.Char(string="Magento ID of product")