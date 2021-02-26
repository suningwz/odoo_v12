# -*- coding: utf-8 -*-


from odoo import fields, models, _, api
from datetime import date, datetime


class SaleOrder(models.Model):
	_inherit = 'sale.order'


from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    warehouse_quantity = fields.Html(compute='_get_warehouse_quantity_warehouse', string='Disponibilité')

    @api.depends('product_id')
    def _get_warehouse_quantity_warehouse(self):
        for record in self:
            warehouse_quantity_text = ''
            product_id = record.product_id
            if product_id:
                quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
                t_warehouses = {}
                for quant in quant_ids:
                    if quant.location_id:
                        if quant.location_id not in t_warehouses:
                            t_warehouses.update({quant.location_id:0})
                        t_warehouses[quant.location_id] += quant.quantity

                tt_warehouses = {}
                for location in t_warehouses:
                    warehouse = False
                    location1 = location
                    while (not warehouse and location1):
                        warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
                        if len(warehouse_id) > 0:
                            warehouse = True
                        else:
                            warehouse = False
                        location1 = location1.location_id
                    if warehouse_id:
                        if warehouse_id.name not in tt_warehouses:
                            tt_warehouses.update({warehouse_id.name:0})
                        tt_warehouses[warehouse_id.name] += t_warehouses[location]

                for item in tt_warehouses:
                    if tt_warehouses[item] != 0:
                    	if record.warehouse_id and record.warehouse_id.name == item:
                    		warehouse_quantity_text = warehouse_quantity_text + ' <b>** ' + item + ': ' + str(tt_warehouses[item]) + '<b/><br/>'
                    	else:
                        	warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(tt_warehouses[item]) + '<br/>'
                record.warehouse_quantity = warehouse_quantity_text

