# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date


class HotelHall(models.Model):
    _name = 'hotel.hall'
    _description = 'Hotel hall'
    _rec_name = 'hall_no'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    avatar = fields.Binary()
    hall_no = fields.Char(string='Hall No.', required=True)
    floor_id = fields.Many2one('hotel.floor', string='Floor', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    price = fields.Monetary(string='Price', required=True)
    hall_facilities_ids = fields.Many2many('hotel.room.facilities', string='Facilities')
    capacity = fields.Integer(string='Capacity', required=True)
    product_id = fields.One2many('product.template', 'hall_id')



class HotelFeast(models.Model):
    _name = "hotel.feast"
    _description = "Hotel Hall Booking"
    _rec_name = 'booking_number'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    booking_number = fields.Char(string='', copy=False, readonly=True, default=lambda self: 'New')
    booking = fields.Boolean("Hotel Guest")
    booking_id = fields.Many2one("hotel.booking", "Booking No")
    customer_id = fields.Many2one('res.partner', string='Customer', required=1)
    responsible = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsible', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    stages = fields.Selection([('Draft', 'Draft'), ('Confirm', 'Confirm'),
                               ('Complete', 'Complete'), ('Cancel', 'Cancel')], string='Stages ', default='Draft',copy=False,)
    total_all_amount = fields.Monetary(string='Total Charges', compute="_compute_total_amount")
    cancellation_charge = fields.Monetary(string='Cancels Charges')
    cancels_invoice_id = fields.Many2one('account.move', string="Invoice ", readonly=True)
    cancellation_reason = fields.Text(string="Cancellation Reason")
    is_cancellation_charge = fields.Boolean(string="Cancellation Charge")
    start_date = fields.Datetime(string="Event Start")
    end_date = fields.Datetime(string="Event End")

    # Hall Details
    hall_id = fields.Many2one('hotel.hall', string="Hall")
    floor_id = fields.Many2one(related="hall_id.floor_id", string='Location')
    price = fields.Monetary(string='Price / Hour', related="hall_id.price", store=True)
    capacity = fields.Integer(related="hall_id.capacity", string="Capacity")
    hours = fields.Float(string="Total Hours", compute="_compute_no_of_days", store=True)

    # Deposit Amount
    is_deposit = fields.Boolean(string='Any Deposit')
    deposit_amount = fields.Monetary(string='Deposit Amount')
    feast_invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True)
    journal_id = fields.Many2one('account.journal', string="Journal", domain="[('type','in',['bank','cash'])]")
    payment_state = fields.Selection(related="feast_invoice_id.payment_state")



    @api.onchange('booking_id')
    def onchange_customer_id(self):
        if self.booking_id:
            self.customer_id = self.booking_id.customer_id

            
    def feast_invoice(self):
        self.stages = 'Complete'
        hall_booking = self.env['hotel.hall.booking'].search([('hall_id', '=', self.hall_id.id)])
        hall_booking.stage = "a"
        data = {
            'housekeeping_type': 'Cleaning',
            'hall_id': self.hall_id.id,
            'desc': "New House Keeping request for Hall",
            'start_datetime': self.end_date
        }
        self.env['hotel.housekeeping'].create(data)
        if self.is_deposit:
            deposit = {
                'payment_type': 'inbound',
                'partner_id': self.customer_id.id,
                'amount': self.deposit_amount,
                'journal_id': self.journal_id.id
            }
            payment_id = self.env['account.payment'].create(deposit)
            payment_id.action_post()

        product_id = self.env.ref('pways_advance_hotel_management.hotel_feast_charges')
        data = {
            'product_id': product_id.id,
            'name': 'Hall Booking',
            'quantity': 1,
            'price_unit': self.total_all_amount,
            'tax_ids': [(4, x) for x in product_id.taxes_id.ids],
        }
        invoice_line = [(0, 0, data)]
        record = {
            'partner_id': self.customer_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line,
            'move_type': 'out_invoice'
        }

        feast_invoice_id = self.env['account.move'].sudo().create(record)
        self.feast_invoice_id = feast_invoice_id.id


    def draft_to_confirm(self):
        if self.hall_id:
            self.stages = 'Confirm'
            data = {
                'hall_id': self.hall_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'stage': 'b'
            }
        booking_id = self.booking_id
        if booking_id:
            l_data = {
                'service': "Benquet Charges",
                'quantity': 1,
                'amount': self.total_all_amount,
                'booking_id': self.booking_id.id,
                'hall_id': self.id,
            }
            booking_id = self.env['hotel.extra.services'].sudo().create(l_data)
        hall_booking = self.env['hotel.hall.booking'].create(data)

    def confirm_to_cancel(self):
        self.stages = 'Cancel'
        hall_booking = self.env['hotel.hall.booking'].search([('hall_id', '=', self.hall_id.id)])
        hall_booking.stage = "a"

    @api.depends('start_date', 'end_date')
    def _compute_no_of_days(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                duration = rec.end_date - rec.start_date
                duration_in_s = duration.total_seconds()
                hours = duration_in_s / 3600
                if hours >= 1:
                    rec.hours = hours
                else:
                    rec.hours = 0.0

    @api.depends('hours', 'price')
    def _compute_total_amount(self):
        for rec in self:
            if rec.hours and rec.price:
                rec.total_all_amount = rec.hours * rec.price
            else:
                rec.total_all_amount = 0.0

    @api.model
    def create(self, vals):
        rec = super(HotelFeast, self).create(vals)
        if vals.get('booking_number', 'New') == 'New':
            rec['booking_number'] = self.env['ir.sequence'].next_by_code(
                'rest.feast.booking') or 'New'
        return rec

    @api.onchange('start_date', 'end_date', 'hall_id')
    def _get_available_hall(self):
        for rec in self:
            hall_ids = self.env['hotel.hall.booking'].sudo().search([('start_date', '<=', rec.end_date),
                                                                     ('end_date', '>=', rec.start_date),
                                                                     ('stage', '!=', 'a')]).mapped('hall_id').ids
            return {'domain': {'hall_id': [('id', 'not in', hall_ids)]}}


class HotelHallBooking(models.Model):
    _name = "hotel.hall.booking"
    _description = "Hotel Hall Booking"
    _rec_name = "hall_id"

    hall_id = fields.Many2one('hotel.hall', string="Hall")
    stage = fields.Selection([('a', 'Available'), ('b', 'Booked'), ('m', 'Maintenance')], string="Stage")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
