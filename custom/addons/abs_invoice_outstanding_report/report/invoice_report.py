# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2019-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError

class ReportInvoices(models.AbstractModel):
    _name = 'report.abs_invoice_outstanding_report.invoice_outstanding'

    '''Find Outstanding invoices between the date and find total outstanding amount'''
    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        outstanding_invoice = []       
        invoices = self.env['account.invoice'].search([('date_due', '>=', docs.start_date),('date_due', '<=', docs.end_date),('type','=', 'out_invoice'),('state','=','open')])
        if invoices:
            amount_due = 0
            for total_amount in invoices:
                amount_due += total_amount.residual
            docs.total_amount_due = amount_due

            return {
                'docs': docs,
                'invoices': invoices,
            }
        else:
            raise UserError("There is not any Outstanding invoice")
