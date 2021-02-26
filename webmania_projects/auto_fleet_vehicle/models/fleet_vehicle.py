# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FleetVehicle(models.Model):

    _inherit = 'fleet.vehicle'

    def _compute_sale_order(self):
       for o in self:
           o.sale_orders_count = len(o.sale_order_ids)

    sale_order_ids = fields.One2many('sale.order', 'our_vehicle_id', 'Devis/Bon commandes')
    sale_orders_count = fields.Integer('Sale orders', default=0, compute=_compute_sale_order)
