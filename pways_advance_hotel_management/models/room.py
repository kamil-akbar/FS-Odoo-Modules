from odoo import models, fields, api
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta, date , datetime, time
from dateutil.relativedelta import relativedelta
import calendar
from odoo.http import request
import dateutil.parser


class HotelFloor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"
    _order = 'id desc'

    name = fields.Char('Floor Number', required=True, index=True)
    floor_number_sequence = fields.Char(string='', copy=False, readonly=True, default=lambda self: 'New')
    capacity = fields.Integer(string='Rooms', compute='get_capacity_room_count')
    responsible_id = fields.Many2one('hr.employee', string='Responsible')

    def get_capacity_room_count(self):
        count = self.env['hotel.room'].search_count([('floor_id', '=', self.id)])
        self.capacity = count

    def total_capacity_rooms_views(self):
        return {
            'name': 'Rooms',
            'domain': [('floor_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'hotel.room',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': "ir.actions.act_window"
        }

    @api.model
    def create(self, vals):
        rec = super(HotelFloor, self).create(vals)
        if vals.get('floor_number_sequence', 'New') == 'New':
            rec['floor_number_sequence'] = self.env['ir.sequence'].next_by_code('rest.floor.sequence') or 'New'
        return rec


class HotelRoomType(models.Model):
    _name = "hotel.room.type"
    _description = "Hotel Room Type"
    _order = 'id desc'

    name = fields.Char('Room Type', required=True)


class HotelRoomCategory(models.Model):
    _name = "hotel.room.category"
    _description = "Hotel Room Category"
    _order = 'id desc'

    name = fields.Char('Room Category', required=True)
    room_facilities_ids = fields.Many2many('hotel.room.facilities', string='Facilities')
    image = fields.Binary(string="Room Image")
    category_ids = fields.One2many('hotel.room', 'room_category_id', string="Rooms")
    price = fields.Integer(string="Charge/ Day", required=True)
    adults = fields.Integer(string="Adults", required=True)
    child = fields.Integer(string="Child", required=True)
    description= fields.Char(string="Description")
    product_cate_id = fields.One2many('product.template','room_category')

    @api.model
    def create(self, vals):
        rec = super(HotelRoomCategory, self).create(vals)
        product = self.env['product.template'].sudo().search([('name', '=', rec.name)])
        product_category = self.env['product.public.category'].sudo().search([('name','=', rec.name)])
        if not product_category:
            product_category = self.env['product.public.category'].sudo().create({
                'name': vals['name']
                })
        if not product:
            product = self.env['product.template'].sudo().create({
                'name':  vals['name'],
                'list_price': vals['price'],
                'adults' : vals['adults'],
                'child' : vals['child'],
                'website_published' : True,
                'room' : True,
                'room_category' : rec.id,
                'public_categ_ids' : product_category,
            })
        return rec



class HotelRoomFacilities(models.Model):
    _name = "hotel.room.facilities"
    _description = "Facilities"
    _order = 'id desc'

    avatar = fields.Binary()
    name = fields.Char('Facilities Name', required=True)
    room_fac_ids = fields.Many2many('hotel.room', string='Rooms')
    room_category_ids = fields.Many2many('hotel.room.category', string='Room Categories')

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    checkin_date = fields.Datetime(string='Check-in Date', store=True)
    checkout_date = fields.Datetime(string='Check-out Date', store=True)
    number_of_days = fields.Integer(string='Number of Days', compute='_compute_number_of_days', store=True)

    @api.depends('checkin_date', 'checkout_date')
    def _compute_number_of_days(self):
        for line in self:
            if line.checkin_date and line.checkout_date:
                if line.checkin_date <= line.checkout_date:
                    delta = line.checkout_date.date() - line.checkin_date.date()
                    line.number_of_days = delta.days
                else:
                    line.number_of_days = 0
            else:
                line.number_of_days = 0



class HotelProductFac(models.Model):
    _inherit = 'product.template'

    hall_id = fields.Many2one('hotel.hall')
    room_ids = fields.One2many('hotel.room', 'product_room_id')
    room_capacity = fields.Integer(string="Room Capacity")
    adults = fields.Integer(string="Adults")
    child = fields.Integer(string="Child")
    room_category = fields.Many2one('hotel.room.category')
    room_facilities_ids = fields.Many2many(related='room_category.room_facilities_ids')
    room = fields.Boolean(string="Is_room")
    hall = fields.Boolean(string="Is_hall")
    hall_capacity = fields.Integer(string="Hall Capacity")
    hall_facilities_ids = fields.Many2many(related='hall_id.hall_facilities_ids')
    room_desc = fields.Char(string="Room Description")
    available_room = fields.Integer(string="Room Available")
    current_available_room = fields.Integer(string="Current Available Room")

    def _filter_on_available_products(self, from_date, to_date, search_result):
        my_time = datetime.min.time()
        my_max_time = datetime.max.time()

        start_date = dateutil.parser.parse(from_date)
        end_date = dateutil.parser.parse(to_date)

        start_date_date = start_date.date()
        end_date_date = end_date.date()

        start_datetime = datetime.combine(start_date_date, my_time)
        end_datetime = datetime.combine(end_date_date, my_max_time)

        domain = ['|', '|', '&', ('check_in', '>=', start_datetime), ('check_in', '<=', end_datetime),
                  '&', ('check_out', '>=', start_datetime), ('check_out', '<=', end_datetime),
                  '&', ('check_in', '<=', start_datetime), ('check_out', '>=', end_datetime)]
        hall_booking = request.env['hotel.feast'].sudo().search(domain)
        all_halls = request.env['hotel.hall'].sudo().search([ ])
        hall = hall_booking.mapped('hall_id')
        free_halls = all_halls - hall
        available_product = free_halls.mapped('product_id')
        search_available_product = available_product.filtered(lambda x: x in search_result)
        return search_available_prodct



    def _filter_on_available_room(self, from_date, to_date, search_result):
        fil_room_ids = request.env['hotel.room']
        from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        from_date_with_time = datetime.combine(from_date, time(13, 0))
        domain = ['|', '|', '&', ('check_in', '>=', from_date_with_time), ('check_in', '<=', to_date),
              '&', ('check_out', '>=', from_date_with_time), ('check_out', '<=', to_date),
              '&', ('check_in', '<=', from_date_with_time), ('check_out', '>=', to_date)]
        room_detail_ids = request.env['hotel.room.details'].sudo().search(domain)
        fil_room_ids = room_detail_ids.mapped('room_id')
        all_rooms = request.env['hotel.room'].sudo().search([])
        free_room = all_rooms - fil_room_ids
        room_products = free_room.mapped('product_room_id')
        for product in room_products:
            product_rooms = free_room.filtered(lambda r: r.product_room_id == product)
            product_current_available_room = len(product_rooms)
            category_id = product_rooms.product_room_id
            category_id.write({'current_available_room': product_current_available_room})
        booked_rooms = fil_room_ids.mapped('product_room_id')
        non_booked_rooms = booked_rooms- room_products
        non_booked_rooms.write({'current_available_room': 0})
        search_available_product = room_products.filtered(lambda x: x in search_result)
        return search_available_product



class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _rec_name = 'room_no'
    _order = 'id desc'

    avatar = fields.Binary()
    room_no = fields.Char(string='Room No.', required=True)
    floor_id = fields.Many2one('hotel.floor', string='Floor', required=True)
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type')
    room_category_id = fields.Many2one('hotel.room.category', string='Room Category', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    price = fields.Monetary(string='Price', required=True)
    room_facilities_ids = fields.Many2many('hotel.room.facilities','room_fac_ids', string='Facilities')
    check_in = fields.Datetime(string='Check-In Date', default=fields.Datetime.now, )
    check_out = fields.Datetime(string='Check-Out Date', default=fields.Datetime.now, )
    capacity = fields.Integer(string='Capacity', required=True)
    hotel_room_details_id = fields.Many2one('hotel.room.details')
    hotel_room_details_ids = fields.One2many('hotel.room.details', 'room_id')
    stages = fields.Selection([('Available', "Available"), ('Booked', "Booked")],string="Stage", default='Available')
    is_booked = fields.Boolean(compute="compute_is_booked")
    adults = fields.Integer(string="Adults")
    child = fields.Integer(string="Child")
    description = fields.Char(string="Room Description")
    product_room_id = fields.Many2one('product.template', string="Room Product")
    hotel_rest_id = fields.One2many('hotel.restaurant','room_id')

    def compute_is_booked(self):
        current_datetime = fields.Datetime.now()
        available_id = self.env['room.available.wizard']
        if self.env.context.get('active_id'):
            available_id = self.env['room.available.wizard'].browse(self.env.context.get('active_id'))
        for rec in self:
            domain = ['|', '|', '&', ('check_in', '>=', available_id.start_date), ('check_in', '<=', available_id.end_date),
                              '&', ('check_out', '>=', available_id.start_date), ('check_out', '<=', available_id.end_date),
                              '&', ('check_in', '<=', available_id.start_date), ('check_out', '>=', available_id.end_date)]
            room_booking = request.env['hotel.room.details'].sudo().search(domain)
            fil_room_details = room_booking.mapped('room_id')
            all_rooms = request.env['hotel.room'].sudo().search([])
            room = room_booking.mapped('room_id')
            free_room = all_rooms - room
            for rec in all_rooms:
                if rec in room:
                    rec.is_booked = True
                else:
                    rec.is_booked = False

    
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s' % (rec.room_no, rec.room_type_id.name)))
        return result


class HotelRoomBookingDetails(models.Model):
    _name = 'hotel.room.details'
    _description = 'Hotel Room Detail'
    _rec_name = 'room_id'
    _inherit = ["mail.thread", "mail.activity.mixin" ]
    _order = 'id desc'

    @api.model
    def _read_group_room_ids(self, room_ids, domain, order):
        all_rental_rooms = room_ids.search([], order=order)
        if len(all_rental_rooms) > 80:
            return room_ids
        return all_rental_rooms

    room_sequence = fields.Char(string='', copy=False, readonly=True,
                                default=lambda self: 'New')
    room_id = fields.Many2one('hotel.room', string='Room', group_expand="_read_group_room_ids")
    check_in = fields.Datetime(string='Check-In Date', required=True, tracking=True)
    check_out = fields.Datetime(string='Check-Out Date', required=True, tracking=True)
    days = fields.Integer(compute='day_compute_hours', string='Number of Days')
    booking_id = fields.Many2one('hotel.booking')
    room_status_id = fields.Many2one('room.status')
    total_price = fields.Monetary(string='Total Charges', compute="compute_total_price")
    room_facilities = fields.Many2many(related='room_id.room_facilities_ids' ,string="Room Facilities")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    price = fields.Monetary(string='Charge', related='room_id.price', required=True)
    capacity = fields.Integer(string='Capacity', related='room_id.capacity', required=True)
    customer_id = fields.Many2one(related='booking_id.customer_id')
    feast_id = fields.Many2one('hotel.feast')
    stages = fields.Selection(
        [('Available', "Available"), ('Booked', "Booked"), ('Maintenance', 'Maintenance')],
        string="Stage", default='Available')
    is_invoice_created = fields.Boolean()


    @api.model
    def create(self, vals):
        rec = super(HotelRoomBookingDetails, self).create(vals)
        if vals.get('room_sequence', 'New') == 'New':
            rec['room_sequence'] = self.env['ir.sequence'].next_by_code('rest.room.sequence') or 'New'
        return rec

    @api.onchange('check_in', 'check_out', 'room_id')
    def _grt_room_id(self):
        for rec in self:
            room_ids = self.env['hotel.room.details'].sudo().search([('check_in', '<=', rec.check_out),
                                                                     ('check_out', '>=', rec.check_in)]).mapped('room_id').ids
            return {'domain': {'room_id': [('id', 'not in', room_ids)]}}

    
    def available_to_booked(self):
        self.stages = 'Booked'

    def booked_to_maintenance(self):
        room_status_id =  self.env['room.status'].search([('room_status', '=', 'maintenance')])
        self.write({'stages':'Maintenance', 'room_status_id': room_status_id and room_status_id.id})

    def maintenance_to_available(self):
        self.stages = 'Available'

    @api.depends('check_out', 'check_in')
    def day_compute_hours(self):
        for rec in self:
            if rec.check_out and rec.check_in:
                check_out = rec.check_out.date() 
                check_in = rec.check_in.date()   
                days = (check_out - check_in).days
                
                days_int = max(0, days) 
                rec.days = days_int
            else:
                rec.days = 0

    @api.depends('days', 'price' ,'room_id', 'check_out', 'check_in' )
    def compute_total_price(self):
        for rec in self:
            rec.total_price = rec.days * rec.price

    @api.model
    def hotel_room_night_invoice(self):
        today_date = fields.Date.today()
        for rec in self.env['hotel.booking.details'].search(
                [('stages', '=', 'Booked')]):
            if rec.booking_id.stages == "check_in":
                if rec.booking_id.invoice_payment_type == "by_night":
                    amount = rec.total_price / rec.days
                    if rec.check_in.date() < today_date < rec.check_out.date():
                        data = {
                            'product_id': self.env.ref('pways_advance_hotel_management.hotel_invoice').id,
                            'name': 'Night Invoice' + " of Room No : " + rec.room_id.room_no,
                            'quantity': 1,
                            'price_unit': amount,
                        }
                        invoice_lines = [(0, 0, data)]
                        record = {
                            'partner_id': rec.booking_id.customer_id.id,
                            'invoice_date': fields.Date.today(),
                            'invoice_line_ids': invoice_lines,
                            'move_type': 'out_invoice',
                        }
                        invoice_id = self.env['account.move'].create(record)
                        booking_data = {
                            'room_id': rec.room_id.id,
                            'date': fields.Date.today(),
                            'amount': amount,
                            'invoice_id': invoice_id.id,
                            'booking_id': rec.booking_id.id
                        }
                        self.env['room.night.invoice'].create(booking_data)
                        rec.is_invoice_created = True


class RoomNightInvoice(models.Model):
    _name = 'room.night.invoice'
    _description = "Room Night Invoice"
    _order = 'id desc'

    room_id = fields.Many2one('hotel.room', string="Room")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(string="Amount")
    date = fields.Date(string="Date")
    booking_id = fields.Many2one('hotel.booking', string="Booking")
    payment_state = fields.Selection(related='invoice_id.payment_state', string="Payment State")
    invoice_due = fields.Monetary(related='invoice_id.amount_residual', string="Due")


class RoomStatus(models.Model):
    _name = 'room.status'
    _description = "Room Status"
    _order = 'id desc'

    name = fields.Char()
    room_status = fields.Selection([('check_in', 'Check In'), ('check_out', 'Check Out'), ('maintenance', 'Maintenance'), ('none', 'None')],string='Check Status', store=True)

