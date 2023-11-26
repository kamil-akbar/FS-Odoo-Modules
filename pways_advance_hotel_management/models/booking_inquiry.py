from odoo import fields, models, api
from datetime import datetime, timedelta

class AccountPayment(models.Model):
    _inherit = "account.payment"

    inquiry_id  = fields.Many2one('booking.inquiry')


class BookingInquiry(models.Model):
    _name = 'booking.inquiry'
    _description = "Booking Inquiry"
    _inherit = 'mail.thread'
    _order = 'id desc'

    booking_number = fields.Char(string="Booking Number",readonly=True)
    partner_id = fields.Many2one("res.partner", "Customer")
    name = fields.Char(string="Inquiry's Names")
    phone = fields.Char(string="Inquiry's Phone")
    email = fields.Char(string="Inquiry's email")
    inquiry_for = fields.Selection([('hall', 'Hall'), ('restaurant','Restaurant'),('room','Room')],string="Inquiry For")
    arrival_date = fields.Datetime(string="Arrival Date")
    departure_date = fields.Datetime(string="Departure Date")
    child = fields.Integer(string="Child")
    number_rooms = fields.Integer(string="Number Of Room")
    company_id= fields.Many2one('res.company')
    person = fields.Integer(string="Number Of People")
    booking_time = fields.Char(string="Booking Time")
    room_type = fields.Char(string="Type")
    hall_type = fields.Char( string='Hall Capacity')
    payment_ids = fields.One2many('account.payment', 'inquiry_id')
    booking_count = fields.Integer(string="Room Booking Count", compute="count_of_booking")
    hall_count = fields.Integer(string="Hall Booking Count", compute="count_of_hall")
    rest_count = fields.Integer(string="Restaurtant Booking Count", compute="count_of_rest")
    info = fields.Text(string="Other Info")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('booking', 'Booking'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft',)
    is_laundry = fields.Boolean(string="Laundry")
    is_food_included = fields.Boolean(string="Food")
    is_transport_included = fields.Boolean(string="Transport")
    user = fields.Many2one('res.users', default=lambda self: self.env.user, string='user')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')

    @api.model
    def create(self, vals):
        vals['booking_number'] = self.env['ir.sequence'].next_by_code('booking.inquiry.seq') or 'New'
        return super(BookingInquiry, self).create(vals)

    def button_view_booking(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pways_advance_hotel_management.hotel_booking_action")
        action['domain'] = [('phone', '=', self.phone)]
        return action

    def button_hall_booking(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pways_advance_hotel_management.hotel_feast_action")
        action['domain'] = [('customer_id.name', '=', self.name)]
        return action

    def button_rest_booking(self):
        action = self.env["ir.actions.actions"]._for_xml_id("pways_advance_hotel_management.open_view_hotel_restaurant_reservation_form_tree")
        action['domain'] = [('customer_id.name', '=', self.name)]
        return action


    def count_of_booking(self):
        count = self.env['hotel.booking'].search_count([('phone', '=', self.phone)])
        self.booking_count = count

    def count_of_hall(self):
        count = self.env['hotel.feast'].search_count([('customer_id.name', '=', self.name)])
        self.hall_count = count

    def count_of_rest(self):
        count = self.env['hotel.restaurant.reservation'].search_count([('customer_id.name', '=', self.name)])
        self.rest_count = count

    def action_confirm(self):
        self.state = 'confirm'
        template_id = self.env.ref('pways_advance_hotel_management.email_template_confirmation')
        template_id.send_mail(self.id, force_send=True)
        return True
    
    def booking(self):
        if self.inquiry_for == 'restaurant':

            partner_find = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
            if not partner_find:
                partner_find = self.env['res.partner'].sudo().create({
                    'name' : self.name,
                    'email' : self.email,
                    'phone' : self.phone,
                    })
                self.partner_id = partner_find.id
            restaurant = self.env['hotel.restaurant.reservation'].sudo().create({
                'customer_id' :  partner_find.id,
                'start_date' : self.arrival_date,
                'end_date' : self.departure_date,
                })
            self.state = 'booking'
            
        if self.inquiry_for == 'hall':
            
            partner_find = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
            if not partner_find:
                partner_find = self.env['res.partner'].sudo().create({
                    'name' : self.name,
                    'email' : self.email,
                    'phone' : self.phone,
                    })
                self.partner_id = partner_find.id
            hall_cap_id = self.env['hotel.hall'].sudo().search([('capacity', '=' , self.hall_type)])
            hall = self.env['hotel.feast'].sudo().create({
                    'customer_id' : partner_find.id,
                    'start_date' : self.arrival_date,
                    'end_date' : self.departure_date,
                    'hall_id' : hall_cap_id.id,
                })
            self.state = 'booking'

        if self.inquiry_for == 'room':
            partner_find = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
            if not partner_find:
                partner_find = self.env['res.partner'].sudo().create({
                    'name' : self.name,
                    'email' : self.email,
                    'phone' : self.phone,
                    })
                self.partner_id = partner_find.id
            room = self.env['hotel.booking'].sudo().create({
                    'customer_id' : partner_find.id,
                    'phone' : self.phone,
                    'email' : self.email,
                    'adults' : self.person,
                    'children' : self.child,
                    'no_of_room' : self.number_rooms,
                    'room_ids' : [(0,0,{'check_in': self.arrival_date, 'check_out': self.departure_date})],
                })

           
            if self.payment_ids:
                total = sum (self.payment_ids.mapped("amount"))
                room.write({    'advance_amount': total, 
                                'is_advance': True,
                                'journal_id' : self.payment_ids.journal_id[0].id,
                            })

            self.state = 'booking'
    
    def action_cancel(self):
        self.state = 'cancel'
        template_id = self.env.ref('pways_advance_hotel_management.email_template_cancellation')
        template_id.send_mail(self.id, force_send=True)
        return True

    def action_open_form(self):
        self.ensure_one()
        lang = self.env.context.get('lang')
        template_id = self.env.ref('pways_advance_hotel_management.email_template_confirmation')
        ctx = {
            'default_model': 'booking.inquiry',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id if template_id else None,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }




