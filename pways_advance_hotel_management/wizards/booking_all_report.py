from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
    
class BookingAllReport(models.TransientModel): 
    _name = 'booking.all.report.wizard'
    _description = "Booking All Report Wizard"

    start_date = fields.Datetime(string="Month Date" ,default=date.today() )
    report_type = fields.Selection([('room', 'Room Booked Per Day'), ('revenue', 'Revenue By Room Per Day'), ('total_revenue', 'Yearly Total Revenue '),('num_book', 'Yearly Total Booking ')], default='room')
    def action_print_report(self):

        month_start_date = self.start_date.replace(day=1, hour=0, minute=59, second=59, microsecond=999)
        _, last_day = calendar.monthrange(month_start_date.year, month_start_date.month)
        month_end_date = month_start_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999)
        
        month_start_month = self.start_date.replace(month=1, day=1 ,hour=0, minute=59, second=59, microsecond=999)
        month_end_month = month_start_month.replace(month=12, day=1, hour=23, minute=59, second=59, microsecond=999)
        
        start_month = month_start_month.month
        end_month = month_end_month.month

        start_day = month_start_date.day
        end_day = month_end_date.day
        room_ids = self.env['hotel.room.details'].search([('check_in', '>=', month_start_date), ('check_in', '<=', month_end_date)])
        data = {
                'start_date' : self.start_date,
                'start_day' : start_day,
                'end_day' : end_day,
                'month_start_date' : month_start_date,
                'month_end_date' : month_end_date,
                'month_start_month' : start_month,
                'month_end_month' : end_month,
                'report_type' : self.report_type,
                'room_ids' : room_ids.ids,
                }
        report = self.env.ref('pways_advance_hotel_management.action_room_per_day_id')
        return report.report_action(self, data=data)
