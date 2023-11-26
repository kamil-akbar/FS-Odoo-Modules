# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LaundryItem(models.Model):
    _name = "laundry.item"
    _description = "Laundry item"
    _order = 'id desc'

    name = fields.Char(string='Laundry Items')
    color = fields.Integer(string='Color')


class HotelLaundry(models.Model):
    _name = "laundry.service.type"
    _description = "Laundry Service Type"
    _rec_name = 'service_name'
    _order = 'id desc'

    service_name = fields.Char('Service Name', required=True, )
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    charges = fields.Monetary(string='Price', required=True)
    laundry_service_type_number = fields.Char(string='', copy=False, readonly=True,
                                              default=lambda self: 'New')

    @api.model
    def create(self, vals):
        rec = super(HotelLaundry, self).create(vals)
        if vals.get('laundry_service_type_number', 'New') == 'New':
            rec['laundry_service_type_number'] = self.env['ir.sequence'].next_by_code('rest.laundry.sequence') or 'New'
        return rec


class HotelLaundryDetails(models.Model):
    _name = "laundry.service"
    _description = "Laundry Service Details"
    _rec_name = 'service_name_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    laundry_service_number = fields.Char(string='', copy=False, readonly=True,
                                         default=lambda self: 'New')
    service_name_id = fields.Many2one('laundry.service.type', string='Service Name', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    charges = fields.Monetary(string='Charge', related='service_name_id.charges', required=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    responsible_id = fields.Many2one('hr.employee', domain=[('is_staff', '=', True)], string='Responsible',
                                     required=True)
    deadline_date = fields.Datetime(string='Deadline')
    booking_id = fields.Many2one('hotel.booking', required=True)
    customer_id = fields.Many2one(related='booking_id.customer_id', string='Customer')
    laundry_item_ids = fields.Many2many('laundry.item', string='Laundry Items', required=True)
    color = fields.Integer(string='Color')
    quantity = fields.Integer(string='Quantity', required=True)
    total_charges = fields.Monetary(string='Total Charges', compute='laundry_charges')
    stages = fields.Selection(
        [('Request', 'Request'), ('In Progress', 'In Progress'), ('Completed', 'Completed')],
        string='Stages', default='Request')

    def confirm_to_send_laundry(self):
        self.stages = 'In Progress'

    def laundry_to_done(self):
        self.stages = 'Completed'

    @api.depends('charges', )
    def laundry_charges(self):
        for rec in self:
            total_charges = rec.total_charges + (rec.charges * rec.quantity)
            rec.total_charges = total_charges

    @api.model
    def create(self, vals):
        rec = super(HotelLaundryDetails, self).create(vals)
        if vals.get('laundry_service_number', 'New') == 'New':
            rec['laundry_service_number'] = self.env['ir.sequence'].next_by_code('rest.laundry.sequence') or 'New'
        return rec

    @api.onchange('room_id')
    def _onchange_room_id(self):
        id = self._context.get('booking_id')
        room_ids = self.env['hotel.room.details'].sudo().search([('booking_id', '=', id)]).mapped('room_id').mapped(
            'id')
        return {'domain': {'room_id': [('id', 'in', room_ids)]}}
