# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Location(models.Model):
    _name = 'location.detail'
    _description = 'Location details'
    _order = 'id desc'

    name = fields.Char('Location Name', required=True)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street-2')
    city = fields.Char(string='City')


class HotelTransportVehicle(models.Model):
    _name = 'transport.vehicle'
    _description = 'Vehicle details'
    _order = 'id desc'

    avatar = fields.Binary()
    name = fields.Char('Vehicle Type', required=True)


class TransportVehicle(models.Model):
    _name = 'vehicle.type'
    _description = 'Vehicle details'
    _order = 'id desc'

    avatar = fields.Binary()
    name = fields.Char('Vehicle Name', required=True)
    number = fields.Char('Vehicle Number ', required=True)
    vehicle_number = fields.Char(string='', copy=False, readonly=True, default=lambda self: 'New')
    vehicle_type_id = fields.Many2one('transport.vehicle', 'Vehicle Type', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    charges = fields.Monetary('Charge', required=True)
    capacity = fields.Integer(string='Capacity', required=True)

    @api.model
    def create(self, vals):
        rec = super(TransportVehicle, self).create(vals)
        if vals.get('vehicle_number', 'New') == 'New':
            rec['vehicle_number'] = self.env['ir.sequence'].next_by_code('rest.vehicle.sequence') or 'New'
        return rec


class HotelTransport(models.Model):
    _name = 'hotel.transport'
    _description = 'Hotel Transport details'
    _rec_name = 'transport_type'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    transport_type = fields.Selection([('Pickup', 'Pickup'), ('Drop', 'Drop')], string=' Transport Type', required=True)
    stage = fields.Selection([('pending', 'Pending'), ('complete', 'Complete'), ('cancel', 'Cancel')],
                             default="pending")
    location = fields.Char('Location Name', required=True)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street-2')
    city = fields.Char(string='City', required=True)
    time = fields.Datetime('Time', required=True)
    charges = fields.Monetary(related='transport_mode_id.charges', string='Charge', required=True)
    driver_id = fields.Many2one('res.partner', 'Driver', domain=[('is_driver', '=', True)], required=True)
    transport_mode_id = fields.Many2one('vehicle.type', 'Vehicle', required=True)
    km = fields.Integer(string='Total KM', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_charges = fields.Monetary('Charge ', compute='total_charges_transport')
    booking_id = fields.Many2one('hotel.booking', required=True)
    customer_id = fields.Many2one(related='booking_id.customer_id', string='Customer')
    transport_number = fields.Char(string='', copy=False, readonly=True,
                                   default=lambda self: 'New')

    @api.model
    def create(self, vals):
        rec = super(HotelTransport, self).create(vals)
        if vals.get('transport_number', 'New') == 'New':
            rec['transport_number'] = self.env['ir.sequence'].next_by_code('rest.transport.booking') or 'New'
        return rec

    @api.depends('total_charges', 'charges')
    def total_charges_transport(self):
        for rec in self:
            rec.total_charges = rec.charges * rec.km

    def action_complete(self):
        self.stage = "complete"

    def action_cancel(self):
        self.stage = "cancel"
