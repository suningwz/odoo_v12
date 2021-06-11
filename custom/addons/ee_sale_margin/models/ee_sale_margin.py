# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    hide_margin =fields.Boolean("Hide margin", default=True, help='Hide or show sales margin as needed.')

    
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    hide_margin = fields.Boolean(related='order_id.hide_margin')
