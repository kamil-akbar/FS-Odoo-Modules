from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from datetime import datetime, timedelta
import base64
import datetime
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.addons.payment import utils as payment_utils
from odoo import fields, http, SUPERUSER_ID, tools, _
import dateutil.parser
from datetime import timedelta, date , datetime
from dateutil.relativedelta import relativedelta
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, MissingError, ValidationError
 
class WebsiteProductFilter(WebsiteSale):
    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        fuzzy_search_term, product_count, search_result = super()._shop_lookup_products(attrib_set, options, post, search, website)
        today = datetime.now()
        if post.get('checkin') and post.get('checkout'):
            checkin_datetime = datetime.strptime(post.get('checkin'), '%Y-%m-%d') 
            checkout_datetime = datetime.strptime(post.get('checkout'),'%Y-%m-%d') 
            search_result = search_result._filter_on_available_room(post.get('checkin'), post.get('checkout'), search_result)
        return fuzzy_search_term, product_count, search_result

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False, csrf=False)
    def shop_payment_confirmation(self, **post):
        lines = []
        response = super(WebsiteProductFilter, self).shop_payment_confirmation(**post)
        if response:
            sale_order_id = request.session.get('sale_last_order_id')
            sale_order = request.env['sale.order'].sudo().search([('id','=',sale_order_id)])
            if sale_order:
                for rec in sale_order:
                    for line in rec.order_line:
                        room_id = line.product_id.room_ids
                        domain = ['|', '|', '&', ('check_in', '>=', line.checkin_date), ('check_in', '<=', line.checkout_date),
                              '&', ('check_out', '>=', line.checkin_date), ('check_out', '<=', line.checkout_date),
                              '&', ('check_in', '<=', line.checkin_date), ('check_out', '>=', line.checkout_date)]
                        room_booking = request.env['hotel.room.details'].sudo().search(domain)
                        all_rooms = request.env['hotel.room'].sudo().search([ ])
                        room = room_booking.mapped('room_id')
                        free_rooms = all_rooms - room
                        product_rooms = free_rooms.filtered(lambda r: r in room_id)
                        if room_id:
                            for x in range(int(line.product_uom_qty)):
                                if line.checkin_date and line.checkout_date:
                                    vals = [0, x, {
                                        'check_in': line.checkin_date,
                                        'check_out': line.checkout_date,
                                        'room_id': product_rooms[x].id,
                                    }]
                                    lines.append(vals)
                                else:
                                    raise ValidationError("Check In Date or Checkout Date is missing")
                        else:
                            raise ValidationError("Room is not available")
                    booking_values = {
                        'customer_id': sale_order.partner_id.id,
                        'room_ids': lines,
                    }
                    booking_id = request.env['hotel.booking'].sudo().create(booking_values)
        return response

class AppointmentCount(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        rtn = super(AppointmentCount, self)._prepare_home_portal_values(counters)
        login_user = request.env.user.partner_id
        rtn['hotel_booking_count'] = request.env['hotel.booking'].sudo().search_count([('customer_id','=', login_user.id)])
        rtn['booking_inquiry_count'] = request.env['booking.inquiry'].sudo().search_count([('partner_id','=',login_user.id)])
        rtn['hall_count'] = request.env['hotel.feast'].sudo().search_count([])
        rtn['rest_count'] = request.env['hotel.restaurant.reservation'].sudo().search_count([])
        return rtn

class WebsiteCalendar(http.Controller):
    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    def cart_update(self, product_id, add_qty=1, set_qty=0, product_custom_attribute_values=None, 
        no_variant_attribute_values=None, express=False, **kwargs):
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        if product_custom_attribute_values:
            product_custom_attribute_values = json_scriptsafe.loads(product_custom_attribute_values)

        if no_variant_attribute_values:
            no_variant_attribute_values = json_scriptsafe.loads(no_variant_attribute_values)

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kwargs
        )
        utc = pytz.timezone('UTC')
        today = datetime.now()
        checkin_datetime = kwargs.get('checkin')
        if checkin_datetime:
            checkin_datetime_input = datetime.strptime(checkin_datetime, "%Y-%m-%d %H:%M:%S")  
            checkin_datetime = checkin_datetime_input
            aware_datetime_to = utc.localize(checkin_datetime_input)
            checkin_datetime_tz_utc = aware_datetime_to.astimezone(pytz.utc).replace(tzinfo=None)
            checkin_datetime_tz_utc -= timedelta(hours=5, minutes=30)
        checkout_datetime = kwargs.get('checkout')
        if checkout_datetime:
            checkout_datetime_input = datetime.strptime(checkout_datetime, "%Y-%m-%d %H:%M:%S") 
            checkout_datetime = checkout_datetime_input
            aware_datetime_to = utc.localize(checkout_datetime_input)
            checkout_datetime_tz_utc = aware_datetime_to.astimezone(pytz.utc).replace(tzinfo=None)
            checkout_datetime_tz_utc -= timedelta(hours=5, minutes=30)
        if checkin_datetime and checkout_datetime:
            if checkin_datetime.date() < today.date():
                raise ValidationError("""Check-in date cannot be less than today.""")
            if checkin_datetime > checkout_datetime:
                raise ValidationError("""Check-out date must be greater than check-in date""")
        for line in sale_order.order_line:
            if not line.checkin_date and not line.checkout_date:
                line.checkin_date = checkin_datetime_tz_utc
                line.checkout_date = checkout_datetime_tz_utc
        request.session['website_sale_cart_quantity'] = sale_order.cart_quantity

        if express:
            return request.redirect("/shop/checkout?express=1")

        return request.redirect("/shop/cart")

    @http.route(['/shop/cart/update_json'], type='json', auth="public", website=True, csrf=False)
    def attachment_sale_order(
            self, product_id, line_id=None, add_qty=None, set_qty=None, display=True,
            product_custom_attribute_values=None, no_variant_attribute_values=None, **kw
        ):
        user_tz = request.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        order = request.website.sale_get_order(force_create=True)
        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=True)
            else:
                return {}

        if product_custom_attribute_values:
            product_custom_attribute_values = json_scriptsafe.loads(product_custom_attribute_values)

        if no_variant_attribute_values:
            no_variant_attribute_values = json_scriptsafe.loads(no_variant_attribute_values)

        values = order._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kw
            )
        order_line = order.order_line.filtered(lambda line: line.id == values.get('line_id'))
        product_quntity_check = order_line.product_id.id
        product_qunitiy = order_line.product_uom_qty
        product_qty = request.env['product.product'].sudo().search([('id','=', product_quntity_check)])
        product = request.env['product.template'].sudo().search([('id','=', product_id)])
        sale_order = request.env['sale.order'].sudo().search([('id','=', order.id)])
        checkin_datetime = kw.get('checkin')
        checkout_datetime = kw.get('checkout')
        if product:
            if product.current_available_room >= 0:
                utc = pytz.timezone('UTC')
                today = datetime.now()
                if checkin_datetime:
                    checkin_datetime_input = datetime.strptime(checkin_datetime, "%Y-%m-%d %H:%M:%S")  
                    checkin_datetime = checkin_datetime_input
                    aware_datetime_to = utc.localize(checkin_datetime_input)
                    checkin_datetime_tz_utc = aware_datetime_to.astimezone(pytz.utc).replace(tzinfo=None)
                    checkin_datetime_tz_utc -= timedelta(hours=5, minutes=30)
                checkout_datetime = kw.get('checkout')
                if checkout_datetime:
                    checkout_datetime_input = datetime.strptime(checkout_datetime, "%Y-%m-%d %H:%M:%S") 
                    checkout_datetime = checkout_datetime_input
                    aware_datetime_to = utc.localize(checkout_datetime_input)
                    checkout_datetime_tz_utc = aware_datetime_to.astimezone(pytz.utc).replace(tzinfo=None)
                    checkout_datetime_tz_utc -= timedelta(hours=5, minutes=30)
                if checkin_datetime and checkout_datetime:
                    if checkin_datetime.date() < today.date():
                        raise ValidationError("""Check-in date cannot be less than today.""")
                    if checkin_datetime > checkout_datetime:
                        raise ValidationError("""Check-out date must be greater than check-in date""")

                line_id = values.get('line_id')
                for line in sale_order.order_line:
                    if line_id == line.id:
                        if line.product_template_id.current_available_room >= line.product_uom_qty:
                            if line.product_uom_qty > 0:
                                if not line.checkin_date and not line.checkout_date:
                                    if checkin_datetime and checkout_datetime:
                                        line.checkin_date = checkin_datetime_tz_utc  
                                        line.checkout_date = checkout_datetime_tz_utc  
                                    else:
                                        raise ValidationError("""Both Check In date and Check Out date must be provided.""")
                        else:
                            raise ValidationError("""You cannot add more bookings than available rooms""")
            else:
                raise ValidationError("""Rooms are not available for your selected Check-In and Check-Out dates""")

        request.session['website_sale_cart_quantity'] = order.cart_quantity

        if not order.cart_quantity:
            request.website.sale_reset()
            return values

        values['cart_quantity'] = order.cart_quantity
        values['minor_amount'] = payment_utils.to_minor_currency_units(
            order.amount_total, order.currency_id
        ),
        values['amount'] = order.amount_total

        if not display:
            return values

        values['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template(
            "website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            }
        )
        values['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template(
            "website_sale.short_cart_summary", {
                'website_sale_order': order,
            }
        )
        return values

    @http.route(['/data/product/'], type='json', auth="public", website=True)
    def check_available_rooms(self, checkin, checkout, **kw):
        fil_room_ids = request.env['hotel.room']
        room_detail_ids = request.env['hotel.room.details'].sudo().search([('check_in', '<=', checkout), ('check_out', '>=', checkin)])
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
        return True

    @http.route(['/refrence2/product/'], type='json', auth="public", website=True)
    def check_products_onchange(self, product, **kw):
        existing_record = request.env['product.product'].sudo().search([('id', '=', product)], limit=1)
        order = request.website.sale_get_order()
        response = existing_record.current_available_room  
        if order:
            for line in order.order_line:
                if existing_record == line.product_id:
                    if existing_record.current_available_room >= line.product_uom_qty:
                        response = existing_record.current_available_room - line.product_uom_qty
                else:
                    response = existing_record.current_available_room
        return response

    @http.route(['/product/room'], type='json', auth="public", website=True)
    def check_room_main(self, product, **kw):
        existing_record = request.env['product.template'].sudo().search([('id', '=', product)], limit=1)
        order = request.website.sale_get_order()
        product_id = existing_record.id
        response = existing_record.current_available_room 
        if order:
            for line in order.order_line:
                if product_id == line.product_id.id:
                    if existing_record.current_available_room >= line.product_uom_qty:
                        response = existing_record.current_available_room - line.product_uom_qty
        return response

    @http.route(['/refrence1/product/'], type='json', auth="public", website=True)
    def check_product(self, **kw):
        today = fields.Date.today()
        checkout = today + timedelta(days=1) 
        checkin = today
        fil_room_ids = request.env['hotel.room']
        room_detail_ids = request.env['hotel.room.details'].sudo().search([('check_in', '<=', checkout), ('check_out', '>=', checkin)])
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
        response = 1

        return response


    @http.route('/hotel', type='http', auth="public", website=True)
    def appointment_country_choice(self, message=None, **kwargs):
        hotel = request.env['hotel.booking'].sudo().search([])
        image = request.env['hotel.image'].sudo().search([])
        room_category = request.env['hotel.room.category'].sudo().search([])
        values = {  'hotel': hotel,
                    'image' : image,
                    'category' : room_category}
        return request.render("pways_advance_hotel_management.hotel_homepage", values)

    @http.route('/data/submit', type='http', auth="public", website=True, csrf=False)
    def submit_form(self, **post):
        selected_option = post.get('type')
        check_in = post.get('arrival_date')
        check_out = post.get('departure_date')
        room_type = post.get('type')
        room = request.env['hotel.room.category'].sudo().search([('name','=',room_type)])
        room_details = request.env['hotel.room'].sudo().search([])
        room_available = request.env['hotel.room.details'].sudo().search([('check_in', '<=', check_out),('check_out', '>=', check_in)])
        values = {
            'room': room,
            'room_details': room_details,
            'check_in': check_in, 
            'type' : room_type,  
            'check_out': check_out, 
        }
        return request.render("pways_advance_hotel_management.hotel_room", values)


    @http.route('/room', type='http', auth="public", website=True, csrf=False)
    def room_form(self, **kw):
        category = request.params.get('category')
        room = request.env['hotel.room.category'].sudo().search([('name', '=', category)])
        room_details = request.env['hotel.room'].sudo().search([])
        values = {
            'room': room,
            'room_details': room_details,
            'type' : category, 
        }

        return request.render("pways_advance_hotel_management.hotel_room", values)


    @http.route('/hall',  type='http', auth="public", website=True, csrf=False)
    def hall_form(self, **post):

        hall = request.env['hotel.hall'].sudo().search([ ])
        image = request.env['hotel.image'].sudo().search([])
        values = {  'hall': hall,
                    'image' : image}

        return request.render("pways_advance_hotel_management.hotel_hall", values)


    @http.route('/restaurant',  type='http', auth="public", website=True, csrf=False)
    def restaurant_form(self, **post):
        image = request.env['hotel.image'].sudo().search([])
        values = {'image' : image}
    
        return request.render("pways_advance_hotel_management.hotel_restaurant_template", values)

    @http.route('/hall/submit', type='http', auth="public", website=True, csrf=False)

    def hotel_hall_submit(self, **post):
        inquiry_type = 'hall' 
        existing_record = request.env['booking.inquiry'].sudo().search([
            ('email', '=', post.get('email')),
            ('phone', '=', post.get('phone')),
            ('inquiry_for', '=', inquiry_type)
        ])
        duration = post.get('booking_time')
        book = int(duration)
        booking_date = datetime.strptime(post.get('booking_date'), '%Y-%m-%d')
        departure_date = booking_date + timedelta(hours=book)
        if existing_record:
            raise ValidationError("Email or phone number already registered with the another Booking")
        appointment = request.env['booking.inquiry'].sudo().create({
            'name' : post.get('name'),
            'email' : post.get('email'),
            'phone' : post.get('phone'),
            'hall_type' : post.get('hall'),
            'arrival_date' : post.get('booking_date'),
            'booking_time' : post.get('booking_time'),
            'departure_date' : departure_date,
            'inquiry_for': 'hall'
        })
        return request.render("pways_advance_hotel_management.thankyou_page")

    @http.route('/rest/submit', type='http', auth="public", website=True, csrf=False)

    def hotel_rest_submit(self, **post):
        inquiry_type = 'restaurant' 
        existing_record = request.env['booking.inquiry'].sudo().search([
            ('email', '=', post.get('email')),
            ('phone', '=', post.get('phone')),
            ('inquiry_for', '=', inquiry_type)
        ])
        duration = post.get('booking_time')
        book = int(duration)
        booking_date = datetime.strptime(post.get('booking_date'), '%Y-%m-%d')
        departure_date = booking_date + timedelta(hours=book)
        if existing_record:
            raise ValidationError("Email or phone number already registered with the another Booking")
           
        appointment = request.env['booking.inquiry'].sudo().create({
            'name' : post.get('name'),
            'email' : post.get('email'),
            'phone' : post.get('phone'),
            'person' : post.get('person'),
            'arrival_date' : post.get('booking_date'),
            'booking_time' : post.get('booking_time'),
            'departure_date' : departure_date,
            'inquiry_for': 'restaurant'
        })
        return request.render("pways_advance_hotel_management.thankyou_page")

    @http.route('/room/book', type='http', auth="public", website=True, csrf=False)
    def room_form_submit(self, **post):
        inquiry_type = 'room' 
        existing_record = request.env['booking.inquiry'].sudo().search([
            ('email', '=', post.get('email')),
            ('phone', '=', post.get('phone')),
            ('inquiry_for', '=', inquiry_type)
        ])
        if existing_record:
            raise ValidationError("Email or phone number already registered with the another Booking")

        appointment = request.env['booking.inquiry'].sudo().create({
            'name' : post.get('name'),
            'email' : post.get('email'),
            'phone' : post.get('phone'),
            'person' : post.get('person'),
            'arrival_date' : post.get('arrival_date'),
            'departure_date' : post.get('departure_date'),
            'child' : post.get('child'),
            'number_rooms' : post.get('num_rooms'),
            'person' : post.get('adult'),
            'room_type' : post.get('type'),
            'inquiry_for': 'room'
        })

        return request.render("pways_advance_hotel_management.thankyou_page")

    @http.route('/my/booking', type='http', auth="user", website=True)
    def portal_my_booking(self, message=None, **kwargs):
        login_user = request.env.user.partner_id
        hotel_booking = request.env['hotel.booking'].sudo().search([('customer_id','=', login_user.id)])
        hotel_booking_count = hotel_booking.search_count([])
        pager = portal_pager(
            url="/my/quotes",
            total=hotel_booking_count,
        )
        values = {
            'hotel_booking': hotel_booking,
            'hotel_booking_count': hotel_booking_count

        }
        return request.render("pways_advance_hotel_management.portal_my_booking", values)

    @http.route('/my/inquiry', type='http', auth="user", website=True)
    def portal_my_inquiry(self, message=None, **kwargs):
        login_user = request.env.user.partner_id
        booking_inquiry = request.env['booking.inquiry'].sudo().search([('partner_id','=',login_user.id)])
        booking_inquiry_count = booking_inquiry.search_count([]) 
        
        pager = portal_pager(
            url="/my/quotes",
            total=booking_inquiry_count,
        )
        
        values = {
            'booking_inquiry': booking_inquiry,
            'booking_inquiry_count': booking_inquiry_count
        }

        return request.render("pways_advance_hotel_management.portal_my_inquiry", values)

    @http.route('/my/hall', type='http', auth="user", website=True)
    def portal_my_inquiry(self, message=None, **kwargs):
        booking_hall = request.env['hotel.feast'].sudo().search([])
        hall_count = booking_hall.search_count([]) 
        
        pager = portal_pager(
            url="/my/quotes",
            total=hall_count,
        )
        
        values = {
            'booking_hall': booking_hall,
            'hall_count': hall_count
        }

        return request.render("pways_advance_hotel_management.portal_my_hall", values)

    @http.route('/my/restaurant', type='http', auth="user", website=True)
    def portal_my_inquiry(self, message=None, **kwargs):
        booking_rest = request.env['hotel.restaurant.reservation'].sudo().search([])
        rest_count = booking_rest.search_count([]) 
        
        pager = portal_pager(
            url="/my/quotes",
            total=rest_count,
        )
        
        values = {
            'booking_rest': booking_rest,
            'rest_count': rest_count
        }

        return request.render("pways_advance_hotel_management.portal_my_rest", values)

    @http.route('/my/booking/<int:booking_id>', type='http', auth='user', website=True)
    def  portal_booking_detail_page(self, booking_id, report_type=None, access_token=None, message=False, download=False, **kw):
        hotel_book = request.env['hotel.booking'].sudo().search([('id','=', booking_id)])
        
        values = {
            'hotel_book': hotel_book,
        }
        return request.render('pways_advance_hotel_management.hotel_booking_details_portal', values)
