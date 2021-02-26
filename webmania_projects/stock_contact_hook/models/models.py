# -*- coding: utf-8 -*-


from odoo import fields, models, _, api
from datetime import date, datetime


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.onchange('partner_shipping_id')
	def _onchange_partner_shipping_id_am(self):
		for r in self:
			if r.partner_shipping_id:
				if r.partner_shipping_id.warehouse_id or (r.partner_id and r.partner_id.warehouse_id):
					r.warehouse_id = (r.partner_shipping_id.warehouse_id and r.partner_shipping_id.warehouse_id.id) or (r.partner_id and r.partner_id.warehouse_id and r.partner_id.warehouse_id.id)
	    
