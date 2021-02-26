# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    occasion_ok = fields.Boolean(string="Pièce d'occasion",index=True)