# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools, exceptions, _


class Category(models.Model):
    _name = 'hs_ita.category'
    _description = 'Category'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    asset_ids = fields.One2many('hs_ita.asset', 'category_id', string='Assets')
    attribute_ids = fields.One2many('hs_ita.attribute', 'category_id', string='Attributes')
    asset_qty = fields.Integer(string="Asset Qty", compute='_compute_asset_qty')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another category already exists with this name!"),
    ]

    @api.multi
    def _compute_asset_qty(self):
        asset_data = self.env['hs_ita.asset'].read_group([('category_id', 'in', self.ids)], ['category_id'], ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in asset_data])
        for category in self:
            category.asset_qty = mapped_data.get(category.id, 0)

    @api.multi
    def unlink(self):
        for category in self:
            if category.asset_ids:
                raise exceptions.UserError(_("You cannot delete a category containing assets."))
        res = super(Category, self).unlink()
        return res


class Attribute(models.Model):
    _name = 'hs_ita.attribute'
    _description = 'Attribute'
    _order = 'category_id, sequence, name'
    _rec_name = 'display_name'

    name = fields.Char('Name', required=True)
    value = fields.Char('Value', required=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    category_id = fields.Many2one('hs_ita.category', string='Category', ondelete='restrict', track_visibility='onchange')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    @api.one
    @api.depends('name', 'value')
    def _compute_display_name(self):
        names = [self.name, self.value]
        self.display_name = ': '.join(filter(None, names))


class Brand(models.Model):
    _name = 'hs_ita.brand'
    _description = 'Brand'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    asset_ids = fields.One2many('hs_ita.asset', 'brand_id', string='Assets')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another brand already exists with this name!"),
    ]


class Asset(models.Model):
    _name = 'hs_ita.asset'
    _inherit = ['mail.thread']
    _rec_name = 'asset_no'
    _description = 'Asset'
    _order = 'asset_no'

    asset_no = fields.Char('Asset No.', required=True, default='ITA000')
    employee_id = fields.Many2one('hr.employee', string='Assigned to Employee', ondelete='restrict',
                                  track_visibility='onchange')
    department_id = fields.Many2one('hr.department', string='Assigned to Department', ondelete='restrict',
                                    track_visibility='onchange')
    category_id = fields.Many2one('hs_ita.category', string='Category', ondelete='restrict',
                                  track_visibility='onchange')
    brand_id = fields.Many2one('hs_ita.brand', string='Brand', ondelete='restrict',
                               track_visibility='onchange')
    model_no = fields.Char('Model No.', track_visibility='onchange')
    serial_no = fields.Char('Serial No.', track_visibility='onchange')
    attribute_ids = fields.Many2many('hs_ita.attribute', string='Attributes', track_visibility='onchange')
    assign_date = fields.Date('Assigned Date', track_visibility='onchange')
    use = fields.Selection(
        [('general office', 'General Office'), ('internal office', 'Internal Office'),
         ('external office', 'External Office'), ('it infrastructure', 'IT Infrastructure'),
         ('production equipment', 'Production Equipment')],
        string='Use', translate=True)
    cost = fields.Float('Cost')
    note = fields.Text('Note')
    warranty = fields.Date('Warranty')
    image = fields.Binary('Asset Image', attachment=True,
                          help="This field holds the image used as picture for the asset.")
    location_id = fields.Many2one('hs_ita.location', string='Location', ondelete='restrict',
                                  track_visibility='onchange')
    finance_asset_no = fields.Char('Finance Asset No.', track_visibility='onchange')
    po_no = fields.Char('PO Number')
    start_date = fields.Date('Start Date')
    active = fields.Boolean('Active?', default=True)
    count_item_ids = fields.One2many('hs_ita.count.item', 'asset_id', string='Count Records')
    cancel_date = fields.Date('Cancel Date', track_visibility='onchange')
    cancel_type = fields.Selection([('retired', 'Retired'), ('damaged', 'Damaged'), ('lost', 'Lost'),
                                    ('sold', 'Sold'), ('other', 'Other')], string='Cancel Type', translate=True)
    cancel_note = fields.Text('Cancel Note')

    @api.one
    @api.constrains('asset_no')
    def _check_asset_no_size(self):
        if len(self.asset_no) < 9:
            raise exceptions.ValidationError(_('Asset Number must have 9 chars!'))

    _sql_constraints = [
        ('asset_no_unique', 'unique(asset_no)',
         "Another asset already exists with this Asset No.!"),
    ]

    @api.onchange('category_id')
    def _onchange_category_id(self):
        self.ensure_one()
        value = dict()
        if self.category_id:
            domain = ['|', ('category_id', '=', self.category_id.id), ('category_id', '=', False)]
            value['domain'] = dict()
            value['domain']['attribute_ids'] = domain
        return value

    @api.model
    def create(self, vals):
        asset = super(Asset, self).create(vals)
        # subscribe employee or department manager when equipment assign to him.
        user_ids = []
        if asset.employee_id and asset.employee_id.user_id:
            user_ids.append(asset.employee_id.user_id.id)
        if asset.department_id and asset.department_id.manager_id and asset.department_id.manager_id.user_id:
            user_ids.append(asset.department_id.manager_id.user_id.id)
        if user_ids:
            asset.message_subscribe_users(user_ids=user_ids)
        return asset

    @api.multi
    def write(self, vals):
        user_ids = []
        # subscribe employee or department manager when equipment assign to employee or department.
        if vals.get('employee_id'):
            user_id = self.env['hr.employee'].browse(vals['employee_id'])['user_id']
            if user_id:
                user_ids.append(user_id.id)
        if vals.get('department_id'):
            department = self.env['hr.department'].browse(vals['department_id'])
            if department and department.manager_id and department.manager_id.user_id:
                user_ids.append(department.manager_id.user_id.id)
        if user_ids:
            self.message_subscribe_users(user_ids=user_ids)
        return super(Asset, self).write(vals)


class Employee(models.Model):
    _inherit = ['hr.employee']

    hs_ita_asset_ids = fields.One2many('hs_ita.asset', 'employee_id', string='IT Assets')


class Count(models.Model):
    _name = 'hs_ita.count'
    _description = 'Count'
    _order = 'plan_date desc'

    name = fields.Char('Subject', required=True)
    plan_date = fields.Date('Plan Date', required=True)
    item_ids = fields.One2many('hs_ita.count.item', 'count_id', string='Count Items')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('done', 'Done'), ('cancelled', 'Cancelled')],
                             string='State', default='draft', translate=True, required=True)
    note = fields.Text('Note')
    item_qty = fields.Integer(string="Item Qty", compute='_compute_item_qty')

    @api.multi
    def _compute_item_qty(self):
        item_data = self.env['hs_ita.count.item'].read_group([('count_id', 'in', self.ids)], ['count_id'], ['count_id'])
        mapped_data = dict([(m['count_id'][0], m['count_id_count']) for m in item_data])
        for count in self:
            count.item_qty = mapped_data.get(count.id, 0)


class CountItem(models.Model):
    _name = 'hs_ita.count.item'
    _description = 'Count Item'
    _rec_name = 'asset_id'
    _order = 'asset_id'

    count_id = fields.Many2one('hs_ita.count', string='Count', ondelete='cascade', auto_join=True)
    asset_id = fields.Many2one('hs_ita.asset', string='Asset', required=True)
    state = fields.Selection([('unknown', 'Unknown'), ('ok', 'OK'), ('missed', 'Missed'), ('damaged', 'Damaged')],
                             string='Result', default='unknown', translate=True, required=True)
    employee_id = fields.Many2one('hr.employee', string='Executor')
    count_date = fields.Date('Count Date')
    note = fields.Text('Note')

    _sql_constraints = [
        ('asset_unique', 'unique(count_id, asset_id)',
         "Another item already exists with this Asset No.!"),
    ]


class CountWizard(models.TransientModel):
    _name = 'hs_ita.count.wizard'
    _description = 'Count Wizard'

    name = fields.Char('Subject', required=True)
    asset_ids = fields.Many2many('hs_ita.asset', string='Assets')
    plan_date = fields.Date('Plan Date', required=True)
    note = fields.Text('Note')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'asset_ids': active_ids}
        return res

    @api.multi
    def create_count(self):
        self.ensure_one()
        count_dataset = self.env['hs_ita.count']
        count_item_dataset = self.env['hs_ita.count.item']
        new_count = count_dataset.create({'name': self.name, 'plan_date': self.plan_date, 'note': self.note})
        for this_asset_id in self.asset_ids:
            count_item_dataset.create({'count_id': new_count.id, 'asset_id': this_asset_id.id})
        return {'type': 'ir.actions.act_window', 'res_model': 'hs_ita.count',
                'res_id': new_count.id, 'view_type': 'form', 'view_mode': 'form'}

