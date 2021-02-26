# -*- coding: utf-8 -*-
from odoo import http

# class Nutrisla(http.Controller):
#     @http.route('/nutrisla/nutrisla/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nutrisla/nutrisla/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('nutrisla.listing', {
#             'root': '/nutrisla/nutrisla',
#             'objects': http.request.env['nutrisla.nutrisla'].search([]),
#         })

#     @http.route('/nutrisla/nutrisla/objects/<model("nutrisla.nutrisla"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nutrisla.object', {
#             'object': obj
#         })