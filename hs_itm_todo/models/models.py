# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools, exceptions, _


class Category(models.Model):
    _name = 'hs_itm.todo.category'
    _description = 'Category'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    task_ids = fields.One2many('hs_itm.todo.task', 'category_id', string='Tasks')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another category already exists with this name!"),
    ]


class Task(models.Model):
    _name = 'hs_itm.todo.task'
    _inherit = ['mail.thread']
    _description = 'Task'
    _order = 'priority, plan_finish_date'
    _parent_store = True

    @api.multi
    def _compute_note_qty(self):
        note_data = self.env['hs_itm.todo.note'].read_group([('task_id', 'in', self.ids)], ['task_id'], ['task_id'])
        mapped_data = dict([(m['task_id'][0], m['task_id_count']) for m in note_data])
        for task in self:
            task.note_qty = mapped_data.get(task.id, 0)

    @api.multi
    def _compute_hour_sum(self):
        hour_data = self.env['hs_itm.todo.hour'].read_group([('task_id', 'in', self.ids)], ['task_id'], ['task_id'])
        mapped_data = dict([(m['task_id'][0], m['task_id_count']) for m in hour_data])
        for task in self:
            task.hour_sum = mapped_data.get(task.id, 0)

    name = fields.Char('Title', required=True, track_visibility='onchange')
    category_id = fields.Many2one('hs_itm.todo.category', string='Category', required=True, ondelete='restrict',
                                  track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='PIC', required=True, default=lambda self: self.env.uid,
                              ondelete='restrict', track_visibility='onchange')
    plan_start_date = fields.Date('Plan Start Date', track_visibility='onchange')
    plan_finish_date = fields.Date('Plan Finish Date', track_visibility='onchange')
    parent_id = fields.Many2one('hs_itm.todo.task', string='Parent Task', ondelete='restrict',
                                track_visibility='onchange')
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    child_ids = fields.One2many('hs_itm.todo.task', 'parent_id', string='Sub Tasks')
    note_ids = fields.One2many('hs_itm.todo.note', 'task_id', string='Notes')
    note_qty = fields.Integer(string="Note Qty", compute='_compute_note_qty')
    hour_ids = fields.One2many('hs_itm.todo.hour', 'task_id', string='Hours', track_visibility='onchange')
    hour_sum = fields.Float(string="Total Hours", compute='_compute_hour_sum')
    description = fields.Html('Description', track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('ongoing', 'Ongoing'), ('pending', 'Pending'), ('cancelled', 'Cancelled'),
         ('finished', 'Finished')], string='Status', required=True, readonly=True, default='draft',
        track_visibility='onchange')
    priority = fields.Integer(string="Priority", default=10, track_visibility='onchange')
    private = fields.Boolean('Private?', default=False, track_visibility='onchange')
    active = fields.Boolean('Active?', default=True, track_visibility='onchange')

    _sql_constraints = [('plan_date_greater','check(plan_finish_date >= plan_start_date)',
                         'Error ! Plan Finish Date cannot be set before Plan Start Date.')]


class Note(models.Model):
    _name = 'hs_itm.todo.note'
    _inherit = ['mail.thread']
    _description = 'Note'
    _order = 'workday desc'

    name = fields.Char('Title', required=True, track_visibility='onchange')
    task_id = fields.Many2one('hs_itm.todo.task', string='Task', required=True, ondelete='restrict',
                              track_visibility='onchange')
    workday = fields.Date('Workday', required=True, default=fields.Datetime.now)
    type = fields.Selection(
        [('issue', 'Issue'), ('plan', 'Plan'), ('update', 'Update'), ('comment', 'Comment'), ('memo', 'Memo')],
        string='Type', default='update', required=True, translate=True, track_visibility='onchange')
    description = fields.Html('Description', track_visibility='onchange')
    private = fields.Boolean('Private?', default=False, track_visibility='onchange')
    active = fields.Boolean('Active?', default=True, track_visibility='onchange')


class Hour(models.Model):
    _name = 'hs_itm.todo.hour'
    _description = 'Hour'
    _order = 'workday desc'
    _rec_name = 'workday'
    _inherit = ['mail.thread']

    task_id = fields.Many2one('hs_itm.todo.task', string='Task', required=True, ondelete='restrict')
    workday = fields.Date('Workday', required=True, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='PIC', required=True, default=lambda self: self.env.uid,
                              ondelete='restrict', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
                                  ondelete='restrict', required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True,
                              track_visibility='onchange')
    qty = fields.Float('Qty', digits=(3,2), required=True)
    description = fields.Text('Description')

    _sql_constraints = [('task_workday_user_unique', 'UNIQUE (task_id, workday, user_id)',
                         'A user can only have one hour record for a task at the same workday.'),
                        ('qty_constraint', 'CHECK (qty > 0 AND qty <= 24)',
                         'A quantity must be positive and cannot be great than 24!')]

