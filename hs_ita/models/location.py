# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _


class Location(osv.osv):
    _name = 'hs_ita.location'
    _description = 'Location'
    _order = 'parent_id, sequence, name'

    def _loc_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'name': fields.char('Name', required=True),
        'complete_name': fields.function(_loc_name_get_fnc, type="char", string='Complete Name'),
        'parent_id': fields.many2one('hs_ita.location', 'Parent Location', select=True),
        'child_ids': fields.one2many('hs_ita.location', 'parent_id', 'Child Locations'),
        'asset_ids': fields.one2many('hs_ita.asset', 'location_id', 'Assets'),
        'sequence': fields.integer('Sequence'),
        'active': fields.boolean('Active?', default=True),
        'note': fields.text('Note'),
    }

    _constraints = [
        (osv.osv._check_recursion, _('Error! You cannot create recursive locations.'), ['parent_id'])
    ]

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        if context is None:
            context = {}
        reads = self.read(cr, uid, ids, ['name', 'parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res
