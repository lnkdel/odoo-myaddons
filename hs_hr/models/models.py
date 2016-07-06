# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Employee(models.Model):
    _inherit = ['hr.employee']
    _rec_name = 'display_name'
    _order = 'badge_no, name'

    badge_no = fields.Char('Badge No.', size=10, index=True)
    other_department_ids = fields.Many2many('hr.department', string='Other Departments')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    wechat_account = fields.Char('WeChat Account', index=True)

    _sql_constraints = [
        ('badge_no_unique', 'unique(badge_no)', u'Duplicated "Badge No"'),
        ('wechat_account_unique', 'unique(wechat_account)', u'Duplicated "WeChat Account"'),
    ]

    @api.one
    @api.depends('name', 'badge_no')
    def _compute_display_name(self):
        names = [self.badge_no, self.name]
        self.display_name = ' / '.join(filter(None, names))
