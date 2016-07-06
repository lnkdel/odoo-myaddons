# -*- coding: utf-8 -*-
from openerp import http

# class HsHr(http.Controller):
#     @http.route('/hs_hr/hs_hr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_hr/hs_hr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_hr.listing', {
#             'root': '/hs_hr/hs_hr',
#             'objects': http.request.env['hs_hr.hs_hr'].search([]),
#         })

#     @http.route('/hs_hr/hs_hr/objects/<model("hs_hr.hs_hr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_hr.object', {
#             'object': obj
#         })