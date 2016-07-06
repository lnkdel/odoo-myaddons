# -*- coding: utf-8 -*-

from openerp import http
import json
from openerp.http import request, serialize_exception as _serialize_exception
from cStringIO import StringIO
from collections import deque
from openerp.addons.web.controllers.main import serialize_exception,content_disposition
import base64

try:
    import xlwt
except ImportError:
    xlwt = None

TIMEOUT = 20

try:
    import xlwt
except ImportError:
    xlwt = None


class Exporter(http.Controller):
    @http.route('/hs_pts_cmsp/exporter/download_document', type='http', auth="public")
    def download_document(self, model, field, ids, filename=None, **kw):
         """ Download link for files stored as binary fields.
         :param str model: name of the model to fetch the binary from
         :param str field: binary field
         :param str id: id of the record from which to fetch the binary
         :param str filename: field holding the file's name, if any
         :returns: :class:`werkzeug.wrappers.Response`
         """
         Model = request.registry[model]
         cr, uid, context = request.cr, request.uid, request.context
         fields = [field]
         # res = Model.read(cr, uid, ids, ['rollno', 'length', 'weight'], context)[0]

         print ids
         # tids = [int(s) for s in ids]
         # print tids
         list_str = []
         for s in ids:
             list_str.append(s)

         print ids.split(',')

         # res = Model.read(cr, uid, ids, ['rollno', 'length', 'weight'], context)[0]
         res = Model.search(cr, uid, [('id', 'in', ids.split(','))], context)
         # self.search(cr, uid, [('state', '=', 'inprogress')], context=context)

         print res
         print field
         print res.get("rollno")
         print '123123'
         # filecontent = base64.b64decode(res.get("rollno") or '')
         filecontent = res.get("rollno")
         print 'zzzzzzzzzzzzzz'
         print filecontent
         if not filecontent:
             print 'aasssssssssssssssssssss'
             return request.not_found()
         else:
             if not filename:
                 filename = '%s_%s' % (model.replace('.', '_'), ids.replace(',', '-'))
             return request.make_response(filecontent,
                                [('Content-Type', 'application/octet-stream'),
                                 ('Content-Disposition', content_disposition(filename))])


    @http.route('/hs_pts_cmsp/exporter/download_xls_prepreg',type='http', auth="public")
    def download_xls_prepreg(self, model, ids, operator, sheetname='Sheet1', filename=None, **kw):
        Model = request.registry[model]
        # prepregModel = request.registry['hs_pts_cmsp.productmodel']
        cr, uid, context = request.cr, request.uid, request.context

        if '.xls' in filename:
            filename = filename[:-4]
        intids = [int(x) for x in ids.split(',') if x]
        # print fields.split(',')

        # print '==============='
        # prepregrolls = Model.read(cr, uid, intids, fields.split(','), context)
        # prepregrolls = Model.read(cr, uid, intids, ['rollno', 'length', 'weight', 'hs_pts_cmsp.productmodel.name'], context)

        query = u"""
              SELECT
                  hs_pts_cmsp_productmodel.product_no,
                  hs_pts_cmsp_productmodel.materiel_name,
                  hs_pts_cmsp_productmodel.name,
                  hs_pts_cmsp_productmodel.width,
                  (CASE hs_pts_cmsp_productmodel.packing
                    WHEN 'standard' THEN '标准'
                    WHEN 'simpleness' THEN '简单'
                    WHEN 'neutral' THEN '中性' END) as packing,
                  (CASE hs_pts_cmsp_productmodel.iscutting
                    WHEN TRUE THEN '是'
                    WHEN FALSE THEN '否'
                    ELSE '空' END) as iscutting,
                  hs_pts_cmsp_productmodel.unit,
                  hs_pts_cmsp_prepregroll.id,
                  hs_pts_cmsp_prepregroll.lot_no,
                  hs_pts_cmsp_prepregroll.roll_length,
                  hs_pts_cmsp_prepregroll.weight,
                  hs_pts_cmsp_qualitylevel.name,
                  hs_pts_cmsp_prepregroll.create_date
                FROM
                  public.hs_pts_cmsp_prepregroll,
                  public.hs_pts_cmsp_productmodel,
                  public.hs_pts_cmsp_workgroup,
                  hs_pts_cmsp_qualitylevel
                WHERE
                  hs_pts_cmsp_prepregroll.model_id = hs_pts_cmsp_productmodel.id AND
                  hs_pts_cmsp_workgroup.id = hs_pts_cmsp_prepregroll.workgroup_id And
                  hs_pts_cmsp_qualitylevel.id = hs_pts_cmsp_prepregroll.qualitylevel AND
                  hs_pts_cmsp_prepregroll.id in (%s)
                      """ % (ids)

        cr.execute(query)
        prepregrolls = []
        for row in cr.fetchall():
            prepregrolls.append(row)

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(sheetname)
        header_bold = xlwt.easyxf("font: bold on; pattern: pattern solid, fore_colour gray25;")
        header_plain = xlwt.easyxf("pattern: pattern solid, fore_colour gray25;")
        bold = xlwt.easyxf("font: bold on;")

        worksheet.write(0, 0, u'产品编码')
        worksheet.write(0, 1, u'产品名称')
        worksheet.write(0, 2, u'规格')
        worksheet.write(0, 3, u'幅宽(M)')
        worksheet.write(0, 4, u'包装要求')
        worksheet.write(0, 5, u'裁边')
        worksheet.write(0, 6, u'单位')
        worksheet.write(0, 7, u'卷号')
        worksheet.write(0, 8, u'批号')
        worksheet.write(0, 9, u'长度M')
        worksheet.write(0, 10, u'数量')
        worksheet.write(0, 11, u'毛重KG')
        worksheet.write(0, 12, u'品级')
        worksheet.write(0, 13, u'备注')
        worksheet.write(0, 14, u'进库时间')
        worksheet.write(0, 15, u'操作员')

        r = 1
        for row in prepregrolls:
            worksheet.write(r, 0, row[0])
            worksheet.write(r, 1, row[1])
            worksheet.write(r, 2, row[2])
            worksheet.write(r, 3, row[3])
            worksheet.write(r, 4, row[4])
            worksheet.write(r, 5, row[5])
            worksheet.write(r, 6, row[6])
            worksheet.write(r, 7, row[7])
            worksheet.write(r, 8, row[8])
            worksheet.write(r, 9, row[9])
            worksheet.write(r, 10, row[9])
            worksheet.write(r, 11, row[10])
            worksheet.write(r, 12, row[11])
            worksheet.write(r, 13, '')
            worksheet.write(r, 14, row[12])
            worksheet.write(r, 15, operator)
            r = r +1

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + filename + '.xls;')])
        workbook.save(response.stream)
        return response


    @http.route('/hs_pts_cmsp/exporter/download_xls_fabric',type='http', auth="public")
    def download_xls_fabric(self, model, ids, sheetname='Sheet1', filename=None, **kw):
        cr, uid, context = request.cr, request.uid, request.context

        if '.xls' in filename:
            filename = filename[:-4]

        query = u"""
              SELECT
                  hs_pts_cmsp_productmodel.product_no,
                  hs_pts_cmsp_productmodel.materiel_name,
                  hs_pts_cmsp_productmodel.name,
                  hs_pts_cmsp_productmodel.width,
                  (CASE hs_pts_cmsp_productmodel.packing
                    WHEN 'standard' THEN '标准'
                    WHEN 'simpleness' THEN '简单'
                    WHEN 'neutral' THEN '中性' END) as packing,
                  (CASE hs_pts_cmsp_productmodel.iscutting
                    WHEN TRUE THEN '是'
                    WHEN FALSE THEN '否'
                    ELSE '空' END) as iscutting,
                  hs_pts_cmsp_productmodel.unit,
                  hs_pts_cmsp_fabricroll.id,
                  hs_pts_cmsp_fabricroll.lot_no,
                  hs_pts_cmsp_fabricroll.roll_length,
                  hs_pts_cmsp_fabricroll.weight,
                  hs_pts_cmsp_qualitylevel.name,
                  hs_pts_cmsp_fabricroll.create_date
                FROM
                  public.hs_pts_cmsp_fabricroll,
                  public.hs_pts_cmsp_productmodel,
                  public.hs_pts_cmsp_workgroup,
                  hs_pts_cmsp_qualitylevel
                WHERE
                  hs_pts_cmsp_fabricroll.model_id = hs_pts_cmsp_productmodel.id AND
                  hs_pts_cmsp_workgroup.id = hs_pts_cmsp_fabricroll.workgroup_id AND
                  hs_pts_cmsp_qualitylevel.id = hs_pts_cmsp_fabricroll.qualitylevel AND
                  hs_pts_cmsp_fabricroll.id in (%s)
                    """ % (ids)

        cr.execute(query)
        prepregrolls = []
        for row in cr.fetchall():
            prepregrolls.append(row)

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(sheetname)

        worksheet.write(0, 0, u'产品编码')
        worksheet.write(0, 1, u'产品名称')
        worksheet.write(0, 2, u'规格')
        worksheet.write(0, 3, u'幅宽(M)')
        worksheet.write(0, 4, u'包装要求')
        worksheet.write(0, 5, u'裁边')
        worksheet.write(0, 6, u'单位')
        worksheet.write(0, 7, u'卷号')
        worksheet.write(0, 8, u'批号')
        worksheet.write(0, 9, u'长度M')
        worksheet.write(0, 10, u'数量')
        worksheet.write(0, 11, u'毛重KG')
        worksheet.write(0, 12, u'品级')
        worksheet.write(0, 13, u'备注')
        worksheet.write(0, 14, u'进库时间')
        worksheet.write(0, 15, u'操作员')

        r = 1
        for row in prepregrolls:
            print row
            worksheet.write(r, 0, row[0])
            worksheet.write(r, 1, row[1])
            worksheet.write(r, 2, row[2])
            worksheet.write(r, 3, row[3])
            worksheet.write(r, 4, row[4])
            worksheet.write(r, 5, row[5])
            worksheet.write(r, 6, row[6])
            worksheet.write(r, 7, row[7])
            worksheet.write(r, 8, row[8])
            worksheet.write(r, 9, row[9])
            worksheet.write(r, 10, row[9])
            worksheet.write(r, 11, row[10])
            worksheet.write(r, 12, row[11])
            worksheet.write(r, 13, '')
            worksheet.write(r, 14, row[12])
            worksheet.write(r, 15, 1)
            r = r +1

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + filename + '.xls;')])
        workbook.save(response.stream)
        return response


    @http.route('/hs_pts_cmsp/exporter/download_xls_resin',type='http', auth="public")
    def download_xls_resin(self, model, ids, sheetname='Sheet1', filename=None, **kw):
        cr, uid, context = request.cr, request.uid, request.context

        if '.xls' in filename:
            filename = filename[:-4]

        query = u"""
              SELECT
                  hs_pts_cmsp_productmodel.product_no,
                  hs_pts_cmsp_productmodel.materiel_name,
                  hs_pts_cmsp_productmodel.name,
                  (CASE hs_pts_cmsp_productmodel.packing
                    WHEN 'standard' THEN '标准'
                    WHEN 'simpleness' THEN '简单'
                    WHEN 'neutral' THEN '中性' END) as packing,
                  hs_pts_cmsp_productmodel.unit,
                  hs_pts_cmsp_resinlot.id,
                  hs_pts_cmsp_resinlot.lot_no,
                  hs_pts_cmsp_resinlot.content,
                  hs_pts_cmsp_resinlot.weight,
                  hs_pts_cmsp_resinlot.shelflife,
                  hs_pts_cmsp_resinlot.create_date
                FROM
                  public.hs_pts_cmsp_resinlot,
                  public.hs_pts_cmsp_productmodel,
                  public.hs_pts_cmsp_workgroup
                WHERE
                  hs_pts_cmsp_resinlot.model_id = hs_pts_cmsp_productmodel.id AND
                  hs_pts_cmsp_workgroup.id = hs_pts_cmsp_resinlot.workgroup_id AND
                  hs_pts_cmsp_resinlot.id in (%s)
                    """ % (ids)

        cr.execute(query)
        prepregrolls = []
        for row in cr.fetchall():
            prepregrolls.append(row)

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(sheetname)

        worksheet.write(0, 0, u'产品编码')
        worksheet.write(0, 1, u'产品名称')
        worksheet.write(0, 2, u'规格')
        worksheet.write(0, 3, u'包装要求')
        worksheet.write(0, 4, u'单位')
        worksheet.write(0, 5, u'卷号')
        worksheet.write(0, 6, u'批号')
        worksheet.write(0, 7, u'固含量')
        worksheet.write(0, 8, u'毛重KG')
        worksheet.write(0, 9, u'保质期')
        worksheet.write(0, 10, u'备注')
        worksheet.write(0, 11, u'进库时间')
        worksheet.write(0, 12, u'操作员')

        r = 1
        for row in prepregrolls:
            print row
            worksheet.write(r, 0, row[0])
            worksheet.write(r, 1, row[1])
            worksheet.write(r, 2, row[2])
            worksheet.write(r, 3, row[3])
            worksheet.write(r, 4, row[4])
            worksheet.write(r, 5, row[5])
            worksheet.write(r, 6, row[6])
            worksheet.write(r, 7, row[7])
            worksheet.write(r, 8, row[8])
            worksheet.write(r, 9, row[9])
            worksheet.write(r, 10, '')
            worksheet.write(r, 11, row[10])
            worksheet.write(r, 12, 1)
            r = r +1

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + filename + '.xls;')])
        workbook.save(response.stream)
        return response


    @http.route('/hs_pts_cmsp/exporter/download_xls_sizing',type='http', auth="public")
    def download_xls_sizing(self, model, ids, sheetname='Sheet1', filename=None, **kw):
        cr, uid, context = request.cr, request.uid, request.context

        if '.xls' in filename:
            filename = filename[:-4]

        query = u"""
              SELECT
                  hs_pts_cmsp_productmodel.product_no,              --0
                  hs_pts_cmsp_productmodel.materiel_name,          --1
                  hs_pts_cmsp_productmodel.name,                    --2
                  (CASE hs_pts_cmsp_productmodel.packing
                    WHEN 'standard' THEN '标准'
                    WHEN 'simpleness' THEN '简单'
                    WHEN 'neutral' THEN '中性' END) as packing,     --3
                  hs_pts_cmsp_productmodel.unit,                    --4
                  hs_pts_cmsp_sizinglot.id,                     --5
                  hs_pts_cmsp_sizinglot.lot_no,                    --6
                  hs_pts_cmsp_sizinglot.content,                    --7
                  hs_pts_cmsp_sizinglot.weight,                     --8
                  hs_pts_cmsp_sizinglot.shelflife,                  --9
                  hs_pts_cmsp_sizinglot.create_date                  --10
                FROM
                  public.hs_pts_cmsp_sizinglot,
                  public.hs_pts_cmsp_productmodel,
                  public.hs_pts_cmsp_workgroup
                WHERE
                  hs_pts_cmsp_sizinglot.model_id = hs_pts_cmsp_productmodel.id AND
                  hs_pts_cmsp_workgroup.id = hs_pts_cmsp_sizinglot.workgroup_id And
                  hs_pts_cmsp_sizinglot.id in (%s)
                    """ % (ids)

        cr.execute(query)
        prepregrolls = []
        for row in cr.fetchall():
            prepregrolls.append(row)

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(sheetname)

        worksheet.write(0, 0, u'产品编码')
        worksheet.write(0, 1, u'产品名称')
        worksheet.write(0, 2, u'规格')
        worksheet.write(0, 3, u'包装要求')
        worksheet.write(0, 4, u'单位')
        worksheet.write(0, 5, u'卷号')
        worksheet.write(0, 6, u'批号')
        worksheet.write(0, 7, u'固含量')
        worksheet.write(0, 8, u'毛重KG')
        worksheet.write(0, 9, u'保质期')
        worksheet.write(0, 10, u'备注')
        worksheet.write(0, 11, u'进库时间')
        worksheet.write(0, 12, u'操作员')

        r = 1
        for row in prepregrolls:
            print row
            worksheet.write(r, 0, row[0])
            worksheet.write(r, 1, row[1])
            worksheet.write(r, 2, row[2])
            worksheet.write(r, 3, row[3])
            worksheet.write(r, 4, row[4])
            worksheet.write(r, 5, row[5])
            worksheet.write(r, 6, row[6])
            worksheet.write(r, 7, row[7])
            worksheet.write(r, 8, row[8])
            worksheet.write(r, 9, row[9])
            worksheet.write(r, 10, '')
            worksheet.write(r, 11, row[10])
            worksheet.write(r, 12, 1)
            r = r +1

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + filename + '.xls;')])
        workbook.save(response.stream)
        return response

    @http.route('/hs_pts_cmsp/exporter/download_fabricshiftreport',type='http', auth="public")
    def download_fabricshiftreport(self, workunit_id, workunit_fullname, starttime, endtime, sheetname='Sheet1', filename=None, **kw):
        cr, uid, context = request.cr, request.uid, request.context

        if '.xls' in filename:
            filename = filename[:-4]

        sheetname = workunit_fullname+'#'

        query = u"""
              SELECT
                      hs_pts_cmsp_workunit.full_name AS unitname,
                      hs_pts_cmsp_fabricshiftreport_main.work_date,
                      CASE hs_pts_cmsp_fabricshiftreport_main.workshift
                        WHEN 'morning' THEN '早班'
                        WHEN 'middle' THEN '中班'
                        WHEN 'night' THEN '夜班' END AS workshift,
                      hs_pts_cmsp_workgroup.name AS workgroup,
                      hs_pts_cmsp_fabricshiftreport_item.running_time/60 || 'h' || (hs_pts_cmsp_fabricshiftreport_item.running_time - (hs_pts_cmsp_fabricshiftreport_item.running_time/60)*60) || 'm' AS runningtime,
                      hs_pts_cmsp_productmodel.name AS modelname,
                      hs_pts_cmsp_productmodel.width,
                      hs_pts_cmsp_fabricshiftreport_item.output_length,
                      hs_pts_cmsp_fabricshiftreport_item.inspect_length,
                      hs_pts_cmsp_fabricshiftreport_item.reject_length,
                      hs_pts_cmsp_fabricshiftreport_item.rolling_number,
                      hs_pts_cmsp_fabricshiftreport_main.slitter_weight,
                      hr_employee.badge_no,
                      hr_employee.name_related,
                      hs_pts_cmsp_fabricshiftreport_main.remark
                    FROM
                      public.hs_pts_cmsp_fabricshiftreport_main,
                      public.hs_pts_cmsp_fabricshiftreport_item,
                      public.hs_pts_cmsp_productmodel,
                      public.hs_pts_cmsp_workgroup,
                      public.hs_pts_cmsp_workunit,
                      public.hr_employee
                    WHERE
                      hs_pts_cmsp_fabricshiftreport_main.id = hs_pts_cmsp_fabricshiftreport_item.report_id AND
                      hs_pts_cmsp_fabricshiftreport_main.workgroup_id = hs_pts_cmsp_workgroup.id AND
                      hs_pts_cmsp_fabricshiftreport_main.workunit_id = hs_pts_cmsp_workunit.id AND
                      hs_pts_cmsp_fabricshiftreport_main.employee_id = hr_employee.id AND
                      hs_pts_cmsp_fabricshiftreport_item.model_id = hs_pts_cmsp_productmodel.id
                      AND hs_pts_cmsp_fabricshiftreport_main.workunit_id = %s
                      AND hs_pts_cmsp_fabricshiftreport_main.work_date > '%s'
                      AND hs_pts_cmsp_fabricshiftreport_main.work_date <= '%s'
                      order by hs_pts_cmsp_fabricshiftreport_main.work_date
                    """ % (workunit_id, starttime, endtime)

        # print query

        cr.execute(query)
        prepregrolls = []
        for row in cr.fetchall():
            prepregrolls.append(row)

        g_normalFont = xlwt.Font()
        g_normalFont.name = u'宋体'
        g_normalFont._weight = 11
        g_normalFont.height = 11*20
        g_normalStyle = xlwt.XFStyle()
        g_normalStyle.font = g_normalFont
        g_normalStyle.alignment.wrap = 1
        g_normalStyle.alignment.HORZ_CENTER = 1
        g_normalStyle.alignment.VERT_CENTER = 1
        g_normalStyle.borders.left = 1
        g_normalStyle.borders.right = 1
        g_normalStyle.borders.top = 1
        g_normalStyle.borders.bottom = 1

        g_headerFont = xlwt.Font()
        g_headerFont.name = u'宋体'
        g_headerFont.bold = True  # 使用粗体
        g_headerFont._weight = 18  # 设置字体大小
        g_headerFont.height = 18*20
        g_headerStyle = xlwt.XFStyle()
        g_headerStyle.font = g_headerFont  # 设置字体
        g_headerStyle.alignment.horz = 2  # 居中
        g_headerStyle.borders.left = 1
        g_headerStyle.borders.right = 1
        g_headerStyle.borders.top = 1
        g_headerStyle.borders.bottom = 1

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(sheetname)

        worksheet.write_merge(0, 0, 0, 12, u'                 编织车间生产日报  Production Daily of Woven workshop          版本号：A    ', g_headerStyle)
        # worksheet.insert_bitmap('/hs_pts_cmsp/static/description/image007.gif', 0, 2)
        worksheet.write_merge(1, 1, 0, 12, u'机台号：%s#' % (workunit_fullname), g_normalStyle)
        worksheet.write(1, 13, '', xlwt.easyxf('font:height 240'))

        tall_style = xlwt.easyxf('font:height 580;')
        first_row = worksheet.row(0)
        first_row.set_style(tall_style)

        first_col = worksheet.col(0)
        first_col.width = 256*14
        five_col = worksheet.col(4)
        five_col.width = 256*25
        ten_col = worksheet.col(9)
        ten_col.width = 256*25
        last_col = worksheet.col(12)
        last_col.width = 256*25
        worksheet.col(1).width = 10*256
        worksheet.col(2).width = 10*256
        worksheet.col(3).width = 10*256
        worksheet.col(5).width = 10*256
        worksheet.col(6).width = 10*256
        worksheet.col(7).width = 10*256
        worksheet.col(8).width = 10*256
        worksheet.col(10).width = 10*256
        worksheet.col(11).width = 10*256

        # worksheet.write(2, 0, u'日期', g_normalStyle)
        # worksheet.write(2, 1, u'班次', g_normalStyle)
        # worksheet.write(2, 2, u'班组', g_normalStyle)
        # worksheet.write(2, 3, u'设备运行时间', g_normalStyle)
        # worksheet.write(2, 4, u'产品规格', g_normalStyle)
        # worksheet.write(2, 5, u'幅宽', g_normalStyle)
        # worksheet.write(2, 6, u'生产量', g_normalStyle)
        # worksheet.write(2, 7, u'送检', g_normalStyle)
        # worksheet.write(2, 8, u'废布', g_normalStyle)
        # worksheet.write(2, 9, u'收卷卷号', g_normalStyle)
        # worksheet.write(2, 10, u'废边纱', g_normalStyle)
        # worksheet.write(2, 11, u'记录人', g_normalStyle)
        # worksheet.write(2, 12, u'备注', g_normalStyle)
        worksheet.write_merge(2, 4, 0, 0, u'日期', g_normalStyle)
        worksheet.write_merge(2, 4, 1, 1, u'班次', g_normalStyle)
        worksheet.write_merge(2, 4, 2, 2, u'班组', g_normalStyle)
        worksheet.write_merge(2, 4, 3, 3, u'设备运行时间', g_normalStyle)
        worksheet.write_merge(2, 4, 4, 4, u'产品规格', g_normalStyle)
        worksheet.write_merge(2, 4, 5, 5, u'幅宽', g_normalStyle)
        worksheet.write_merge(3, 4, 6, 6, u'生产量', g_normalStyle)
        worksheet.write_merge(3, 4, 7, 7, u'送检', g_normalStyle)
        worksheet.write_merge(3, 4, 8, 8, u'废布', g_normalStyle)
        worksheet.write_merge(2, 4, 9, 9, u'收卷卷号', g_normalStyle)
        worksheet.write_merge(2, 4, 10, 10, u'废边纱', g_normalStyle)
        worksheet.write_merge(2, 4, 11, 11, u'记录人', g_normalStyle)
        worksheet.write_merge(2, 4, 12, 12, u'备注', g_normalStyle)
        worksheet.write_merge(2, 2, 6, 8, u'          产量（m）', g_normalStyle)
        worksheet.write(2, 13, '', xlwt.easyxf('font:height 320'))

        r = 5
        for row in prepregrolls:
            # print row
            worksheet.write(r, 0, row[1], g_normalStyle)
            worksheet.write(r, 1, row[2], g_normalStyle)
            worksheet.write(r, 2, row[3], g_normalStyle)
            worksheet.write(r, 3, row[4], g_normalStyle)
            worksheet.write(r, 4, row[5], g_normalStyle)
            worksheet.write(r, 5, row[6], g_normalStyle)
            worksheet.write(r, 6, row[7], g_normalStyle)
            worksheet.write(r, 7, row[8], g_normalStyle)
            worksheet.write(r, 8, row[9], g_normalStyle)
            worksheet.write(r, 9, row[10], g_normalStyle)
            worksheet.write(r, 10, row[11], g_normalStyle)
            badgeno = ''
            if row[12] is not None:
                badgeno = row[12]
            worksheet.write(r, 11, '%s%s' % (badgeno, row[13]), g_normalStyle)
            worksheet.write(r, 12, row[14], g_normalStyle)
            worksheet.write(r, 13, '', xlwt.easyxf('font:height 320'))
            r = r +1

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + filename + '.xls;')])

        workbook.save(response.stream)
        return response