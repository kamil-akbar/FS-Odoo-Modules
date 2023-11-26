# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError, AccessError, UserError


class HotelRestaurant(models.Model):
    _name = "hotel.restaurant"
    _description = "Reservation Details"
    _rec_name = 'reservation_number'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    reservation_number = fields.Char(string='', copy=False, readonly=True,
                                     default=lambda self: 'New')
    is_table_booking = fields.Boolean(string='Table Reservation')
    room_id = fields.Many2one('hotel.room', string='Room')
    booking_id = fields.Many2one('hotel.booking')
    customer_id = fields.Many2one(related='booking_id.customer_id', string='Customer')
    customer_foods_ids = fields.One2many('customer.food.order', 'restaurant_id')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_charges = fields.Monetary(string='Total Price', compute='restaurant_food_charges')
    stages = fields.Selection(
        [('Confirm', 'Confirm'), ('Delivered', 'Delivered')],
        string='Stages ', default='Confirm')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    feast_id = fields.Many2one('hotel.feast')
    # Table Details
    table_id = fields.Many2one('table.details', string="Table")
    table_stages = fields.Selection(related="table_id.stages")
    table_capacity = fields.Integer(related="table_id.capacity", string="Capacity")
    no_of_person = fields.Integer(string="No of People")
    res_start = fields.Datetime(string="Reservation Start")
    res_end = fields.Datetime(string="Reservation End")
    table_charges = fields.Monetary(string="Reservation Charges")
    kot = fields.Boolean(string="KOT" ,readonly=True)


    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        if self.booking_id:
            booked_room_ids = self.booking_id.room_ids.mapped('room_id').ids
            domain = [('id', 'in', booked_room_ids)]
            return {'domain': {'room_id': domain}}

            
    @api.depends('customer_foods_ids', )
    def restaurant_food_charges(self):
        for rec in self:
            total_charges = 0.0
            for data in rec.customer_foods_ids:
                total_charges = total_charges + data.subtotal_amount
            if rec.is_table_booking:
                total_charges = total_charges + rec.table_charges
            rec.total_charges = total_charges

    def confirm_to_delivered(self):
        self.stages = 'Delivered'

    def write(self, vals):
        if any(stages == 'Delivered' for stages in set(self.mapped('stages'))):
            raise UserError(_("Order delivered, edit order not allowed."))
        else:
            return super().write(vals)

    @api.model
    def create(self, vals):
        rec = super(HotelRestaurant, self).create(vals)
        if vals.get('reservation_number', 'New') == 'New':
            rec['reservation_number'] = self.env['ir.sequence'].next_by_code('rest.restaurant.sequence') or 'New'
        return rec

    # @api.onchange('room_id')
    # def _onchange_room_id(self):
    #     id = self._context.get('booking_id')
    #     room_ids = self.env['hotel.room.details'].sudo().search([('booking_id', '=', id)]).mapped('room_id').mapped(
    #         'id')
    #     return {'domain': {'room_id': [('id', 'in', room_ids)]}}

    @api.onchange('res_start', 'res_end', 'table_id')
    def _get_available_table(self):
        for rec in self:
            table_ids = self.env['hotel.table.booking'].sudo().search([('start_date', '<=', rec.res_end),
                                                                       ('end_date', '>=', rec.res_start),
                                                                       ('stage', '!=', 'a')]).mapped('table_id').ids
            return {'domain': {'table_id': [('id', 'not in', table_ids)]}}

    def action_book_table(self):
        data = {
            'table_id': self.table_id.id,
            'start_date': self.res_start,
            'end_date': self.res_end,
            'stage': 'b'
        }
        table_booking = self.env['hotel.table.booking'].create(data)
        table_booking.table_id.stages = "Booked"

    def action_free_table(self):
        table_booking = self.env['hotel.table.booking'].search([('table_id', '=', self.table_id.id)])
        table_booking.stage = "a"
        table_booking.table_id.stages = "Available"

    def action_create_kot(self):
        lines = []
        if self.kot == False:
            for line in self.customer_foods_ids:
                if line.kot == False:
                    vals= [ 0, 0, {
                    'menucard_id': line.food_id.id,
                    'item_qty': line.quantity
                    }]
                    lines.append(vals)
                booking_values = {
                    'order_number': self.booking_id.booking_number,
                    'room_no': self.room_id.room_no,
                    'kot_date': self.create_date,
                    'kot_list_ids': lines,
                    'kot': True
                }
                self.write({'kot': True})
        booking_id = self.env['hotel.restaurant.kitchen.order.tickets'].sudo().create(booking_values)

class RestaurantFoodCategory(models.Model):
    _name = 'food.category'
    _description = "Food Category Details"
    _order = 'id desc'

    name = fields.Char('Food Category', required=True)


class RestaurantFood(models.Model):
    _name = 'food.item'
    _description = "Food Details"
    _order = 'id desc'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product','Food', required=True)
    food_category = fields.Many2one('food.category', required=True)
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    price = fields.Monetary(string='Price')
    food_sequence = fields.Char(string='', copy=False, readonly=True,
                                default=lambda self: 'New')

    @api.model
    def create(self, vals):
        rec = super(RestaurantFood, self).create(vals)
        if vals.get('food_sequence', 'New') == 'New':
            rec['food_sequence'] = self.env['ir.sequence'].next_by_code('rest.food.sequence') or 'New'
        return rec


class RestaurantOrder(models.Model):
    _name = 'customer.food.order'
    _description = "Customer Food Order Details"
    _rec_name = 'food_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    food_id = fields.Many2one('food.item', required=True)
    quantity = fields.Integer(string='Quantity', required=True, default=1)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    price = fields.Monetary(string='Price', related='food_id.price', required=True)
    restaurant_id = fields.Many2one('hotel.restaurant')
    subtotal_amount = fields.Monetary(string='Subtotal', compute='food_order_total_amount')
    booking_id = fields.Many2one(related='restaurant_id.booking_id')
    customer_id = fields.Many2one(related='restaurant_id.booking_id.customer_id', string='Customer')
    stages = fields.Selection(
        [('Confirm', 'Confirm'), ('Prepared', 'Prepared'), ('Delivered', 'Delivered')],
        string='Stages', default='Confirm')
    food_included = fields.Boolean(string="Food Included")
    kot = fields.Boolean(string='Kot' , readonly=True)


    def confirm_to_prepared(self):
        self.stages = 'Prepared'

    def prepared_to_delivered(self):
        self.stages = 'Delivered'

    @api.depends('quantity', 'food_id')
    def food_order_total_amount(self):
        for rec in self:
            subtotal_amount = 0.0
            if not rec.food_included:
                subtotal_amount = subtotal_amount + (rec.price * rec.quantity)
                rec.subtotal_amount = subtotal_amount
            else:
                rec.subtotal_amount = subtotal_amount


class RestaurantTableDetail(models.Model):
    _name = 'table.details'
    _description = "Table Details"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    name = fields.Char('Table Number ', required=True)
    capacity = fields.Integer(string='Capacity', required=True)
    stages = fields.Selection(
        [('Available', "Available"), ('Booked', "Booked")],
        string='Stages', default='Available')
    table_number = fields.Char(string='', copy=False, readonly=True,
                               default=lambda self: 'New')

    @api.model
    def create(self, vals):
        rec = super(RestaurantTableDetail, self).create(vals)
        if vals.get('table_number', 'New') == 'New':
            rec['table_number'] = self.env['ir.sequence'].next_by_code('rest.table.sequence') or 'New'
        return rec

    def available_to_booked(self):
        self.stages = 'Booked'

    def booked_to_available(self):
        self.stages = 'Available'


class HotelTableBooking(models.Model):
    _name = "hotel.table.booking"
    _description = "Hotel Table Booking"
    _rec_name = "table_id"
    _order = 'id desc'

    table_id = fields.Many2one('table.details', string="Hall")
    stage = fields.Selection([('a', 'Available'), ('b', 'Booked')], string="Stage", default="a")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
