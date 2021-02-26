# -*- coding: utf-8 -*-


from odoo import fields, models, _, api
from datetime import date, datetime

MATRICULES = [
        ('123456 A 67', '123456 A 67'),
        ('89899 B 6', '89899 B 6'),
        ('90673 A 54', '90673 A 54'),
        ('88888 H 9', '88888 H 9'),
        ('33333 W 2', '33333 W 2'),
        ]

class ResPartner(models.Model):
    _inherit = 'res.partner'

    am_is_driver = fields.Boolean(string='Est un chauffeur', default=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    am_driver_id = fields.Many2one('res.partner',string='Chauffeur', domain=[('am_is_driver','=',True)])
    matric_vdriver = fields.Selection(MATRICULES, string="Matricule")

    def action_confirm(self):
        am_driver_id = False
        matric_vdriver = False
        for r in self:
            am_driver_id = r.am_driver_id and r.am_driver_id.id or False
            matric_vdriver = r.matric_vdriver

        return super(SaleOrder, self.with_context(default_am_driver_id=am_driver_id, 
            default_matric_vdriver=matric_vdriver)).action_confirm()

    @api.multi
    def _prepare_invoice(self):
        values_res = super(SaleOrder, self)._prepare_invoice()
        am_driver_id = self.am_driver_id and self.am_driver_id.id or False
        matric_vdriver = self.matric_vdriver
        values_res.update(am_driver_id=am_driver_id, matric_vdriver=matric_vdriver)
        return values_res


class StockMove(models.Model):
    _inherit = 'stock.move'

    prd_categ_id = fields.Many2one('product.category', related='product_id.categ_id', store=True)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    am_driver_id = fields.Many2one('res.partner',string='Chauffeur', domain=[('am_is_driver','=',True)],)
    matric_vdriver = fields.Selection(MATRICULES, string="Matricule")


    @api.model
    def create(self, values):
        res = super(AccountInvoice, self).create(values)
        return res


class stockPicking(models.Model):
    _inherit = 'stock.picking'

    am_driver_id = fields.Many2one('res.partner',string='Chauffeur', domain=[('am_is_driver','=',True)],
        )
    matric_vdriver = fields.Selection(MATRICULES, string="Matricule")


    @api.model
    def create(self, values):
        res = super(stockPicking, self).create(values)
        return res

    @api.onchange('group_id')
    def get_driver(self):
        for r in self:
            if r.group_id and r.group_id.sale_id:
                r.am_driver_id = r.group_id.sale_id.am_driver_id and r.group_id.sale_id.am_driver_id.id
                r.matric_vdriver = r.group_id.sale_id.matric_vdriver and r.group_id.sale_id.matric_vdriver

    @api.constrains('am_driver_id', 'matric_vdriver')
    def save_driver_set_to_relations(self):
        context = self._context or {}
        if context.get('ignore_others','other') != 'majid':
            for r in self:
                if r.sudo().group_id and r.sudo().group_id.sale_id:
                    #devis
                    r.sudo().group_id.sale_id.write({
                        'am_driver_id': r.am_driver_id and r.am_driver_id.id or False,
                        'matric_vdriver': r.matric_vdriver,
                        })
                    #facture
                    if r.sudo().group_id.sale_id.invoice_ids:
                        r.sudo().group_id.sale_id.invoice_ids.write({
                            'am_driver_id': r.am_driver_id and r.am_driver_id.id or False,
                        'matric_vdriver': r.matric_vdriver,
                            })
                    #stock pickings
                    self.with_context(ignore_others='majid').sudo().env['stock.picking'].search([('group_id', '=', r.group_id.id), ('id','!=', r.id)]).write({
                        'am_driver_id': r.am_driver_id and r.am_driver_id.id or False,
                        'matric_vdriver': r.matric_vdriver,
                        })


    def get_data_grouped(self):

        grouped_categ= {}
        dates = []
        devis = []
        chauffeur, matric_vdriver = '', ''
        for doc in self:
            dates.append(fields.Date.from_string(doc.scheduled_date).strftime("%m/%d/%Y"))
            devis.append(doc.origin)
            if not chauffeur and doc.am_driver_id:
                chauffeur = doc.am_driver_id.name
                matric_vdriver = doc.matric_vdriver or ''
            for move in doc.move_ids_without_package:
                categ_id = move.product_id.categ_id or False
                categ_key = categ_id.id if categ_id else 'Indefinie'
                if not grouped_categ.get(categ_key, False):
                    if categ_id:
                        grouped_categ[categ_key] = {
                                           'categ': categ_id, 
                                           'categ_name': categ_id.name, 
                                           'move_ids_without_package': self.env['stock.move'],
                                            }
                    else:
                        grouped_categ[categ_key] = {
                                           'categ': False, 
                                           'categ_name': 'Indefinie', 
                                           'move_ids_without_package': self.env['stock.move'],
                                            }

                grouped_categ[categ_key]['move_ids_without_package'] += move

        res = {'pickings': self, 
        'pickings_str':", ".join([s.name for s in self]), 
        'origin': ", ".join(devis), 
        'scheduled_date': ", ".join(dates),
        'grouped': grouped_categ,
        'chauffeur' : chauffeur,
        'matricule' : matric_vdriver,
        }
        return res

    def group_move_lines_by_log(self, moves):
        res = {

        }
        for mv in moves:
            for ml in mv.move_line_ids:
                if not res.get("%s_%s"%(ml.product_id.id, ml.lot_id and ml.lot_id.id or "Indefinie"), False):
                    res["%s_%s"%(ml.product_id.id, ml.lot_id and ml.lot_id.id or "Indefinie")]={
                        'product_id': ml.product_id,
                        'product_uom_qty': ml.product_uom_qty,
                        'qty_done': ml.qty_done,
                        'product_uom_id': ml.product_uom_id,
                        'location_id': ml.location_id,
                        'package_id': ml.package_id,
                        'location_dest_id': ml.location_dest_id,
                        'result_package_id': ml.result_package_id,
                        'lot_id': ml.lot_id or False,
                    }
                else:
                    res["%s_%s"%(ml.product_id.id, ml.lot_id and ml.lot_id.id or "Indefinie")]['product_uom_qty'] += ml.product_uom_qty
                    res["%s_%s"%(ml.product_id.id, ml.lot_id and ml.lot_id.id or "Indefinie")]['qty_done'] += ml.qty_done

        return res


