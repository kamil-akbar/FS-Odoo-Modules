# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HotelHousekeepingStaff(models.Model):
    _inherit = 'hr.employee'
    _description = "Housekeeping Employees Details"
    _order = 'id desc'

    is_staff = fields.Boolean(string='Staff')


class HotelHousekeeping(models.Model):
    _name = "hotel.housekeeping"
    _description = "Housekeeping Details"
    _rec_name = 'housekeeping_type'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    housekeeping_type = fields.Selection([('Cleaning', 'Cleaning'), ('Maintenance', 'Maintenance')],
                                         string='Housekeeping Type', required=True)
    is_room = fields.Boolean(string='Room')
    is_hall = fields.Boolean(string='Hall')
    room_id = fields.Many2one('hotel.room', string='Room Number' )
    hall_id = fields.Many2one('hotel.hall', string='Hall Number' )
    end_date = fields.Date("Deadline Date", )
    state = fields.Selection([('Assign', 'Assign'), ('In Progress', 'In Progress'), ('Complete', 'Complete')], 'State',default="Assign")
    housekeeping_number = fields.Char(string='', copy=False, readonly=True,
                                      default=lambda self: 'New')
    desc = fields.Text(string="Description")
    housekeeper_ids = fields.Many2many('hr.employee', domain="[('is_staff','=',True)]")
    start_datetime = fields.Datetime(string="Start")
    end_datetime = fields.Datetime(string="End")

    @api.model
    def create(self, vals):
        rec = super(HotelHousekeeping, self).create(vals)
        if vals.get('housekeeping_number', 'New') == 'New':
            rec['housekeeping_number'] = self.env['ir.sequence'].next_by_code(
                'rest.transport.booking') or 'New'
        return rec

    def assign_to_progress(self):
        self.state = 'In Progress'

    def dirty_to_clean(self):
        self.state = 'Complete'
