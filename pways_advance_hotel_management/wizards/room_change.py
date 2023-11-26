from odoo import fields, api, models


class RoomChange(models.TransientModel):
    _name = 'room.change'
    _description = 'Room Change'
    _rec_name = 'room_id'

    old_room_id = fields.Many2one('hotel.room.details', string="Room To Change")
    room_id = fields.Many2one('hotel.room', string="Room")
    booking_id = fields.Many2one('hotel.booking', string="Booking")
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    is_room_change_charges = fields.Boolean(string="Is Charges")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    charges = fields.Monetary(string="Room Change Charges")

    @api.onchange('check_in', 'check_out', 'room_id')
    def _get_room_id(self):
        for rec in self:
            room_ids = self.env['hotel.room.details'].sudo().search([('check_in', '<=', rec.check_out),
                                                                     ('check_out', '>=', rec.check_in),
                                                                     ('stages', '!=', 'Available')]).mapped(
                'room_id').ids

            return {'domain': {'room_id': [('id', 'not in', room_ids)]}}

    @api.onchange('old_room_id', 'booking_id')
    def _get_old_room_id(self):
        for rec in self:
            ids = []
            for data in rec.booking_id.room_ids:
                if data.stages == "Booked":
                    ids.append(data.id)
            return {'domain': {'old_room_id': [('id', 'in', ids)]}}

    @api.onchange('old_room_id')
    def _onchange_old_room_check_in_check_out(self):
        for rec in self:
            if rec.old_room_id:
                rec.check_in = rec.old_room_id.check_in
                rec.check_out = rec.old_room_id.check_out

    def action_room_change(self):
        if self.is_room_change_charges:
            data = {
                'service': 'Room Change : ' + self.old_room_id.room_id.room_no + " to " + self.room_id.room_no,
                'quantity': 1,
                'amount': self.charges,
                'booking_id': self.booking_id.id
            }
            self.env['hotel.extra.services'].create(data)
        self.old_room_id.room_id = self.room_id.id
