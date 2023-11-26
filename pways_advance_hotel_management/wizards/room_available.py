from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
import calendar
    
class RoomAvailable(models.TransientModel): 
    _name = 'room.available.wizard'
    _description = "Booking Rooms Available Wizard"

    start_date = fields.Datetime(string=" Start Date" ,required=True)
    end_date = fields.Datetime(string="End Date" ,required=True)

    @api.onchange('start_date', 'end_date')
    def _onchange_start_end_dates(self):
        today = fields.Datetime.now()
        if self.start_date:
            if self.start_date.date() < today.date():
                raise ValidationError("Start date cannot be less than to today.")
        if self.end_date:
            if self.end_date.date() < today.date():
                raise ValidationError("End date cannot be less to today.")

    def hotel_room_action(self):
        action = self.env.ref('pways_advance_hotel_management.hotel_room_chek_action').read()[0]
        action['context'] = {'start_date': self.start_date, 'end_date': self.end_date}
        return action

    