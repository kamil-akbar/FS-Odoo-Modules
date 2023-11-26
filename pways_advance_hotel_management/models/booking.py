
import calendar
import datetime
import pytz
from datetime import timedelta, datetime
from datetime import date
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo import fields, models, api, _ ,Command
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import SUPERUSER_ID

class AccountPayment(models.Model):
    _inherit = "account.payment"

    booking_id = fields.Many2one('hotel.booking')

class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = "Hotel Bookings"
    _rec_name = 'booking_number'
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _order = 'id desc'

    payment_ids = fields.One2many('account.payment', 'booking_id')
    booking_number = fields.Char(string='', copy=False, readonly=True,default=lambda self: 'New')
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    phone = fields.Char("Alternative Number")
    email = fields.Char("Alternative Email")
    adults = fields.Integer(string='Adults', required=True, default=1)
    children = fields.Integer(string='Children')
    responsible = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsible', required=True)
    no_of_room = fields.Integer(string='No of Rooms', compute='room_count')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    stages = fields.Selection(
        [('Draft', 'Draft'), ('Confirm', 'Confirm'), ('check_in', 'Check-in'), ('Complete', 'Check-out'),
         ('Cancel', 'Cancel')],
        string='Stages', default='Draft', copy=False)
    is_any_agent = fields.Boolean(string="Any Agent")
    agent_id = fields.Many2one('res.partner', domain="[('is_agent','=',True)]", string="Agent")
    agent_commission = fields.Monetary(string="Commission")
    agent_percentage_commission = fields.Monetary(string="Commission ", compute="_compute_percentage_commission")
    percentage = fields.Float(string="Percentage")
    agent_bill_id = fields.Many2one('account.move', string="Agent Bill")
    agent_commission_type = fields.Selection([('fix', 'Fix'), ('percentage', 'Percentage')], default="fix",
                                             string="Commission Type")
    agent_payment_state = fields.Selection(related="agent_bill_id.payment_state", string="Payment Status ")

    is_breakfast_included = fields.Boolean(string="Breakfast")
    breakfast_charge = fields.Monetary(string="Breakfast Charges")
    is_dinner_included = fields.Boolean(string="Dinner")
    dinner_charge = fields.Monetary(string="Dinner Charges")
    is_lunch_included = fields.Boolean(string="Lunch")
    lunch_charge = fields.Monetary(string="Lunch Charges")

    # Invoices
    room_total_charges = fields.Monetary(string='Room Charges', compute='room_charges')
    transport_total_charges = fields.Monetary(string='Transport Charges', compute='transport_charges')
    laundry_total_charges = fields.Monetary(string='Laundry Charges', compute='laundry_charges')
    restaurant_services_charges = fields.Monetary(string='Restaurant Charges', compute='restaurant_charges')
    all_service_amount = fields.Monetary(string='Amount Due', compute='total_service_amount')
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True)
    invoice_id = fields.Many2one('account.move', string="Invoice ")
    payment_state = fields.Selection(related='invoice_id.payment_state', string="Payment Status")
    invoice_due = fields.Monetary(related='invoice_id.amount_residual', string="Due", store=True)
    payable_due = fields.Monetary(string="Payable Due", compute="_compute_payable_due_charges")
    invoice_payment_type = fields.Selection([('once', 'Once'), ('by_night', 'Invoice Posted by Night')], default="once",
                                            string="Invoice Payment")
    room_night_invoice_ids = fields.One2many('room.night.invoice', 'booking_id')
    total_night_invoice = fields.Monetary(string="Room Charges Payable", compute="_compute_total_due_invoice")
    total_night_invoice_due = fields.Monetary(string="Room Charges Due", compute="_compute_total_due_invoice")

    is_advance = fields.Boolean(string='Advance')
    advance_amount = fields.Monetary(string='Advance Amount')
    journal_id = fields.Many2one('account.journal', string="Journal", domain="[('type','in',['bank','cash'])]")

    # One2Many
    room_id = fields.Many2one('hotel.room')
    benquet_booking = fields.Many2one('hotel.feast')
    service_ids = fields.One2many('hotel.extra.services', 'booking_id', string='Services')
    room_ids = fields.One2many('hotel.room.details', 'booking_id', string='Rooms')
    transport_ids = fields.One2many('hotel.transport', 'booking_id')
    laundry_ids = fields.One2many('laundry.service', 'booking_id')
    restaurant_ids = fields.One2many('hotel.restaurant', 'booking_id')
    proof_ids = fields.One2many('proof.details', 'booking_id', string='Proof Details')

    # Cancel Booking
    cancels_invoice_id = fields.Many2one(
        'account.move', string="Invoice", readonly=True)
    cancellation_reason = fields.Text(string="Cancellation Reason")
    cancellation_charge = fields.Monetary(string='Cancellation Charges')
    is_cancellation_charge = fields.Boolean(string="Cancellation Charge")
    room_name = fields.Char(string='Room', compute="show_room_details")
    room_amenities_ids = fields.Many2many("hotel.room.amenities", string="Room Amenities", help="List of room amenities.")
    price = fields.Monetary('Price', compute='_amenities_charges')
    service_line_ids = fields.One2many("hotel.service.line","booking_id", readonly=True)
    product_line_ids = fields.Many2many('hotel.beer.type' ,string="Bar Items")
    price_subtotal = fields.Monetary(string='Total Amount', compute='services_charges')

    def _compute_access_url(self):
        super()._compute_access_url()
        for order in self:
            order.access_url = f'/my/booking/{order.id}'


    def send_check_out_reminder_emails(self):
        company = self.env['res.company'].sudo().search([], limit=1)
        checkout_hour = company.notification_hour
        target_time_zone = company.user_ids[0].tz if company.user_ids and len(company.user_ids) > 0 else (self.env.user.tz or 'UTC')
        time_zone = pytz.timezone(target_time_zone)
        current_time = datetime.now()
        current_time_utc = current_time.astimezone(time_zone)
        Attachment = self.env['ir.attachment']
        manager_id = self.env['ir.model.data'].sudo()._xmlid_lookup('base.group_system')[2]
        group_manager = self.env['res.groups'].sudo().browse(manager_id)
        super_user = group_manager.users[0]
        if not group_manager.users:
            internal_user_id = self.env['ir.model.data'].sudo().get_object_reference('base', 'group_user')[1]
            group_internal_user = self.env['res.groups'].sudo().browse(internal_user_id)
            super_user = group_internal_user.users[0]

        rooms = self.env['hotel.room.details'].sudo().search([('stages', '=', 'Booked')])
        for room in rooms.filtered(lambda x: x.check_out):
            checkout_date = room.check_out
            cur_checkout_date = checkout_date.astimezone(time_zone)
            final_check_out = cur_checkout_date - timedelta(hours=checkout_hour)
            if final_check_out <= current_time_utc:
                template_id = self.env['ir.model.data']._xmlid_lookup('pways_advance_hotel_management.email_template_hotel_booking_check_out')[2]
                email_template_obj = self.env['mail.template'].sudo().browse(template_id)
                values = email_template_obj.generate_email(self.id, ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])

                values['attachment_ids'] = [Command.link(aid) for aid in values.get('attachment_ids', list())]
                attachment_ids = values.pop('attachment_ids', [])
                attachments = values.pop('attachments', [])

                values['email_from'] = super_user.partner_id.email
                email_to = ','.join(group_manager.mapped('users.partner_id.email')) + ',' + room.customer_id.email

                values['email_to'] = email_to                
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.create(values)
                for attachment in attachments:
                    attachment_data = {
                        'name': attachment[0],
                        'datas': attachment[1],
                        'type': 'binary',
                        'res_model': 'mail.message',
                        'res_id': msg_id.mail_message_id.id,
                    }
                    attachment_ids.append((4, Attachment.create(attachment_data).id))

                if attachment_ids:
                    msg_id.write({'attachment_ids': attachment_ids})

                if msg_id:
                    mail_mail_obj.send([msg_id])

        return True
   

    @api.depends('product_line_ids')
    def services_charges(self):
        for rec in self:
            price_subtotal = 0.0
            for data in rec.product_line_ids:
                price_subtotal = price_subtotal + data.price_subtotal
            rec.price_subtotal = price_subtotal
  
    @api.depends('room_amenities_ids', )
    def _amenities_charges(self):
        for rec in self:
            price = 0.0
            for data in rec.room_amenities_ids:
                price = price + data.price
            rec.price = price
    

    def open_booking_kanban(self):
        return {
            'type': 'ir.actions.act_window', 
            'res_model': 'hotel.booking', 
            'name': 'New HotelBooking', 
            'view_type': 'form', 
            'view_mode': 'form', 
            'view_id': False ,
            'target': 'new', 
        }

    @api.depends('room_ids')
    def show_room_details(self):
        for rec in self:
            if rec.room_ids:
                for data in rec.room_ids:
                    rec.room_name = data.room_id.room_no
            else:
                rec.room_name = False

    @api.model
    def create(self, vals):
        rec = super(HotelBooking, self).create(vals)
        if vals.get('booking_number', 'New') == 'New':
            rec['booking_number'] = self.env['ir.sequence'].next_by_code(
                'rest.room.booking') or 'New'
        return rec

    def action_draft_invoice(self):
        today_date = fields.Date.today()
        for rec in self.env['hotel.room.details'].sudo().search([('stages', '=', 'Booked')]):
            if rec.booking_id.stages == "check_in":
                amount = rec.total_price / rec.days
                if rec.check_in.date() == today_date < rec.check_out.date():
                    data = {
                        'product_id': self.env.ref('pways_advance_hotel_management.hotel_invoice').id,
                        'name': f'Night Invoice of Room No: {rec.room_id.room_no} Booking No: {rec.booking_id.booking_number}',
                        'quantity': 1,
                        'price_unit': amount,
                    }
                    invoice_lines = [(0, 0, data)]
                    record = {
                        'partner_id': rec.booking_id.customer_id.id,
                        'booking_id': rec.booking_id.id,
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


    # Stages
    def draft_to_confirm(self):
        Attachment = self.env['ir.attachment']
        manager_id = self.env['ir.model.data'].sudo()._xmlid_lookup('base.group_system')[2]
        group_manager = self.env['res.groups'].sudo().browse(manager_id)
        super_user = group_manager.users[0]
        if not group_manager.users:
            internal_user_id = self.env['ir.model.data'].sudo().get_object_reference('base', 'group_user')[1]
            group_internal_user = self.env['res.groups'].sudo().browse(internal_user_id)
            super_user = group_internal_user.users[0]

        if self.no_of_room > 0:
            for rec in self.room_ids:
                if not rec.room_id:
                    raise UserError(_('Please add room in room details'))
                ids = self.env['hotel.room.details'].sudo().search([('check_in', '<=', rec.check_out),
                                                                    ('check_out', '>=', rec.check_in),
                                                                    ('stages', '!=', 'Available')]).mapped('room_id').ids
                if rec.room_id.id in ids:
                    raise ValidationError("Some Rooms are booked choose another room to proceed")
                
                template_id = self.env['ir.model.data']._xmlid_lookup('pways_advance_hotel_management.email_template_hotel_booking')[2]
                email_template_obj = self.env['mail.template'].sudo().browse(template_id)
                values = email_template_obj.generate_email(self.id, ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])

                values['attachment_ids'] = [Command.link(aid) for aid in values.get('attachment_ids', list())]
                attachment_ids = values.pop('attachment_ids', [])
                attachments = values.pop('attachments', [])

                values['email_from'] = super_user.partner_id.email
                values['email_to'] = self.customer_id.email

                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.create(values)

                # manage attachments
                for attachment in attachments:
                    attachment_data = {
                        'name': attachment[0],
                        'datas': attachment[1],
                        'type': 'binary',
                        'res_model': 'mail.message',
                        'res_id': msg_id.mail_message_id.id,
                    }
                    attachment_ids.append((4, Attachment.create(attachment_data).id))

                if attachment_ids:
                    msg_id.write({'attachment_ids': attachment_ids})

                if msg_id:
                    mail_mail_obj.send([msg_id])

                if rec.booking_id == self:
                    rec.available_to_booked()

            if self.is_breakfast_included:
                b_data = {
                    'service': "Breakfast Charges",
                    'quantity': 1,
                    'amount': self.breakfast_charge,
                    'booking_id': self.id
                }
                self.env['hotel.extra.services'].create(b_data)

            if self.is_dinner_included:
                d_data = {
                    'service': "Dinner Charges",
                    'quantity': 1,
                    'amount': self.dinner_charge,
                    'booking_id': self.id
                }
                self.env['hotel.extra.services'].create(d_data)

            if self.is_lunch_included:
                l_data = {
                    'service': "Lunch Charges",
                    'quantity': 1,
                    'amount': self.lunch_charge,
                    'booking_id': self.id
                }
                self.env['hotel.extra.services'].create(l_data) 
            self.stages = 'Confirm'

        else:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': ('Add Rooms to Confirm Booking !'),
                    'sticky': False,
                }
            }
            return message

    def confirm_to_done(self):
        self.stages = 'Complete'
        for rec in self.room_ids:
            if rec.booking_id.id == self.id:
                rec.maintenance_to_available()
                data = {
                    'is_room': True,
                    'housekeeping_type': 'Cleaning',
                    'room_id': rec.room_id.id,
                    'desc': 'New Request for Housekeeping for Room',
                    'start_datetime': rec.check_out
                }
                self.env['hotel.housekeeping'].create(data)

    def confirm_to_cancel(self):
        Attachment = self.env['ir.attachment']
        manager_id = self.env['ir.model.data'].sudo()._xmlid_lookup('base.group_system')[2]
        group_manager = self.env['res.groups'].sudo().browse(manager_id)
        super_user = group_manager.users[0]

        if not group_manager.users:
            internal_user_id = self.env['ir.model.data'].sudo().get_object_reference('base', 'group_user')[1]
            group_internal_user = self.env['res.groups'].sudo().browse(internal_user_id)
            super_user = group_internal_user.users[0]

        for rec in self.room_ids:
            template_id = self.env['ir.model.data']._xmlid_lookup('pways_advance_hotel_management.email_template_hotel_booking_cancel')[2]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            values = email_template_obj.generate_email(self.id, ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
            values['attachment_ids'] = [Command.link(aid) for aid in values.get('attachment_ids', list())]
            attachment_ids = values.pop('attachment_ids', [])
            attachments = values.pop('attachments', [])
            values['email_from'] = super_user.partner_id.email
            values['email_to'] = rec.customer_id.email
            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.create(values)
            for attachment in attachments:
                attachment_data = {
                    'name': attachment[0],
                    'datas': attachment[1],
                    'type': 'binary',
                    'res_model': 'mail.message',
                    'res_id': msg_id.mail_message_id.id,
                }
                attachment_ids.append((4, Attachment.create(attachment_data).id))

            if attachment_ids:
                msg_id.write({'attachment_ids': attachment_ids})

            if msg_id:
                mail_mail_obj.send([msg_id])
            if rec.booking_id == self:
                rec.maintenance_to_available()

        self.stages = 'Cancel'

    def check_in_booking_status(self):
        booking_id = self.env['hotel.room.details'].sudo().search([('booking_id', '=', self.id)], limit=1)
        if booking_id:
            if self.stages == 'check_in':
                room_status_id =  self.env['room.status'].sudo().search([('room_status', '=', 'check_in')], limit=1)
                booking_id.room_status_id = room_status_id and room_status_id.id
            elif self.stages == 'Complete':
                room_status_id =  self.env['room.status'].sudo().search([('room_status', '=', 'check_out')], limit=1)
                booking_id.room_status_id = room_status_id and room_status_id.id
            else:
                room_status_id =  self.env['room.status'].sudo().search([('room_status', '=', 'none')], limit=1)
                booking_id.room_status_id = room_status_id and room_status_id.id

    def action_check_in(self):
        self.stages = "check_in"
        self.check_in_booking_status()
        for rooms in self.room_ids:
            room = self.env['hotel.room'].sudo().search([('room_no','=', rooms.room_id.room_no)])
            room.stages = 'Booked'
        

    def action_draft(self):
        self.stages = 'Draft'
        self.check_in_booking_status()

    def unlink(self):
        raise UserError("Please cancel this booking delete is not allowed")
        return super(Booking, self).unlink()

    # Compute Amount
    @api.depends('room_ids', 'is_breakfast_included', 'breakfast_charge', 'is_dinner_included', 'dinner_charge',
                 'is_lunch_included', 'lunch_charge', 'total_night_invoice', 'total_night_invoice_due')
    def room_charges(self):
        for rec in self:
            room_total_charges = 0.0
            if rec.invoice_payment_type == "by_night":
                rec.room_total_charges = rec.total_night_invoice
            else:
                for data in rec.room_ids:
                    room_total_charges = room_total_charges + data.total_price
                rec.room_total_charges = room_total_charges

    @api.depends('transport_ids')
    def transport_charges(self):
        for rec in self:
            transport_total_charges = 0.0
            for data in rec.transport_ids:
                if data.stage == "complete":
                    transport_total_charges = transport_total_charges + data.total_charges
            rec.transport_total_charges = transport_total_charges

    @api.depends('laundry_ids', )
    def laundry_charges(self):
        for rec in self:
            laundry_total_charges = 0.0
            for data in rec.laundry_ids:
                laundry_total_charges = laundry_total_charges + data.total_charges
            rec.laundry_total_charges = laundry_total_charges

    @api.depends('restaurant_ids')
    def restaurant_charges(self):
        for rec in self:
            restaurant_services_charges = 0.0
            for data in rec.restaurant_ids:
                restaurant_services_charges = restaurant_services_charges + data.total_charges
            rec.restaurant_services_charges = restaurant_services_charges

    @api.depends('service_ids')
    def total_service_amount(self):
        for rec in self:
            all_service_amount = 0.0
            for data in rec.service_ids:
                if data.hall_id and data.hall_id.feast_invoice_id:
                    all_service_amount = all_service_amount + 0
                else:
                    all_service_amount = all_service_amount + data.all_amount

            rec.all_service_amount = all_service_amount

    @api.depends('room_total_charges', 'transport_total_charges', 'laundry_total_charges','price','price_subtotal',
                 'restaurant_services_charges', 'all_service_amount', 'invoice_payment_type')
    def _compute_total_amount(self):
        
        for rec in self:
            total_amount = rec.room_total_charges + rec.transport_total_charges + rec.laundry_total_charges + rec.price +rec.price_subtotal+rec.restaurant_services_charges + rec.all_service_amount 
            rec.total_amount = total_amount 


    @api.depends('agent_commission_type', 'percentage', 'total_amount')
    def _compute_percentage_commission(self):
        for rec in self:
            if rec.agent_commission_type == "percentage":
                rec.agent_percentage_commission = (rec.percentage * rec.total_amount) / 100
            else:
                rec.agent_percentage_commission = 0.0

    @api.depends('room_night_invoice_ids', 'invoice_payment_type')
    def _compute_total_due_invoice(self):
        for rec in self:
            total = 0.0
            total_due = 0.0
            for data in rec.room_night_invoice_ids:
                total = total + data.amount
                total_due = total_due + data.invoice_due
            rec.total_night_invoice = total
            rec.total_night_invoice_due = total_due

    @api.depends('total_night_invoice_due', 'invoice_id', 'invoice_payment_type', 'invoice_due',
                 'room_night_invoice_ids.invoice_id.amount_residual', 'room_night_invoice_ids.invoice_due')
    def _compute_payable_due_charges(self):
        for rec in self:
            if rec.invoice_payment_type == "by_night":
                rec.payable_due = rec.invoice_due + rec.total_night_invoice_due
            else:
                rec.payable_due = rec.invoice_due

    # Count
    def room_count(self):
        for order in self:
            count = 0
            for line in order.room_ids:
                count += 1
            order.update({
                'no_of_room': count,
            })

    @api.model
    def get_hotel_stats(self):
        active_booking_count = self.env['hotel.booking'].sudo().search_count(
            ['|', ('stages', '=', 'check_in'), ('stages', '=', 'Confirm')])
        food_count = self.env['hotel.restaurant'].sudo().search_count([('stages', '=', 'Confirm')])
        transports_count = self.env['hotel.transport'].sudo().search_count([('stage', '=', 'pending')])
        hall_count = self.env['hotel.feast'].sudo().search_count([('stages', '=', 'Confirm')])
        laundry_count = self.env['laundry.service'].sudo().search_count([('stages', '=', 'In Progress')])
        table_count = self.env['hotel.restaurant.reservation'].sudo().search_count([('state', '=', 'order')])
        staff_count = self.env['hr.employee'].sudo().search_count([('is_staff', '=', True)])
        driver_count = self.env['res.partner'].sudo().search_count([('is_driver', '=', True)])
        attendance_count = self.env['hr.attendance'].sudo().search_count([('check_in', '=', date.today())])
        leave_count = self.env['hr.leave'].sudo().search_count([('state', '=', 'confirm')])
        house_count = self.env['hotel.housekeeping'].sudo().search_count([('state', '=', 'Assign')])
        book_count = self.env['table.details'].sudo().search_count([('stages', '=', 'Available')])
        order_count = self.env['hotel.reservation.order'].sudo().search_count([('state', '=', 'order')])
        amenities_count = self.env['hotel.room.amenities'].sudo().search_count([('product_id','=','product_id')])
        staff_available_count = self.env['hr.employee'].sudo().search_count([('is_staff','=',True),('active','=',True),('is_absent','!=',True)])
        male_female = [['Male', 'Female'], [15, 7]]
        d_booking = self.env['hotel.booking'].sudo().search_count([('stages', '=', 'Draft')])
        c_booking = self.env['hotel.booking'].sudo().search_count([('stages', '=', 'Confirm')])
        check_in_booking = self.env['hotel.booking'].sudo().search_count([('stages', '=', 'check_in')])
        cancel_booking = self.env['hotel.booking'].sudo().search_count([('stages', '=', 'Cancel')])
        booking_inquiry= self.env['booking.inquiry'].sudo().search_count([('state','=','draft')])
        data = {
            'active_booking_count': active_booking_count,
            'food_count': food_count,
            'transports_count': transports_count,
            'hall_count': hall_count,
            'laundry_count': laundry_count,
            'table_count': table_count,
            'staff_count': staff_count,
            'driver_count': driver_count,
            'attendance_count': attendance_count,
            'leave_count': leave_count,
            'house_count': house_count,
            'book_count': book_count,
            'order_count': order_count,
            'amenities_count': amenities_count,
            'inquiry_count' : booking_inquiry,
            'staff_available_count': staff_available_count,
            'male_female': male_female,
            'top_customer': self.get_top_customer(),
            'get_cat_room': self.get_cat_room(),
            'booking_month': self.booking_month(),
            'booking_day': self.booking_day(),
            'today_check_out': self.today_check_out_count(),
            'today_check_in': self.today_check_in_count(),
            'room': [['Draft', 'Confirm', 'Check In', 'Cancel'],
                     [d_booking, c_booking, check_in_booking, cancel_booking]],
            'company': self.env.user.company_id.name
        }

        return data

    def get_top_customer(self):
        partner, amount, data = [], [], []
        customer = self.env['res.partner'].sudo().search(
            [('is_agent', '=', False)]).mapped('id')
        for group in self.env['account.move'].read_group([('partner_id', 'in', customer)],
                                                         ['amount_total',
                                                          'partner_id'],
                                                         ['partner_id'],
                                                         orderby="amount_total DESC", limit=5):
            if group['partner_id']:
                name = self.env['res.partner'].sudo().browse(
                    int(group['partner_id'][0])).name
                partner.append(name)
                amount.append(group['amount_total'])

        data = [partner, amount]

        return data

    def get_cat_room(self):
        stages, room_counts, data_cat = [], [], []
        room_cat_ids = self.env['hotel.room.type'].sudo().search([])
        if not room_cat_ids:
            data_cat = [[], []]
        for stg in room_cat_ids:
            room_data = self.env['hotel.room'].sudo().search_count([('room_category_id', '=', stg.id)])
            room_counts.append(room_data)
            stages.append(stg.name)
        data_cat = [stages, room_counts]
        return data_cat

    def booking_month(self):
        data_dict = {'January': 0,
                     'February': 0,
                     'March': 0,
                     'April': 0,
                     'May': 0,
                     'June': 0,
                     'July': 0,
                     'August': 0,
                     'September': 0,
                     'October': 0,
                     'November': 0,
                     'December': 0,
                    }
        booking = self.env['hotel.booking'].sudo().search(['|', ('stages', '=', 'Confirm'), ('stages', '=', 'check_in')])
        for data in booking:
            data_dict[data.create_date.strftime("%B")] = data_dict[data.create_date.strftime("%B")] + 1
        return [list(data_dict.keys()), list(data_dict.values())]

    def booking_day(self):
        day_dict = {}
        year = fields.date.today().year
        month = fields.date.today().month
        num_days = calendar.monthrange(year, month)[1]
        days = [date(year, month, day) for day in range(1, num_days + 1)]
        for data in days:
            day_dict[data.strftime('%d') + " " + data.strftime('%h')] = 0
        booking = self.env['hotel.booking'].search(['|', ('stages', '=', 'Confirm'), ('stages', '=', 'check_in')])
        for data in booking:
            if data.create_date.year == year and month == data.create_date.month:
                booking_time = data.create_date.strftime('%d') + " " + data.create_date.strftime('%h')
                day_dict[booking_time] = day_dict[booking_time] + 1
        return [list(day_dict.keys()), list(day_dict.values())]

    def today_check_in_count(self):
        today_date = fields.Date.today()
        count = 0
        for data in self.env['hotel.room.details'].sudo().search([('stages', '=', 'Booked')]):
            date = data.check_in.date()
            if date == today_date:
                count = count + 1
        return count

    def today_check_out_count(self):
        today_date = fields.Date.today()
        count = 0
        for data in self.env['hotel.room.details'].sudo().search([('stages', '=', 'Booked')]):
            date = data.check_out.date()
            if date == today_date:
                count = count + 1
        return count


class HotelBookingProofDetails(models.Model):
    _name = 'proof.details'
    _description = "Proof Details"
    _rec_name = 'booking_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    id_number = fields.Char('Document Number', required=True)
    id_name = fields.Char('Document Name', required=True)
    person_Id = fields.Char('Full Name', required=True)
    document = fields.Binary(string='Document', required=True)
    file_name = fields.Char()
    booking_id = fields.Many2one('hotel.booking', required=True)
    customer_id = fields.Many2one(
        related='booking_id.customer_id', string='Customer')
    proof_number = fields.Char(string='', copy=False, readonly=True,
                               default=lambda self: 'New')


class HotelExtraServices(models.Model):
    _name = 'hotel.extra.services'
    _description = "Hotel Extra Service"
    _rec_name = 'service'

    service = fields.Char('Service', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(string='Amount')
    quantity = fields.Integer(string='Quantity', required=True)
    booking_id = fields.Many2one('hotel.booking')
    hall_id = fields.Many2one('hotel.feast')
    all_amount = fields.Monetary(
        string='Total Amount', compute='total_all_amount_charges')

    @api.depends('amount', 'quantity')
    def total_all_amount_charges(self):
        for rec in self:
            rec.all_amount = rec.amount * rec.quantity
