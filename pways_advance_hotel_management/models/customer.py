from odoo import models, fields, api

class HotelCustomerBooking(models.Model):
    _inherit = 'res.partner'

    is_agent = fields.Boolean(string="Agent")


class HotelCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Description'

    policy = fields.Text()
    term = fields.Text()
    notification_hour = fields.Float(string="Notification Hour", default="2.0")