# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Users(models.Model):
    _inherit = ['res.users']
    _rec_name = 'display_name'
    _order = 'login'

    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    @api.one
    @api.depends('login', 'partner_id.name')
    def _compute_display_name(self):
        names = [self.login, self.partner_id.name]
        self.display_name = ' / '.join(filter(None, names))

    @api.model
    def create(self, vals):
        new_record = super(Users, self).create(vals)
        # Set default email by login, and avoiding the issue while creating "Template User" in auth_signup module.
        if new_record.login != 'portaltemplate':
            new_record.email = new_record.login
        return new_record
