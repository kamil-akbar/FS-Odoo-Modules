from odoo import fields, api, models

class BookingAdvancePayment(models.TransientModel): 

    _name = "booking.advance.payment"
    _description = "Booking Payment"

    payment_method = fields.Many2one('account.journal', string="Payment Method")
    amount = fields.Float(string="Amount")
    ref = fields.Char()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)

    def inqui_paid(self):
        if not self.payment_method:
            raise UserError("Please select payment method")
        booking_id = self.env['hotel.booking'].browse(self.env.context.get('active_id'))
        if not booking_id.is_advance:
            booking_id.advance_amount = 0.00
        partner_id = booking_id.customer_id.id  # Get the partner (customer) associated with the booking

        payment_methods = self.payment_method.inbound_payment_method_line_ids
        payment_method_id = payment_methods and payment_methods[0] or False
        payment_object = self.env['account.payment']
        vals = {
                'journal_id' : self.payment_method.id,
                'amount' : self.amount,
                'currency_id' : self.currency_id.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': partner_id,  # Link the payment to the customer
                'booking_id' : booking_id and booking_id.id,
                'inquiry_id': False,
                'ref': self.ref
            }
        new_advance_amount = booking_id.advance_amount + self.amount
        booking_id.write({'is_advance': True, 'journal_id': self.payment_method.id, 'advance_amount': new_advance_amount})
        payment_id = payment_object.create(vals)
        payment_id.action_post()
        return True