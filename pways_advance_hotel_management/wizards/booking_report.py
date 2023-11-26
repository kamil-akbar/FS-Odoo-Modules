# -*- coding: utf-8 -*-

from odoo import fields, api, models
import xlwt
import base64
from io import BytesIO


class BookingExcelReport(models.TransientModel):
    _name = 'booking.excel.report'
    _description = "Booking Excel report"

    check_in = fields.Date(string="Check In Date", required=True)
    check_out = fields.Date(string="Check Out Date", required=True)

    def booking_excel_report(self):
        check_in = self.check_in
        check_out = self.check_out
        customer_ids = self.env['hotel.room.details'].search(
            [('check_in', '>=', check_in),
             ('check_out', '<=', check_out)])

        filename = 'Customer Details.pdf'
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet('Customer', cell_overwrite_ok=True)
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        format1 = xlwt.easyxf()

        sheet1.col(0).width = 5000
        sheet1.col(1).width = 5000
        sheet1.col(2).width = 6000
        sheet1.col(3).width = 6000
        sheet1.col(4).width = 6000
        sheet1.col(5).width = 6000
        sheet1.write(0, 0, 'Customer', format1)
        sheet1.write(0, 1, 'Room', format1)
        sheet1.write(0, 2, 'Check-In Date', format1)
        sheet1.write(0, 3, 'Check-Out Date', format1)
        sheet1.write(0, 4, 'Number Of Days', format1)
        sheet1.write(0, 5, 'Total Charges', format1)
        row = 1
        for customer in customer_ids:
            sheet1.write(row, 0, customer.booking_id.customer_id.name, format1)
            sheet1.write(row, 1, customer.room_id.room_no, format1)
            sheet1.write(row, 2, customer.check_in, date_format)
            sheet1.write(row, 3, customer.check_out, date_format)
            sheet1.write(row, 4, customer.days)
            sheet1.write(row, 5, customer.total_price)
            row += 1

        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        attachment = self.env['ir.attachment'].sudo()
        filename = 'Customer Details' + ".xlsx"
        attachment_id = attachment.create(
            {'name': filename,
             'type': 'binary',
             'public': False,
             'datas': out})
        if attachment_id:
            report = {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % (attachment_id.id),
                'target': 'self',
                'nodestroy': False,
            }
            return report
