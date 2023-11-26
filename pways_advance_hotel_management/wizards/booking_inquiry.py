from odoo import fields, api, models
    
class BookingInquiryPayment(models.TransientModel): 

    _name = "booking.inquiry.payment"
    _description = "Booking Inquiry Payment"

    payment_method = fields.Many2one('account.journal' , string="Payment Method")
    amount = fields.Float(string="Amount")
    ref = fields.Char()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)

    def otm_paid(self):
        if not self.payment_method:
            raise UserError("Please select payment method")
        inquiry_id = self.env['booking.inquiry'].browse(self.env.context.get('active_id'))
        payment_methods = self.payment_method.inbound_payment_method_line_ids
        payment_method_id = payment_methods and payment_methods[0] or False
        payment_obj = self.env['account.payment']
        vals = {
                'journal_id' : self.payment_method.id,
                'amount' : self.amount,
                'currency_id' : self.currency_id.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'inquiry_id' : inquiry_id and inquiry_id.id,
                'booking_id': False,
                'ref': self.ref
            }
        payment_id = payment_obj.create(vals)
        payment_id.action_post()
        return True