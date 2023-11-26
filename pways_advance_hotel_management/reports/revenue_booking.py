from odoo import api, models
from datetime import date, datetime, timedelta
import pytz

class RoomRevenue(models.AbstractModel):
    _name = 'report.pways_advance_hotel_management.room_revenue_report'
    _description = "Room Revenue Report"