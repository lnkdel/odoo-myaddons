# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp import http
import json
from collections import deque
from openerp.http import request, serialize_exception as _serialize_exception
import werkzeug.urls
import datetime,time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProductModel(models.Model):
    _name = 'hs_pts.cmsp.productmodel'
    _description = 'Product Model'
    _order = 'sequence, name, product_no'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    name = fields.Char('Name', required=True, track_visibility='onchange')  # 型号名称
    materiel_name = fields.Char('Materiel Name', required=True, track_visibility='onchange')  # 物料名称
    product_no = fields.Char('Product No.', required=True, track_visibility='onchange')  # 物料编码
    packing = fields.Selection(
        [('standard', 'Standard'), ('simpleness', 'Simpleness'), ('neutral', 'Neutral')],
        string='Packing', translate=True)
    iscutting = fields.Boolean('Cutting?', track_visibility='onchange')  # nullable
    width = fields.Float('Width', track_visibility='onchange')  # nullable
    unit = fields.Char('Unit', required=True)
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    remark = fields.Text('Remark')

    _sql_constraints = [
        ('productno_unique', 'unique(product_no)',
         "Another product model already exists with this Product No.!"),
    ]

    @api.one
    @api.depends('name', 'product_no', 'materiel_name')
    def _compute_display_name(self):
        names = [self.name, self.product_no, self.materiel_name]
        self.display_name = ' / '.join(names)


class Plan(models.Model): # 生产计划
    _name = 'hs_pts.cmsp.plan'
    _description = 'Product Plan'
    _order = 'write_date DESC, id ASC'
    _inherit = ['mail.thread']
    _rec_name = 'display_name'

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    @api.model
    def compute_default_no(self):
        # maxid = self.env['hs_pts.cmsp.plan'].search([('active', '=', True)], order="id desc", limit=1).id
        maxid = self.env['hs_pts.cmsp.plan'].sudo().search([(1, '=', 1)], order="id desc", limit=1).id
        nid = int(maxid)+1
        return nid

    def plan_reset(self):
        self.write({'state': 'draft'})
        return True

    def plan_process_selection(self):
        self.write({'state': 'ps'})

    def plan_doc_prepare(self):
        if self.processprogram is False or self.processprogram is None:
            raise exceptions.UserError(_("Please select the process program."))
            return False
        self.write({'state': 'dp'})
        return True

    def plan_task_confirm(self):
        self.write({'state': 'tc'})
        return True

    def task_in_progressing(self):
        if not self.task_ids or len(self.task_ids) == 0:
            raise exceptions.UserError(_("Please set the production task."))
            return False
        self.write({'state': 'tip'})
        return True

    def task_finished(self):
        self.write({'state': 'tf'})
        return True

    def cancel(self):
        self.write({'state': 'cancel'})
        return True

    # plan_no = fields.Char('Plan No.', required=True, default=compute_default_no, readonly=True, store=True)
    notice_no = fields.Char('Notice No.', required=True)
    planner = fields.Many2one('hr.employee', string='Planner', default=_default_employee_get, ondelete='restrict', required=True)
    product_type = fields.Selection(
        [('prepreg', 'Prepreg'), ('fabric', 'Fabric'), ('resin', 'Resin'), ('sizing', 'Sizing')],
        string='Product Type', translate=True, required=True)
    production_type = fields.Selection(
        [('military', 'Military'), ('civilian', 'Civilian'), ('project', 'Project'), ('test', 'Test'), ('stock', 'Stock')],
        string='Production Type', translate=True, required=True)
    model_id = fields.Many2one('hs_pts.cmsp.productmodel', string='Model', track_visibility='onchange', required=True)
    task_ids = fields.One2many('hs_pts.cmsp.task', 'plan_id', string='Tasks')

    state = fields.Selection(
        [('draft', 'Draft'), ('ps', 'Process Selection'), ('dp', 'Doc Preparation'), ('tc', 'Task Confirmation'),
         ('tip', 'Task in Progressing'), ('tf', 'Task Finished'), ('cancel', 'Cancelled')],
        string='State', default='draft', translate=True, copy=False, readonly=True, track_visibility='onchange')
    remark = fields.Text('Remark')
    processprogram = fields.Char('Process Program')
    amount = fields.Integer(string="Amount")
    complete_date = fields.Date('Complete Date')

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    _sql_constraints = [
        ('plan_unique', 'unique(notice_no, planner, product_type)',
         "Another plan already exists with this planno!"),
    ]

    @api.multi
    def unlink(self):
        if any(plan.state not in ['draft', 'cancel'] for plan in self):
            raise exceptions.UserError(_('You can only delete draft or cancelled plan!'))
        return super(Plan, self).unlink()

    @api.multi
    def write(self, vals):
        uid = self._uid

        checkmanager = False
        checkplanner = False
        checkprocessprogram_prepreg = False
        checkprocessprogram_fabric = False
        checkprocessprogram_resinsizing = False
        checkdirectorprepreg = False
        checkdirectorfabric = False
        checkdirectorresin = False
        checkdirectorsizing = False
        query = u"""
                  SELECT
                      res_groups.name
                    FROM
                      public.res_groups,
                      public.res_groups_users_rel,
                      public.res_users
                    WHERE
                      res_groups.id = res_groups_users_rel.gid AND
                      res_groups_users_rel.uid = res_users.id
                      and res_users.id=%d
                        """ % (uid)
        self._cr.execute(query)

        for row in self._cr.fetchall():
            groupname = row[0]
            if groupname == 'PTS CMSP Process Confirm Prepreg':
                checkprocessprogram_prepreg = True
            if groupname == 'PTS CMSP Process Confirm Fabric':
                checkprocessprogram_fabric = True
            if groupname == 'PTS CMSP Process Confirm ResinSizing':
                checkprocessprogram_resinsizing = True
            if groupname == 'PTS CMSP Planner':
                checkplanner = True
            if groupname == 'PTS CMSP Manager':
                checkmanager = True
            if groupname == 'PTS CMSP Production director for prepreg':
                checkdirectorprepreg = True
            if groupname == 'PTS CMSP Production director for fabric':
                checkdirectorfabric = True
            if groupname == 'PTS CMSP Production director for resin':
                checkdirectorresin = True
            if groupname == 'PTS CMSP Production director for sizing':
                checkdirectorsizing = True

        if checkmanager is False:
            if self.state == 'draft':
                if self.planner.user_id.id != uid or checkplanner is False:
                    raise exceptions.UserError(_("You can not change the record."))

            if vals.get('processprogram'):
                if self.product_type == 'prepreg':
                    if checkprocessprogram_prepreg is False:
                        vals['processprogram'] = None
                        raise exceptions.UserError(_("You can not change the record."))
                elif self.product_type == 'fabric':
                    if checkprocessprogram_fabric is False:
                        vals['processprogram'] = None
                        raise exceptions.UserError(_("You can not change the record."))
                elif self.product_type == 'fabric' or self.product_type == 'sizing':
                    if checkprocessprogram_resinsizing is False:
                        vals['processprogram'] = None
                        raise exceptions.UserError(_("You can not change the record."))

            if self.state == 'tc':
                if self.product_type == 'prepreg':
                    if checkdirectorprepreg is False:
                        raise exceptions.UserError(_("You can not change the record."))
                if self.product_type == 'fabric':
                    if checkdirectorfabric is False:
                        raise exceptions.UserError(_("You can not change the record."))
                if self.product_type == 'resin':
                    if checkdirectorresin is False:
                        raise exceptions.UserError(_("You can not change the record."))
                if self.product_type == 'sizing':
                    if checkdirectorsizing is False:
                        raise exceptions.UserError(_("You can not change the record."))

        return super(Plan, self).write(vals)

    @api.one
    @api.depends('product_type', 'production_type')
    def _compute_display_name(self):
        pt = ''
        if self.product_type:
            if self.product_type == 'prepreg':
                pt = u'预浸料'
            elif self.product_type == 'fabric':
                pt = u'织物'
            elif self.product_type == 'resin':
                pt = u'树脂'
            elif self.product_type == 'sizing':
                pt = u'上浆剂'
        self.display_name = '%d / %s / %s' % (self.id, pt, self.model_id.name)

    @api.onchange('product_type')
    def getmodelbyproduct_type(self):
        self.ensure_one()
        value = dict()
        if self.product_type:
            pt = u'预浸料'
            if self.product_type == 'prepreg':
                pt = u'预浸料'
            elif self.product_type == 'fabric':
                pt = u'织物'
            elif self.product_type == 'resin':
                pt = u'树脂'
            elif self.product_type == 'sizing':
                pt = u'上浆剂'
            domain = [('materiel_name', 'like', pt)]
            if self.product_type == 'fabric':
                domain = [('materiel_name', 'like', pt), ('materiel_name', 'not like', u'预浸料')]
            value['domain'] = dict()
            value['domain']['model_id'] = domain
        return value

    def onchange_product_type(self):
        self.getmodelbyproduct_type(self)


class Task(models.Model): # 车间任务
    _name = 'hs_pts.cmsp.task'
    _description = 'Product Task'
    _order = 'priority, start_date, plan_id'
    _inherit = ['mail.thread']
    _rec_name = 'display_name'

    def _default_workshift_get(self):
        workshift = ''
        now = datetime.datetime.now()
        hour = now.hour + 8
        if hour >= 8 and hour < 16:
            workshift = 'morning'
        elif hour >= 16 and hour < 24:
            workshift = 'middle'
        else:
            workshift = 'night'
        return workshift

    plan_id = fields.Many2one('hs_pts.cmsp.plan', string='Plan', ondelete='cascade', auto_join=True, required=True)
    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', track_visibility='onchange', required=True)   # 机台
    start_date = fields.Date('Start', required=True, default=fields.Datetime.now)
    lot = fields.Char('Lot No.', required=True, default='HF', track_visibility='onchange')
    priority = fields.Integer(string="Priority", default=10, track_visibility='onchange')
    remark = fields.Text('Remark')
    workshift = fields.Selection(
        [('morning', 'Morning Shift'), ('middle', 'Middle Shift'), ('night', 'Night Shift')],
        string='Work Shift', default=_default_workshift_get, translate=True, required=True)
    display_workshift = fields.Char(string='Work Shift', compute='_compute_display_workshift', translate=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    @api.one
    @api.depends('workshift')
    def _compute_display_workshift(self):
        wsdc = [('morning', u'早班'), ('middle', u'中班'), ('night', u'晚班')]
        for item in wsdc:
            if item[0] == self.workshift:
                self.display_workshift = item[1]

    @api.one
    def _compute_display_name(self):
        self.display_name = u'任务号：[%d] / 所属计划:[%s] / %s' % (self.id, self.plan_id.display_name, self.plan_id.model_id.display_name)

    @api.onchange('plan_id')
    def generateplanlot(self):
        self.ensure_one()
        pt = ""
        if self.plan_id.product_type == 'prepreg':
            pt = 'P'
        elif self.plan_id.product_type == 'fabric':
            pt = 'F'
        elif self.plan_id.product_type == 'resin':
            pt = 'R'
        elif self.plan_id.product_type == 'sizing':
            pt = 'S'
        wu = ''
        if self.workunit_id.name:
            wu = self.workunit_id.name

        p = self.env['hs_pts.cmsp.plan'].sudo().search([('notice_no', '=', self.plan_id.notice_no),
                                                   ('product_type', '=', self.plan_id.product_type),
                                                   ('state', '=', self.plan_id.state)])
        if p.id:
            self.plan_id = p.id
            self.lot = 'HF%s%s%s%s' % (pt, wu, self.start_date.replace('-', ''), str(p.id))
        else:
            self.lot = 'HF%s%s%s' % (pt, wu, self.start_date.replace('-', ''))

        self.workunit_id = None
        value = dict()
        if self.plan_id:
            pt = u'预浸车间'
            if self.plan_id.product_type == 'prepreg':
                pt = u'预浸车间'
            elif self.plan_id.product_type == 'fabric':
                pt = u'织物车间'
            elif self.plan_id.product_type == 'resin':
                pt = u'树脂车间'
            elif self.plan_id.product_type == 'sizing':
                pt = u'上浆剂车间'
            domain = [('workfloor_id.name', '=', pt)]
            value['domain'] = dict()
            value['domain']['workunit_id'] = domain
        return value

    @api.onchange('start_date', 'workunit_id')
    def generatelot(self):
        pt = ""
        if self.plan_id.product_type == 'prepreg':
            pt = 'P'
        elif self.plan_id.product_type == 'fabric':
            pt = 'F'
        elif self.plan_id.product_type == 'resin':
            pt = 'R'
        elif self.plan_id.product_type == 'sizing':
            pt = 'S'
        wu = ''
        if self.workunit_id.name:
            wu = self.workunit_id.name
        p = self.env['hs_pts.cmsp.plan'].sudo().search([('notice_no', '=', self.plan_id.notice_no),
                                                   ('product_type', '=', self.plan_id.product_type),
                                                   ('state', '=', self.plan_id.state)])
        if p.id:
            self.lot = 'HF%s%s%s%s' % (pt, wu, self.start_date.replace('-', ''), str(p.id))
        else:
            self.lot = 'HF%s%s%s' % (pt, wu, self.start_date.replace('-', ''))

    def onchange_plan(self):
        self.generateplanlot(self)

    def onchange_startdate(self):
        self.generatelot(self)

    def onchange_workunit(self):
        self.generatelot(self)


class WorkUnit(models.Model):  # 机台
    _name = 'hs_pts.cmsp.workunit'
    _description = 'Work Unit'
    _order = 'sequence, name'
    _inherit = ['mail.thread']
    _rec_name = 'display_name'

    name = fields.Char('Name', required=True, track_visibility='onchange')
    full_name = fields.Char('Full Name', track_visibility='onchange')
    workfloor_id = fields.Many2one('hs_pts.cmsp.workfloor', string='Workfloor', required=True, track_visibility='onchange')
    remark = fields.Text('Remark')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    _sql_constraints = [
        ('name_unique', 'unique(name, workfloor_id)',
         "Another workunit already exists with this name!"),
    ]

    @api.one
    @api.depends('workfloor_id', 'full_name')
    def _compute_display_name(self):
        fn = ''
        if self.full_name:
            fn = self.full_name
        else:
            fn = self.name
        names = [self.workfloor_id.name, self.full_name]
        self.display_name = '%s%s' % (names[0], names[1])


class WorkFloor(models.Model):  # 车间
    _name = 'hs_pts.cmsp.workfloor'
    _description = 'Work Floor'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char('Name', required=True, track_visibility='onchange')
    manager = fields.Many2one('hr.employee', string='Manager', ondelete='restrict')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    remark = fields.Text('Remark')

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another workfloor already exists with this name!"),
    ]


class WorkGroup(models.Model):  # 班组
    _name = 'hs_pts.cmsp.workgroup'
    _description = 'Work Group'
    _order = 'workfloor_id, sequence'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    name = fields.Char('Name', required=True, track_visibility='onchange')
    workfloor_id = fields.Many2one('hs_pts.cmsp.workfloor', string='Workfloor', track_visibility='onchange')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    groupitem_ids = fields.One2many('hs_pts.cmsp.workgroupitem', 'workgroup_id', string='Items')
    remark = fields.Text('Remark')

    _sql_constraints = [
        ('name_unique', 'unique(name, workfloor_id)',
         "Another work group already exists with this name!"),
    ]

    @api.one
    @api.depends('workfloor_id', 'name')
    def _compute_display_name(self):
        names = [self.workfloor_id.name, self.name]
        self.display_name = ' / '.join(names)


class WorkGroupItem(models.Model):
    _name = 'hs_pts.cmsp.workgroupitem'
    _description = 'Work Group Item'
    _order = 'workgroup_id'
    _inherit = ['mail.thread']

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    workgroup_id = fields.Many2one('hs_pts.cmsp.workgroup', string='Work Group', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_get, ondelete='restrict', required=True)

    _sql_constraints = [
        ('groupitem_unique', 'unique(workgroup_id, employee_id)',
         "The work group item already exists with this employee!"),
    ]

    @api.onchange('workgroup_id')
    def generateworkgroup(self):
        self.ensure_one()
        wg = self.env['hs_pts.cmsp.workgroup'].sudo().search([('name', '=', self.workgroup_id.name),
                                                   ('workfloor_id', '=', self.workgroup_id.workfloor_id.id)])
        if wg and wg.id:
            self.workgroup_id = wg

    def onchange_workgroup(self):
        self.generateworkgroup(self)


class QualityLevel(models.Model):  # 品级
    _name = 'hs_pts.cmsp.qualitylevel'
    _description = 'Quality Level'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char('Name', required=True, track_visibility='onchange')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Another quality level already exists with this name!"),
    ]


class PrepregStorage(models.TransientModel):
    _name = 'hs_pts.cmsp.prepreg.storage.wizard'

    operate = fields.Selection(
        [('yes', 'Storage'), ('no', 'Cancel')],
        string='操作类型', default='yes', translate=True, required=True)
    prepreg_ids = fields.Many2many('hs_pts.cmsp.prepregroll', string='PrepregRoll', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'prepreg_ids': active_ids}
        return res

    @api.multi
    def confirm_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.prepregroll'].sudo().search([('id', 'in', active_ids)])
        if self.operate == 'yes':
            rolls.write({'stock_time': datetime.datetime.now()})
        else:
            rolls.write({'stock_time': None})
        return {'type': 'ir.actions.act_window_close'}


class PrepregBatchSetQuality(models.TransientModel):
    _name = 'hs_pts.cmsp.prepreg.sq.wizard'

    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    prepreg_ids = fields.Many2many('hs_pts.cmsp.prepregroll', string='PrepregRoll', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'prepreg_ids': active_ids}
        return res

    @api.multi
    def set_quality_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.prepregroll'].sudo().search([('id', 'in', active_ids)])
        rolls.write({'qualitylevel': self.qualitylevel.id})
        return {'type': 'ir.actions.act_window_close'}


class PrepregXLS(models.TransientModel):
    _name = 'hs_pts.cmsp.prepreg.wizard'

    prepreg_ids = fields.Many2many('hs_pts.cmsp.prepregroll', string='PrepregRoll', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'prepreg_ids': active_ids}
        return res

    @api.multi
    def export_xls_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        print '\033[1;31;40m'
        print '--------------------开始导出--------------------'
        print active_ids
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if emp.display_name is not False:
            operator = emp.display_name.replace(' / ', ' ')
        else:
            operator = 'noemployee'
        print operator
        print '\033[0;m'

        pids = ','.join(str(i) for i in active_ids)
        now = datetime.datetime.now()
        otherStyleTime = now.strftime("%Y%m%d%H%M%S")

        filename = 'prpregroll-%s' % (otherStyleTime)
        return {
            'type': 'ir.actions.act_url',
            'url': '/hs_pts_cmsp/exporter/download_xls_prepreg?model=hs_pts.cmsp.prepregroll&ids=%s&operator=%s&filename=%s' % (pids, operator, filename),
            'target': 'self',
        }


class PrepregRoll(models.Model):
    _name = 'hs_pts.cmsp.prepregroll'
    _description = 'Prepreg Roll'
    _order = 'sequence, create_date DESC'
    _rec_name = 'barcode_no'
    _inherit = ['mail.thread']

    @api.model
    def compute_default_value(self):
        maxid = self.env['hs_pts.cmsp.prepregroll'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        return maxid+1

    def compute_default_workgroupid(self):
        usergroups = self.env['hs_pts.cmsp.workgroupitem'].sudo().search([('employee_id.user_id', '=', self.env.uid)])
        for g in usergroups:
            if g.workgroup_id.workfloor_id.name == u'预浸车间':
                return g.workgroup_id

    @api.multi
    @api.depends('roll_length', 'model_id.width')
    def _compute_area(self):
        self.area = self.roll_length * self.model_id.width

    @api.multi
    @api.depends('plan_id')
    def _compute_model(self):
        self.model_id = self.plan_id.model_id

    @api.multi
    @api.depends('task_id')
    def _compute_workunit(self):
        self.workunit_id = self.task_id.workunit_id

    barcode_no = fields.Char('Roll No.', readonly=True)  # roll_barcode
    plan_id = fields.Many2one('hs_pts.cmsp.plan', required=True, string='Plan', track_visibility='onchange')
    task_id = fields.Many2one('hs_pts.cmsp.task', required=True, string='Task', track_visibility='onchange')
    roll_length = fields.Float('Length', required=True, track_visibility='onchange')
    gross_weight = fields.Float('Gross Weight (Kg)', required=True, track_visibility='onchange')
    net_weight = fields.Float('Net Weight (Kg)', required=True, track_visibility='onchange')
    lot_no = fields.Char('Lot No.', default='HFP', required=True, track_visibility='onchange')
    model_id = fields.Many2one('hs_pts.cmsp.productmodel', string='Product Model', readonly=True, compute='_compute_model', store=True)
    workgroup_id = fields.Many2one('hs_pts.cmsp.workgroup', string='Work Group', default=compute_default_workgroupid, track_visibility='onchange', required=True)

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    product_date = fields.Datetime('Production Date', default=fields.Datetime.now)
    area = fields.Float('Area', compute='_compute_area', readonly=True, store=True)
    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    remark = fields.Text('Remark')
    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', readonly=True, compute='_compute_workunit', store=True)
    stock_time = fields.Datetime('Stock Time')

    _sql_constraints = [
        ('prepregrollno_unique', 'unique(barcode_no)',
         "Another prepreg roll already exists with this barcode_no!"),
    ]

    @api.model
    def create(self, vals):
        # number = self.env['hs_pts.cmsp.prepregroll'].search([('active', '=', True)], order="id desc", limit=1).id + 1
        maxid = self.env['hs_pts.cmsp.prepregroll'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        nextid = maxid+1
        rollnumber = 'P' + str(nextid).zfill(7)
        # vals['number'] = number
        vals['barcode_no'] = rollnumber
        prepreg = super(PrepregRoll, self).create(vals)
        return prepreg

    @api.multi
    def unlink(self):
        if any(prepreg.stock_time is not None for prepreg in self):
            raise exceptions.UserError(_('You can not delete the product already in storage!'))
        return super(PrepregRoll, self).unlink()

    @api.onchange('plan_id')
    def getproductinfobyplan(self):
        value = dict()
        if self.plan_id and self.plan_id is not None:
            if self.plan_id.product_type == 'prepreg':
                domain = [('plan_id', '=', self.plan_id.id)]
                value['domain'] = dict()
                value['domain']['task_id'] = domain
                self.task_id = self.env['hs_pts.cmsp.task'].sudo().search([('plan_id', '=', self.plan_id.id)])[0]
                return value
            else:
                raise exceptions.UserError(_("Please select the plan for prepreg."))

    def onchange_plan(self):
        self.getproductinfobyplan(self)

    @api.onchange('task_id')
    def getproductinfobytask(self):
        if self.task_id and self.task_id is not None:
            if self.plan_id.id is False:
                self.plan_id = self.task_id.plan_id.id
            if self.plan_id.product_type == 'prepreg':
                self.lot_no = self.task_id.lot
                self.model_id = self.plan_id.model_id
                self.workunit_id = self.task_id.workunit_id

    @api.multi
    def label_print(self):
        self.ensure_one()
        return self.env['report'].get_action(self, 'cmsp_prepregroll')


class FabricStorage(models.TransientModel):
    _name = 'hs_pts.cmsp.fabric.storage.wizard'

    operate = fields.Selection(
        [('yes', 'Storage'), ('no', 'Cancel')],
        string='操作类型', default='yes', translate=True, required=True)
    fabric_ids = fields.Many2many('hs_pts.cmsp.fabricroll', string='FabricRoll', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'fabric_ids': active_ids}
        return res

    @api.multi
    def confirm_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.fabricroll'].sudo().search([('id', 'in', active_ids)])
        if self.operate == 'yes':
            rolls.write({'stock_time': datetime.datetime.now()})
        else:
            rolls.write({'stock_time': None})
        return {'type': 'ir.actions.act_window_close'}


class FabricBatchSetQuality(models.TransientModel):
    _name = 'hs_pts.cmsp.fabric.sq.wizard'

    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    fabric_ids = fields.Many2many('hs_pts.cmsp.fabricroll', string='FabricRoll', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'fabric_ids': active_ids}
        return res

    @api.multi
    def set_quality_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.fabricroll'].search([('id', 'in', active_ids)])
        rolls.write({'qualitylevel': self.qualitylevel.id})
        return {'type': 'ir.actions.act_window_close'}


class FabricXLS(models.TransientModel):
    _name = 'hs_pts.cmsp.fabric.wizard'

    fabric_ids = fields.Many2many('hs_pts.cmsp.fabricroll', string='FabricRoll', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'fabric_ids': active_ids}
        return res

    @api.multi
    def export_xls_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')

        pids = ','.join(str(i) for i in active_ids)
        now = datetime.datetime.now()
        otherStyleTime = now.strftime("%Y%m%d%H%M%S")

        filename = 'fabricroll-%s' % (otherStyleTime)
        return {
            'type': 'ir.actions.act_url',
            'url': '/hs_pts_cmsp/exporter/download_xls_fabric?model=hs_pts.cmsp.prepregroll&ids=%s&filename=%s' % (pids, filename),
            'target': 'self',
        }


class FabricRoll(models.Model):
    _name = 'hs_pts.cmsp.fabricroll'
    _description = 'Fabric Roll'
    _order = 'sequence, create_date DESC'
    _rec_name = 'barcode_no'
    _inherit = ['mail.thread']

    @api.model
    def compute_default_value(self):
        maxid = self.env['hs_pts.cmsp.fabricroll'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        return maxid+1

    def compute_default_workgroupid(self):
        usergroups = self.env['hs_pts.cmsp.workgroupitem'].sudo().search([('employee_id.user_id', '=', self.env.uid)])
        for g in usergroups:
            if g.workgroup_id.workfloor_id.name == u'织物车间':
                return g.workgroup_id
    @api.multi
    @api.depends('roll_length', 'model_id.width')
    def _compute_area(self):
        self.area = self.roll_length * self.model_id.width

    @api.multi
    @api.depends('plan_id')
    def _compute_model(self):
        self.model_id = self.plan_id.model_id

    @api.multi
    @api.depends('task_id')
    def _compute_workunit(self):
        self.workunit_id = self.task_id.workunit_id

    barcode_no = fields.Char('Roll No.', readonly=True)
    plan_id = fields.Many2one('hs_pts.cmsp.plan', required=True, string='Plan', track_visibility='onchange')
    task_id = fields.Many2one('hs_pts.cmsp.task', required=True, string='Task', track_visibility='onchange')
    roll_length = fields.Float('Length', required=True, track_visibility='onchange')
    gross_weight = fields.Float('Gross Weight (Kg)', required=True, track_visibility='onchange')
    net_weight = fields.Float('Net Weight (Kg)', required=True, track_visibility='onchange')
    lot_no = fields.Char('Lot No.', default='HFP', required=True, track_visibility='onchange')
    model_id = fields.Many2one('hs_pts.cmsp.productmodel', string='Product Model', readonly=True, compute='_compute_model', store=True)
    workgroup_id = fields.Many2one('hs_pts.cmsp.workgroup', string='Work Group', default=compute_default_workgroupid, track_visibility='onchange', required=True)

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    product_date = fields.Datetime('Production Date', default=fields.Datetime.now)
    area = fields.Float('Area', compute='_compute_area', readonly=True, store=True)
    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    remark = fields.Text('Remark')
    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', readonly=True, compute='_compute_workunit', store=True)
    stock_time = fields.Datetime('Stock Time')

    _sql_constraints = [
        ('fabricrollno_unique', 'unique(barcode_no)',
         "Another fabric roll already exists with this barcode_no!"),
    ]

    @api.model
    def create(self, vals):
        # number = self.env['hs_pts.cmsp.fabricroll'].search([('active', '=', True)], order="id desc", limit=1).id + 1
        maxid = self.env['hs_pts.cmsp.fabricroll'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        nextid = maxid + 1
        rollnumber = 'F' + str(nextid).zfill(7)
        # vals['number'] = number
        vals['barcode_no'] = rollnumber
        fabric = super(FabricRoll, self).create(vals)
        return fabric

    @api.multi
    def unlink(self):
        if any(fabric.stock_time is not None for fabric in self):
            raise exceptions.UserError(_('You can not delete the product already in storage!'))
        return super(FabricRoll, self).unlink()

    @api.onchange('plan_id')
    def getproductinfobyplan(self):
        value = dict()
        if self.plan_id and self.plan_id is not None:
            if self.plan_id.product_type == 'fabric':
                domain = [('plan_id', '=', self.plan_id.id)]
                value['domain'] = dict()
                value['domain']['task_id'] = domain
                self.task_id = self.env['hs_pts.cmsp.task'].sudo().search([('plan_id', '=', self.plan_id.id)])[0]
                return value
            else:
                raise exceptions.UserError(_("Please select the plan for fabric."))

    def onchange_plan(self):
        self.getproductinfobyplan(self)

    @api.onchange('task_id')
    def getproductinfobytask(self):
        if self.task_id and self.task_id is not None:
            if self.plan_id.id is False:
                self.plan_id = self.task_id.plan_id.id
            if self.plan_id.product_type == 'fabric':
                self.lot_no = self.task_id.lot
                self.model_id = self.plan_id.model_id
                self.workunit_id = self.task_id.workunit_id


class ResinStorage(models.TransientModel):
    _name = 'hs_pts.cmsp.resin.storage.wizard'

    operate = fields.Selection(
        [('yes', 'Storage'), ('no', 'Cancel')],
        string='操作类型', default='yes', translate=True, required=True)
    resin_ids = fields.Many2many('hs_pts.cmsp.resinlot', string='ResinLot', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'resin_ids': active_ids}
        return res

    @api.multi
    def confirm_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.resinlot'].sudo().search([('id', 'in', active_ids)])
        if self.operate == 'yes':
            rolls.write({'stock_time': datetime.datetime.now()})
        else:
            rolls.write({'stock_time': None})
        return {'type': 'ir.actions.act_window_close'}


class ResinBatchSetQuality(models.TransientModel):
    _name = 'hs_pts.cmsp.resin.sq.wizard'

    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    resin_ids = fields.Many2many('hs_pts.cmsp.resinlot', string='ResinLot', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'resin_ids': active_ids}
        return res

    @api.multi
    def set_quality_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.resinlot'].sudo().search([('id', 'in', active_ids)])
        rolls.write({'qualitylevel': self.qualitylevel.id})
        return {'type': 'ir.actions.act_window_close'}


class ResinXLS(models.TransientModel):
    _name = 'hs_pts.cmsp.resin.wizard'

    resin_ids = fields.Many2many('hs_pts.cmsp.resinlot', string='ResinLot', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'resin_ids': active_ids}
        return res

    @api.multi
    def export_xls_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')

        pids = ','.join(str(i) for i in active_ids)
        now = datetime.datetime.now()
        otherStyleTime = now.strftime("%Y%m%d%H%M%S")

        filename = 'resinlot-%s' % (otherStyleTime)
        return {
            'type': 'ir.actions.act_url',
            'url': '/hs_pts_cmsp/exporter/download_xls_resin?model=hs_pts.cmsp.resinlot&ids=%s&filename=%s' % (pids, filename),
            'target': 'self',
        }


class ResinLot(models.Model):
    _name = 'hs_pts.cmsp.resinlot'
    _description = 'Resin Lot'
    _order = 'sequence, create_date DESC'
    _rec_name = 'barcode_no'
    _inherit = ['mail.thread']

    @api.model
    def compute_default_value(self):
        maxid = self.env['hs_pts.cmsp.resinlot'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        return maxid+1

    def compute_default_workgroupid(self):
        usergroups = self.env['hs_pts.cmsp.workgroupitem'].sudo().search([('employee_id.user_id', '=', self.env.uid)])
        for g in usergroups:
            if g.workgroup_id.workfloor_id.name == u'树脂车间':
                return g.workgroup_id

    @api.multi
    @api.depends('plan_id')
    def _compute_model(self):
        self.model_id = self.plan_id.model_id

    @api.multi
    @api.depends('task_id')
    def _compute_workunit(self):
        self.workunit_id = self.task_id.workunit_id

    barcode_no = fields.Char('No.', readonly=True)
    plan_id = fields.Many2one('hs_pts.cmsp.plan', required=True, string='Plan', track_visibility='onchange')
    task_id = fields.Many2one('hs_pts.cmsp.task', required=True, string='Task', track_visibility='onchange')
    model_id = fields.Many2one('hs_pts.cmsp.productmodel', string='Product Model', readonly=True, compute='_compute_model', store=True)
    lot_no = fields.Char('Lot No.', default='HFP', required=True, track_visibility='onchange')
    content = fields.Float('Solid Content', requires=True, track_visibility='onchange')
    gross_weight = fields.Float('Gross Weight (Kg)', required=True, track_visibility='onchange')
    net_weight = fields.Float('Net Weight (Kg)', required=True, track_visibility='onchange')
    shelflife = fields.Float('Shelf Life (year)', required=True, default=1, track_visibility='onchange')
    workgroup_id = fields.Many2one('hs_pts.cmsp.workgroup', string='Work Group', default=compute_default_workgroupid, track_visibility='onchange', required=True)

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    product_date = fields.Datetime('Production Date', default=fields.Datetime.now)
    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    remark = fields.Text('Remark')
    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', readonly=True, compute='_compute_workunit', store=True)
    stock_time = fields.Datetime('Stock Time')

    _sql_constraints = [
        ('resinpailno_unique', 'unique(barcode_no)',
         "Another resin pail already exists with this barcode_no!"),
    ]

    @api.model
    def create(self, vals):
        #number = self.env['hs_pts.cmsp.resinlot'].search([('active', '=', True)], order="id desc", limit=1).id + 1
        maxid = self.env['hs_pts.cmsp.resinlot'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        nextid = maxid + 1
        rollnumber = 'R' + str(nextid).zfill(7)
        #vals['number'] = number
        vals['barcode_no'] = rollnumber
        resin = super(ResinLot, self).create(vals)
        return resin

    @api.multi
    def unlink(self):
        if any(resin.stock_time is not None for resin in self):
            raise exceptions.UserError(_('You can not delete the product already in storage!'))
        return super(ResinLot, self).unlink()

    @api.onchange('plan_id')
    def getproductinfobyplan(self):
        value = dict()
        if self.plan_id and self.plan_id is not None:
            if self.plan_id.product_type == 'resin':
                domain = [('plan_id', '=', self.plan_id.id)]
                value['domain'] = dict()
                value['domain']['task_id'] = domain
                self.task_id = self.env['hs_pts.cmsp.task'].sudo().search([('plan_id', '=', self.plan_id.id)])[0]
                return value
            else:
                raise exceptions.UserError(_("Please select the plan for resin."))


    def onchange_plan(self):
        self.getproductinfobyplan(self)

    @api.onchange('task_id')
    def getproductinfobytask(self):
        if self.task_id and self.task_id is not None:
            if self.plan_id.id is False:
                self.plan_id = self.task_id.plan_id.id
            if self.plan_id.product_type == 'resin':
                self.lot_no = self.task_id.lot
                self.model_id = self.plan_id.model_id
                self.workunit_id = self.task_id.workunit_id


class SizingStorage(models.TransientModel):
    _name = 'hs_pts.cmsp.sizing.storage.wizard'

    operate = fields.Selection(
        [('yes', 'Storage'), ('no', 'Cancel')],
        string='操作类型', default='yes', translate=True, required=True)
    sizing_ids = fields.Many2many('hs_pts.cmsp.sizinglot', string='SizingLot', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'sizing_ids': active_ids}
        return res

    @api.multi
    def confirm_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.sizinglot'].sudo().search([('id', 'in', active_ids)])
        if self.operate == 'yes':
            rolls.write({'stock_time': datetime.datetime.now()})
        else:
            rolls.write({'stock_time': None})
        return {'type': 'ir.actions.act_window_close'}


class SizingBatchSetQuality(models.TransientModel):
    _name = 'hs_pts.cmsp.sizing.sq.wizard'

    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    sizing_ids = fields.Many2many('hs_pts.cmsp.sizinglot', string='SizingLot', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'sizing_ids': active_ids}
        return res

    @api.multi
    def set_quality_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        rolls = self.env['hs_pts.cmsp.sizinglot'].search([('id', 'in', active_ids)])
        rolls.write({'qualitylevel': self.qualitylevel.id})
        return {'type': 'ir.actions.act_window_close'}


class SizingXLS(models.TransientModel):
    _name = 'hs_pts.cmsp.sizing.wizard'

    sizing_ids = fields.Many2many('hs_pts.cmsp.sizinglot', string='SizingLot', required=True)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'sizing_ids': active_ids}
        return res

    @api.multi
    def export_xls_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')

        pids = ','.join(str(i) for i in active_ids)
        now = datetime.datetime.now()
        otherStyleTime = now.strftime("%Y%m%d%H%M%S")

        filename = 'sizinglot-%s' % (otherStyleTime)
        return {
            'type': 'ir.actions.act_url',
            'url': '/hs_pts_cmsp/exporter/download_xls_sizing?model=hs_pts.cmsp.sizinglot&ids=%s&filename=%s' % (pids, filename),
            'target': 'self',
        }


class SizingLot(models.Model):
    _name = 'hs_pts.cmsp.sizinglot'
    _description = 'Sizing Lot'
    _order = 'sequence, create_date DESC'
    _rec_name = 'barcode_no'
    _inherit = ['mail.thread']
    @api.model
    def compute_default_value(self):
        maxid = self.env['hs_pts.cmsp.sizinglot'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        return maxid+1

    def compute_default_workgroupid(self):
        usergroups = self.env['hs_pts.cmsp.workgroupitem'].sudo().search([('employee_id.user_id', '=', self.env.uid)])
        for g in usergroups:
            if g.workgroup_id.workfloor_id.name == u'上浆剂车间':
                return g.workgroup_id

    @api.multi
    @api.depends('plan_id')
    def _compute_model(self):
        self.model_id = self.plan_id.model_id

    @api.multi
    @api.depends('task_id')
    def _compute_workunit(self):
        self.workunit_id = self.task_id.workunit_id

    barcode_no = fields.Char('No.', readonly=True)
    plan_id = fields.Many2one('hs_pts.cmsp.plan', required=True, string='Plan', track_visibility='onchange')
    task_id = fields.Many2one('hs_pts.cmsp.task', required=True, string='Task', track_visibility='onchange')
    model_id = fields.Many2one('hs_pts.cmsp.productmodel', string='Product Model', readonly=True, compute='_compute_model', store=True)
    lot_no = fields.Char('Lot No.', default='HFS', required=True, track_visibility='onchange')
    content = fields.Float('Solid Content', requires=True, track_visibility='onchange')
    gross_weight = fields.Float('Gross Weight (Kg)', required=True, track_visibility='onchange')
    net_weight = fields.Float('Net Weight (Kg)', required=True, track_visibility='onchange')
    shelflife = fields.Float('Shelf Life (year)', required=True,default=1, track_visibility='onchange')
    workgroup_id = fields.Many2one('hs_pts.cmsp.workgroup', string='Work Group', default=compute_default_workgroupid, track_visibility='onchange', required=True)

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean('Active?', default=True)
    product_date = fields.Datetime('Production Date', default=fields.Datetime.now)
    qualitylevel = fields.Many2one('hs_pts.cmsp.qualitylevel', string='Quality Level', track_visibility='onchange')
    remark = fields.Text('Remark')
    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', readonly=True, compute='_compute_workunit', store=True)
    stock_time = fields.Datetime('Stock Time')

    _sql_constraints = [
        ('sizingno_unique', 'unique(barcode_no)',
         "Another sizing lot already exists with this barcode_no!"),
    ]

    @api.model
    def create(self, vals):
        # number = self.env['hs_pts.cmsp.sizinglot'].search([('active', '=', True)], order="id desc", limit=1).id + 1
        maxid = self.env['hs_pts.cmsp.sizinglot'].sudo().search([('active', '=', True)], order="id desc", limit=1).id
        nextid = maxid + 1
        rollnumber = 'S' + str(nextid).zfill(7)
        # vals['number'] = number
        vals['barcode_no'] = rollnumber
        sizing = super(SizingLot, self).create(vals)
        return sizing

    @api.multi
    def unlink(self):
        if any(sizing.stock_time is not None for sizing in self):
            raise exceptions.UserError(_('You can not delete the product already in storage!'))
        return super(SizingLot, self).unlink()

    @api.onchange('plan_id')
    def getproductinfobyplan(self):
        value = dict()
        if self.plan_id and self.plan_id is not None:
            if self.plan_id.product_type == 'sizing':
                domain = [('plan_id', '=', self.plan_id.id)]
                value['domain'] = dict()
                value['domain']['task_id'] = domain
                self.task_id = self.env['hs_pts.cmsp.task'].sudo().search([('plan_id', '=', self.plan_id.id)])[0]
                return value
            else:
                raise exceptions.UserError(_("Please set the plan for sizing."))

    def onchange_plan(self):
        self.getproductinfobyplan(self)

    @api.onchange('task_id')
    def getproductinfobytask(self):
        if self.task_id and self.task_id is not None:
            if self.plan_id.id is False:
                self.plan_id = self.task_id.plan_id.id
            if self.plan_id.product_type == 'sizing':
                self.lot_no = self.task_id.lot
                self.model_id = self.plan_id.model_id
                self.workunit_id = self.task_id.workunit_id


class FabricShiftReport(models.Model):
    _name = 'hs_pts.cmsp.fabricshiftreport'
    _description = 'Fabric Shift Report'
    _order = 'workunit_id, workgroup_id, workshift'
    _rec_name = 'workunit_id'
    _inherit = ['mail.thread']

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    def _default_workshift_get(self):
        workshift = ''
        now = datetime.datetime.now()
        hour = now.hour + 8
        if hour >= 8 and hour < 16:
            workshift = 'morning'
        elif hour >= 16 and hour < 24:
            workshift = 'middle'
        else:
            workshift = 'night'
        return workshift

    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', track_visibility='onchange', required=True)
    work_date = fields.Date('Work Date', default=fields.Datetime.now, required=True)
    workgroup_id = fields.Many2one('hs_pts.cmsp.workgroup', string='Work Group', track_visibility='onchange')
    workshift = fields.Selection(
        [('morning', 'Morning Shift'), ('middle', 'Middle Shift'), ('night', 'Night Shift')],
        string='Work Shift', default=_default_workshift_get, translate=True, required=True)
    display_workshift = fields.Char(string='Work Shift', compute='_compute_display_workshift', translate=True)
    running_time = fields.Integer('Eq. Running (min)', track_visibility='onchange')
    display_runningtime = fields.Char(string='Eq. Running', compute='_compute_display_runningtime')
    model_id = fields.Many2one('hs_pts.cmsp.productmodel', string='Model', track_visibility='onchange', required=True)
    output_length = fields.Float('Output（m）', track_visibility='onchange')
    inspect_length = fields.Float('Inspect（m）', track_visibility='onchange')
    reject_length = fields.Float('Reject（m）', track_visibility='onchange')
    slitter_weight = fields.Float('Slitter edge yarn（kg)', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_get, ondelete='restrict', required=True)
    remark = fields.Text('Remark')
    rolling_number = fields.Char('Rolling Number', track_visibility='onchange')

    @api.one
    @api.depends('running_time')
    def _compute_display_runningtime(self):
        hours = self.running_time/60
        minutes = self.running_time - hours*60
        self.display_runningtime = '%dh%dmin' % (hours, minutes)

    @api.one
    @api.depends('workshift')
    def _compute_display_workshift(self):
        wsdc = [('morning', 'Morning Shift'), ('middle', 'Middle Shift'), ('night', 'Night Shift')]
        for item in wsdc:
            if item[0] == self.workshift:
                self.display_workshift = item[1]


class FabricShiftReportMain(models.Model):
    _name = 'hs_pts.cmsp.fabricshiftreport_main'
    _description = 'Fabric Shift Report'
    _order = 'work_date, workunit_id, workshift'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    # @api.returns('self')
    # def _default_items_get(self):
    #     print '=========================='
    #     print self
    #     print self.report_id
    #     if self.report_id:
    #         return self.env['hs_pts.cmsp.fabricshiftreport_item'].sudo().search([('report_id', '=', self.report_id)])

    def _default_workshift_get(self):
        workshift = ''
        now = datetime.datetime.now()
        hour = now.hour + 8
        if hour >= 8 and hour < 16:
            workshift = 'morning'
        elif hour >= 16 and hour < 24:
            workshift = 'middle'
        else:
            workshift = 'night'
        return workshift

    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', track_visibility='onchange', required=True)
    work_date = fields.Date('Work Date', default=fields.Datetime.now, required=True)
    workshift = fields.Selection(
        [('morning', 'Morning Shift'), ('middle', 'Middle Shift'), ('night', 'Night Shift')],
        string='Work Shift', default=_default_workshift_get, translate=True, required=True)
    display_workshift = fields.Char(string='Work Shift', compute='_compute_display_workshift', translate=True)
    workgroup_id = fields.Many2one('hs_pts.cmsp.workgroup', string='Work Group', track_visibility='onchange', required=True)

    slitter_weight = fields.Float('Slitter edge yarn（kg)', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_get, ondelete='restrict', required=True)
    remark = fields.Text('Remark')
    item_ids = fields.One2many('hs_pts.cmsp.fabricshiftreport_item', 'report_id', string='Report Items')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    _sql_constraints = [
        ('fabricshiftreport_unique', 'unique(workunit_id, work_date, workshift)',
         "Another record already exists with this workunit, workdate, workshift!"),
    ]

    @api.one
    @api.depends('running_time')
    def _compute_display_runningtime(self):
        hours = self.running_time/60
        minutes = self.running_time - hours*60
        self.display_runningtime = '%dh%dmin' % (hours, minutes)

    @api.one
    @api.depends('workshift')
    def _compute_display_workshift(self):
        wsdc = [('morning', u'早班'), ('middle', u'中班'), ('night', u'晚班')]
        for item in wsdc:
            if item[0] == self.workshift:
                self.display_workshift = item[1]

    @api.one
    @api.depends('workunit_id', 'work_date', 'workshift')
    def _compute_display_name(self):
        bc=''
        if self.workshift:
            if self.workshift == 'morning':
                bc = u'早班'
            elif self.workshift == 'middle':
                bc = u'中班'
            elif self.workshift == 'night':
                bc = u'晚班'
        names = [self.work_date, self.workunit_id.full_name, bc]
        self.display_name = u'日期：%s 机台：%s 班次：%s' % (names[0], names[1], names[2])


class FabricShiftReportItem(models.Model):
    _name = 'hs_pts.cmsp.fabricshiftreport_item'
    _description = 'Fabric Shift Report Item'
    _order = 'report_id, model_id'
    _rec_name = 'report_id'
    _inherit = ['mail.thread']

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    report_id = fields.Many2one('hs_pts.cmsp.fabricshiftreport_main', string='Shift Report', track_visibility='onchange', required=True, readonly=True)
    model_id = fields.Many2one('hs_pts.cmsp.productmodel', string='Model', track_visibility='onchange', required=True)
    output_length = fields.Float('Output（m）', track_visibility='onchange')
    inspect_length = fields.Float('Inspect（m）', track_visibility='onchange')
    reject_length = fields.Float('Reject（m）', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_get, ondelete='restrict', required=True)
    remark = fields.Text('Remark')
    rolling_number = fields.Char('Rolling Number', track_visibility='onchange')
    running_time = fields.Integer('Eq. Running (min)', track_visibility='onchange')
    display_runningtime = fields.Char(string='Eq. Running', compute='_compute_display_runningtime')

    _sql_constraints = [
        ('fabricshiftreportitem_unique', 'unique(report_id, model_id)',
         "Another record already exists with this report!"),
    ]

    @api.one
    @api.depends('running_time')
    def _compute_display_runningtime(self):
        hours = self.running_time/60
        minutes = self.running_time - hours*60
        self.display_runningtime = '%dh%dmin' % (hours, minutes)

    @api.onchange('report_id')
    def getreport(self):
        self.ensure_one()
        p = self.env['hs_pts.cmsp.fabricshiftreport_main'].sudo().search([('workunit_id', '=', self.report_id.workunit_id.id),
                                                   ('work_date', '=', self.report_id.work_date),
                                                   ('workshift', '=', self.report_id.workshift)])
        if p.id:
            self.report_id = p.id

    def onchange_report(self):
        self.getreport(self)

    @api.onchange('model_id')
    def generateoutput(self):
        self.ensure_one()
        # print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        wd = '%s %s' % (self.report_id.work_date, '00:00:00')
        # print wd
        # begin = datetime.datetime.combine(self.report_id.work_date, datetime.time())
        begin = datetime.datetime.strptime(wd, "%Y-%m-%d %H:%M:%S")
        if self.report_id.workshift == 'morning':
            # begin = begin + datetime.timedelta(hours=8) #UTC时间的问题，此处减8小时
            begin = begin + datetime.timedelta(hours=0)
        elif self.report_id.workshift == 'middle':
            # begin = begin + datetime.timedelta(hours=16)
            begin = begin + datetime.timedelta(hours=8)
        else:
            # begin = begin + datetime.timedelta(hours=24)
            begin = begin + datetime.timedelta(hours=16)
        end = begin + datetime.timedelta(hours=8)
        # print begin
        # print end
        # print type(begin)
        # print begin.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # print end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # print self.model_id.id
        # print self.report_id.workunit_id.id
        # print self.report_id.workgroup_id.id
        if self.model_id.id:
            products = self.env['hs_pts.cmsp.fabricroll'].search([('product_date', '>', begin.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                              ('product_date', '<=', end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                              ('model_id', '=', self.model_id.id),
                                                                  ('workunit_id', '=', self.report_id.workunit_id.id),
                                                                  ('workgroup_id', '=', self.report_id.workgroup_id.id)])
            amount = 0
            for item in products:
                amount = amount + item.roll_length
            self.output_length = amount
            # print amount

    def onchange_model(self):
        self.generateoutput(self)


class FabricShiftReportReport(models.TransientModel):
    _name = 'hs_pts.cmsp.fabricshiftreport.report.wizard'

    workunit_id = fields.Many2one('hs_pts.cmsp.workunit', string='WorkUnit', track_visibility='onchange', required=True)
    starttime = fields.Date('Start Time', required=True)
    endtime = fields.Date('End Time', required=True)

    @api.multi
    def confirm_button(self):
        self.ensure_one()
        # print '===================='
        # print self.starttime
        # print self.endtime
        # print self.workunit_id

        # start = self.starttime.replace('-','')
        # end = self.endtime.replace('-','')
        # print start
        # print end

        now = datetime.datetime.now()
        otherStyleTime = now.strftime("%Y%m%d%H%M%S")

        filename = 'fabricshiftreport-%s' % (otherStyleTime)
        return {
            'type': 'ir.actions.act_url',
            'url': '/hs_pts_cmsp/exporter/download_fabricshiftreport?workunit_id=%s&workunit_fullname=%s&starttime=%s&endtime=%s&filename=%s' %
                   (self.workunit_id.id, self.workunit_id.full_name.replace('#', '').replace('&', '').replace('?', ''), self.starttime, self.endtime, filename),
            'target': 'self',
        }


