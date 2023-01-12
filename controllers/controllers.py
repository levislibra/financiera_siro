# -*- coding: utf-8 -*-
from openerp import http

# class FinancieraSiro(http.Controller):
#     @http.route('/financiera_siro/financiera_siro/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/financiera_siro/financiera_siro/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('financiera_siro.listing', {
#             'root': '/financiera_siro/financiera_siro',
#             'objects': http.request.env['financiera_siro.financiera_siro'].search([]),
#         })

#     @http.route('/financiera_siro/financiera_siro/objects/<model("financiera_siro.financiera_siro"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('financiera_siro.object', {
#             'object': obj
#         })