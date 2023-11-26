from odoo import api, models
from datetime import date, datetime, timedelta
import pytz
import calendar

class RoomPerDayBooking(models.AbstractModel):
    _name = 'report.pways_advance_hotel_management.room_per_day_report'
    _description = "All Room Par Day Report"


    @api.model
    def _get_report_values(self, docids, data=None):
        start_date_str = data.get('start_date')
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")

        start_month = data.get('month_start_month')
        end_month = data.get('month_end_month')

        start_day = data.get('start_day')
        end_day = data.get('end_day')
        report_type = data.get('report_type')

        target_time_zone = self.env.context.get('tz') or 'UTC'
        month_start_date_str = data.get('month_start_date')
        month_start_date = datetime.strptime(month_start_date_str, "%Y-%m-%d %H:%M:%S")
        month_end_date_str = data.get('month_end_date')
        month_end_date = datetime.strptime(month_end_date_str, "%Y-%m-%d %H:%M:%S")
        month = month_start_date.strftime("%B")
        year = month_start_date.year

        day_names = []
        room_dict = {}
        revenue_dict = {}
        room_list = []
        emp_list = []
        rev_list = []
        my_months = []

        fil_room_ids = self.env['hotel.room'].search([])
        room_ids = fil_room_ids.filtered(lambda x: x.hotel_room_details_ids)
        current_date = month_start_date
        if report_type in ("room", "revenue"):
            while current_date <= month_end_date:
                day_name = current_date.strftime('%A')[0]
                day_names.append(day_name)
                current_date += timedelta(days=1)

            target_time_zone = self.env.context.get('tz') or 'UTC'
            tz = pytz.timezone(target_time_zone)
            for room in room_ids:
                room_dict[room] = {}
                fil_room_details_ids = self.env['hotel.room.details'].search([('room_id', '=' , room.id)])
                sort_room_details_ids = fil_room_details_ids.filtered(lambda x: x.check_in.date() >= month_start_date.date() and  x.check_out.date() <= month_end_date.date())
                if sort_room_details_ids:
                    for day in range(1, end_day+1):
                        emp_list = []
                        room_dict[room][day]  = []
                        if report_type == "room":
                            for room_de in sort_room_details_ids:
                                check_in = room_de.check_in.astimezone(tz)
                                check_out = room_de.check_out.astimezone(tz)
                                room_no_id = (check_in.day <= day <= check_out.day)
                                if room_no_id:
                                    emp_list.append(room_de.room_id)

                        if report_type == "revenue":
                            for room_de in sort_room_details_ids:
                                check_in = room_de.check_in.astimezone(tz)
                                check_out = room_de.check_out.astimezone(tz)
                                room_no_id = check_out.day == day
                                if room_no_id:
                                    emp_list.append({'total_price': room_de.booking_id.total_amount})
                        room_dict[room][day] = emp_list 
            return {
                'day_names' : day_names,
                'end_day' : end_day,
                'month': month,
                'year': year,
                'data': data,
                'room_dict': room_dict,
            }

        else:
            if report_type == "total_revenue":
                for month in range(1, 13):
                    month_start_date = start_date.replace(month=month, day=1 ,hour=0, minute=59, second=59, microsecond=999)
                    _, last_day = calendar.monthrange(month_start_date.year, month_start_date.month)
                    month_end_date = month_start_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999)
                    my_months.append(month_start_date.strftime("%B"))

                for room in room_ids:
                    revenue_dict[room] = {}
                    hotel_room_details_ids = self.env['hotel.room.details'].search([('room_id', '=' , room.id)])
                    # hotel_room_details_ids = fil_room_details_ids.filtered(lambda x: x.check_in.date() >= month_start_date.date() and  x.check_out.date() <= month_end_date.date())
                    if hotel_room_details_ids:
                        for mon in range(1, end_month+1):
                            rev_list = []
                            revenue_dict[room][mon] = []
                            fil_room_details_ids = hotel_room_details_ids.filtered(lambda x: x.check_out.month == mon)
                            total_vals = sum(fil_room_details_ids.mapped('booking_id').mapped('total_amount'))
                            revenue_dict[room][mon] = total_vals
            else:
                target_time_zone = self.env.context.get('tz') or 'UTC'
                tz = pytz.timezone(target_time_zone)
                for room in room_ids:
                    revenue_dict[room] = {}
                    for mon in range(1, 13):
                        revenue_dict[room][mon] = []
                        total_booked = 0
                        month_start_date = start_date.replace(month=mon, day=1 ,hour=0, minute=59, second=59, microsecond=999)
                        _, last_day = calendar.monthrange(month_start_date.year, month_start_date.month)
                        month_end_date = month_start_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999)
                        if month_start_date.strftime("%B") not in my_months:
                            my_months.append(month_start_date.strftime("%B"))
                        fil_room_details_ids = self.env['hotel.room.details'].search([('room_id', '=' , room.id)])
                        hotel_room_details_ids = fil_room_details_ids.filtered(lambda x: x.check_in.date() >= month_start_date.date() and  x.check_out.date() <= month_end_date.date())
                        if hotel_room_details_ids:
                            month_day = (month_end_date - month_start_date).days
                            total_vals = []
                            for day in range(1, month_day+2):
                                for room_de in hotel_room_details_ids:
                                    check_in = room_de.check_in.astimezone(tz)
                                    check_out = room_de.check_out.astimezone(tz)
                                    room_no_id = (check_in.day <= day <= check_out.day)
                                    if room_no_id:
                                        total_booked += 1
                                        total_non_booked = month_day+1 - total_booked
                            revenue_dict[room][mon] = [total_non_booked, total_booked]
        return {
            'my_months': my_months,
            'end_month' : end_month,
            'month': month,
            'year': year,
            'data': data,
            'revenue_dict': revenue_dict,
        }
