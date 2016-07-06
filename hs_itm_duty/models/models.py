# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools, exceptions, _


class DutyRecord(models.Model):
    _name = 'hs_itm.duty.record'
    _description = 'Duty Record'
    _order = 'dutyday desc'
    _rec_name = 'dutyday'
    _inherit = ['mail.thread']

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    dutyday = fields.Date('Dutyday', required=True, default=fields.Datetime.now)

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_get, ondelete='restrict')
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True,
                              track_visibility='onchange')

    duty_begin_hour = fields.Integer('Begin Hour', default=8, required=True)
    duty_end_hour = fields.Integer('End Hour', default=17, required=True)

    description = fields.Text('Description')

    _sql_constraints = [('dutyrecordhour_constraint', 'CHECK (duty_end_hour >= duty_begin_hour)',
                         'Error ! End Hour cannot be set before Begin Hour.')]
