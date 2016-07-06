# -*- coding: utf-8 -*-
from openerp import http

# class HsPts(http.Controller):
#     @http.route('/hs_pts/hs_pts/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_pts/hs_pts/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_pts.listing', {
#             'root': '/hs_pts/hs_pts',
#             'objects': http.request.env['hs_pts.hs_pts'].search([]),
#         })

#     @http.route('/hs_pts/hs_pts/objects/<model("hs_pts.hs_pts"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_pts.object', {
#             'object': obj
#         })