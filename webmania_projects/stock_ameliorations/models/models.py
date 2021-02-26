# -*- coding: utf-8 -*-


from odoo import fields, models, _, api
from datetime import date, datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def name_get(self):
        res = []
        for partner in self:
            name = partner._get_name()
            res.append((partner.id, name + (", %s"%partner.city if partner.city else '')))
        return res




class StockPicking(models.Model):
    _inherit = 'stock.picking'

    city = fields.Char("Ville", related="partner_id.city", store=True)


	

	

	
