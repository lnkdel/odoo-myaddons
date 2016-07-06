# -*- coding: utf-8 -*-
from openerp import http

# class HsItmDuty(http.Controller):
#     @http.route('/hs_itm_duty/hs_itm_duty/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hs_itm_duty/hs_itm_duty/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hs_itm_duty.listing', {
#             'root': '/hs_itm_duty/hs_itm_duty',
#             'objects': http.request.env['hs_itm_duty.hs_itm_duty'].search([]),
#         })

#     @http.route('/hs_itm_duty/hs_itm_duty/objects/<model("hs_itm_duty.hs_itm_duty"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hs_itm_duty.object', {
#             'object': obj
#         })