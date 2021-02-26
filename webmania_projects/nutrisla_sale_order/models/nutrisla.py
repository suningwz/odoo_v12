# -*- coding: utf-8 -*-

from odoo import models, fields, api



class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'
    number_of_packs = fields.Integer('Nombre de packs')


    @api.onchange('number_of_packs','product_packaging')
    def set_product_uom(self):
                pack = self.product_packaging
                self.product_uom_qty = pack.qty * self.number_of_packs