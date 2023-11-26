

from odoo import models, fields, api, _

class HotelBeertype(models.Model):

    _name = "hotel.beer.type"
    _description = "Hotel Restaurant Beer Bar"
    _order = 'id desc'


    name = fields.Char(readonly=True)    
    product_id = fields.Many2one('product.product',string ="Product Name" ,required=True)
    description = fields.Char(string="Description")
    qty = fields.Integer(string="Quantity" , default=1 )
    list_price = fields.Float(string="Price")
    # uom_id = fields.Char()
    price_subtotal = fields.Float(compute="_compute_price_subtotal", string="Subtotal")

    @api.onchange('product_id')
    def price_details(self):
        if self.product_id:
            self.update({'list_price': self.list_price})


    @api.depends("qty", "list_price")
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.list_price * int(line.qty)


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hotel.beer.type') or 'New'
        return super(HotelBeertype, self).create(vals)


class HotelBeerbar(models.Model):

    _name = "hotel.beer.bar"
    _description = "Hotel Restaurant Beer Bar"
    _order = 'id desc'


    name = fields.Char(readonly=True)
    booking_id = fields.Many2one('hotel.booking' , required=True)
    customer_id = fields.Many2one('res.partner',related='booking_id.customer_id', string='Customer')
    product_line = fields.Many2many('hotel.beer.type')
    price_subtotal = fields.Monetary(string='Total Amount', compute='services_charges')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_amount_all_total', store=True)
    state = fields.Selection([('draft','New'),('invoice','Invoice'),('done','Done'),('cancel','Cancel')], default='draft', string='State')
    invoice_count = fields.Integer(string="Invoice", compute="_compute_invoice_count")


    def _compute_invoice_count(self):
        for invoice in self:
            invoice.invoice_count = self.env['account.move'].search_count([('partner_id','=', self.customer_id.id)])

    def button_draft(self):
        self.state = "draft"

    def button_done(self):
        self.state = "done"

    def button_cancel(self):
        self.state = "cancel"


    def button_invoice(self):
        inv_list = []
        inv_obj = self.env['account.move']
        for rec in self.product_line:
            tax_ids = [(6, 0, rec.product_id.taxes_id.ids)] 
            inv_list.append((0, 0,{
                'product_id': rec.product_id.id,
                'name':rec.description,
                'quantity':rec.qty,
                'price_unit': rec.price_subtotal,
                'tax_ids': tax_ids,
                # [(4, x) for x in rec.product_id.taxes_id]
            }))
        invoice = inv_obj.create({
            'move_type': 'out_invoice',
            'ref': self.name,
            'partner_id': self.customer_id.id,
            'invoice_line_ids': inv_list
        })
        self.state = "invoice"

    def action_open(self):
        invoice_ids = self.env['account.move'].search([('partner_id', '=', self.customer_id.id)])
        return {
            'name': _('Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'context':"{}",
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoice_ids.ids)],

        }


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hotel.beer.bar') or 'New'
        return super(HotelBeerbar, self).create(vals)

    @api.depends('product_line')
    def services_charges(self):
        for rec in self:
            price_subtotal = 0.0
            for data in rec.product_line:
                price_subtotal = price_subtotal + data.price_subtotal
            rec.price_subtotal = price_subtotal
