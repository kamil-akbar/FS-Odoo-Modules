# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TransportDriver(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean(string='Driver')



class RestaurantInvoice(models.Model):
    _inherit = 'account.move'

    reservation_id = fields.Many2one("hotel.restaurant.reservation", "Reservation No")
    booking_id = fields.Many2one("hotel.booking", "Booking No")
