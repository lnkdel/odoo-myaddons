# -*- coding: utf-8 -*-
from openerp import http

# class HsIta(http.Controller):
#     @http.route('/hs_ita/hs_ita/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_ita/hs_ita/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_ita.listing', {
#             'root': '/hs_ita/hs_ita',
#             'objects': http.request.env['hs_ita.hs_ita'].search([]),
#         })

#     @http.route('/hs_ita/hs_ita/objects/<model("hs_ita.hs_ita"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_ita.object', {
#             'object': obj
#         })