# -*- coding: utf-8 -*-

from odoo import fields, api, models


class RoomCancellation(models.TransientModel):
    _name = "room.cancellation"
    _description = "Room Cancellation Charge"
    _rec_name = "booking_id"

    booking_id = fields.Many2one('hotel.booking', string="Booking")
    hall_booking_id = fields.Many2one('hotel.feast', string="Hall Booking")
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    charge = fields.Monetary(string="Charge")
    cancellation_reason = fields.Text(string="Cancellation Reason")
    is_cancellation_charge = fields.Boolean(string="Cancellation Charge")
    hall_cancel = fields.Boolean(string="Hall cancel")

    def action_room_cancellation(self):
        for rec in self:
            if rec.hall_cancel:
                rec.hall_booking_id.confirm_to_cancel()
                cancel_hall_data = {
                    'cancellation_charge': rec.charge,
                    'is_cancellation_charge': rec.is_cancellation_charge,
                    'cancellation_reason': rec.cancellation_reason
                }
                rec.hall_booking_id.write(cancel_hall_data)
                if rec.is_cancellation_charge:
                    data = {
                        'product_id': self.env.ref('pways_advance_hotel_management.hotel_cancellation_charge').id,
                        'name': 'Cancellation Charge',
                        'quantity': 1,
                        'price_unit': rec.charge,
                    }
                    invoice_line = [(0, 0, data)]
                    record = {
                        'partner_id': rec.hall_booking_id.customer_id.id,
                        'invoice_date': fields.Date.today(),
                        'invoice_line_ids': invoice_line,
                        'move_type': 'out_invoice',

                    }
                    cancels_invoice_id = self.env['account.move'].sudo().create(record)
                    cancels_invoice_id.action_post()
                    rec.hall_booking_id.cancels_invoice_id = cancels_invoice_id.id
            else:
                rec.booking_id.confirm_to_cancel()
                cancel_data = {
                    'cancellation_charge': rec.charge,
                    'is_cancellation_charge': rec.is_cancellation_charge,
                    'cancellation_reason': rec.cancellation_reason
                }
                rec.booking_id.write(cancel_data)
                if rec.is_cancellation_charge:
                    data = {
                        'product_id': self.env.ref('pways_advance_hotel_management.hotel_cancellation_charge').id,
                        'name': 'Cancellation Charge',
                        'quantity': 1,
                        'price_unit': rec.charge,
                    }
                    invoice_line = [(0, 0, data)]
                    record = {
                        'partner_id': rec.booking_id.customer_id.id,
                        'invoice_date': fields.Date.today(),
                        'invoice_line_ids': invoice_line,
                        'move_type': 'out_invoice',

                    }
                    cancels_invoice_id = self.env['account.move'].sudo().create(
                        record)
                    cancels_invoice_id.action_post()
                    rec.booking_id.cancels_invoice_id = cancels_invoice_id.id
                rec.booking_id.check_in_booking_status()
