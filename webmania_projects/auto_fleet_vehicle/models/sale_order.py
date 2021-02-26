# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    our_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicules')

    @api.onchange('our_vehicle_id')
    def _get_partner_if_none(self):
      for o in self:
          if not o.partner_id:
               if o.our_vehicle_id:
                   o.partner_id = o.our_vehicle_id.driver_id
                   o.onchange_partner_id()            
