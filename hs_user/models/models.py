# -*- coding: utf-8 -*-

from openerp import models, fields, api


class User(models.TransientModel):
    _name = 'hs_user.wizard'
    _description = 'Change Password User'

    user_ids = fields.Many2many('res.users', string='User', required=True)
    new_passwd = fields.Char('New Password', default='', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'user_ids': active_ids}
        return res

    @api.multi
    def change_password_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        users = self.env['res.users'].search([('id', 'in', active_ids)])
        users.write({'password': self.new_passwd})
        return {'type': 'ir.actions.act_window_close'}