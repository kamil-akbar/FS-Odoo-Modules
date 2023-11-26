
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class HotelReservationOrder(models.Model):

    _name = "hotel.reservation.order"
    _description = "Reservation Order"
    _rec_name = "order_number"
    _order = 'id desc'

    @api.depends("order_list_ids")
    def _compute_amount_all_total(self):
        for sale in self:
            sale.amount_subtotal = sum(
                line.price_subtotal for line in sale.order_list_ids
            )
            sale.amount_total = (
                sale.amount_subtotal + (sale.amount_subtotal * sale.tax) / 100
            )

    tickets_count = fields.Integer(string="Tickets", compute="_compute_tickets_count")


    def _compute_tickets_count(self):
        for tickets in self:
            tickets.tickets_count = self.env['hotel.restaurant.kitchen.order.tickets'].search_count([('order_number','=', self.order_number)])

    def action_open_tickets(self):
        ticket_ids = self.env['hotel.restaurant.kitchen.order.tickets'].search([('order_number', '=', self.order_number)])
        return {
            'name': _('Tickets Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hotel.restaurant.kitchen.order.tickets',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', ticket_ids.ids)],

        }
    


    def reservation_generate_kot(self):
        res = []
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            if not order.order_list_ids:
                raise ValidationError(_("Please Give an Order"))
            table_ids = order.table_nos_ids.ids
            line_data = {
                "order_number": order.order_number,
                "reservation_number": order.reservation_id.reservation_id,
                "kot_date": order.order_date,
                "waiter_name": order.waitername.name,
                "table_nos_ids": [(6, 0, table_ids)],
            }
            kot_data = order_tickets_obj.create(line_data)
            for order_line in order.order_list_ids:
                if order_line.kot==False:
                    o_line = {
                        "kot_order_id": kot_data.id,
                        "menucard_id": order_line.menucard_id.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    rest_order_list_obj.create(o_line)
                    res.append(order_line.id)
                order.update(
                    {
                        "kitchen": kot_data.id,
                        "rests_ids": [(6, 0, res)],
                        "state": "order",
                    }
                )
            self.order_list_ids.write({'kot': True}) 
            return res


    def reservation_update_kot(self):
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            table_ids = order.table_nos_ids.ids
            line_data = {
                "order_number": order.order_number,
                "reservation_number": order.reservation_id.reservation_id,
                "kot_date": fields.Datetime.to_string(fields.datetime.now()),
                "waiter_name": order.waitername.name,
                "table_nos_ids": [(6, 0, table_ids)],
            }
            kot_id = order_tickets_obj.browse(self.kitchen)
            kot_id.write(line_data)

            for order_line in order.order_list_ids:
                if order_line not in order.rests_ids.ids and order_line.kot==False:
                    kot_data = order_tickets_obj.create(line_data)
                    o_line = {
                        "kot_order_id": kot_data.id,
                        "menucard_id": order_line.menucard_id.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    order.update(
                        {
                            "kitchen": kot_data.id,
                            "rests_ids": [(4, order_line.id)],
                        }
                    )
                    rest_order_list_obj.create(o_line)
                order_line.write({'kot': True}) 
            return True

    def action_invoice(self):
        inv_list = []
        inv_obj = self.env['account.move']
        for rec in self.order_list_ids.filtered(lambda x: not x.current):
                inv_list.append((0, 0,{
                    'product_id': rec.menucard_id.product_id.id,
                    'quantity':rec.item_qty,
                    'price_unit': rec.item_rate,
                    'tax_ids': [(4, x) for x in rec.menucard_id.product_id.taxes_id.ids]
                }))
        inv_obj.create({
            'move_type': 'out_invoice',
            'ref': self.reservation_id,
            'partner_id': self.reservation_id.customer_id.id,
            'reservation_id':self.reservation_id,
            'invoice_line_ids': inv_list
        })
        self.state = "invoice"
        self.order_list_ids.write({'current': True})
    
    def action_open(self):
        invoice_ids = self.env['account.move'].search([('reservation_id', '=', self.reservation_id.id)])        
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



    def done_kot(self):
        self.write({"state": "done"})
        return True

    order_number = fields.Char(readonly=True)
    reservation_id = fields.Many2one("hotel.restaurant.reservation", "Reservation No")
    order_date = fields.Datetime(
        "Date", required=True, default=lambda self: fields.Datetime.now()
    )
    waitername = fields.Many2one("res.partner", "Waiter Name")
    table_nos_ids = fields.Many2many(
        "table.details")
    order_list_ids = fields.One2many(
        "hotel.restaurant.order.list", "reservation_order_id", "Order List"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", string="Subtotal"
    )
    amount_total = fields.Float(compute="_compute_amount_all_total", string="Total")
    kitchen = fields.Integer("Kitchen Id")
    rests_ids = fields.Many2many(
        "hotel.restaurant.order.list",
        "reserv_id",
        "kitchen_id",
        "res_kit_ids",
        "Rest",
    )
    state = fields.Selection(
        [("draft", "Draft"),("order", "Order Created"),("invoice","Invoice"),("done", "Done")],
        required=True,
        readonly=True,
        default="draft",
    )
    booking_id = fields.Many2one("hotel.booking", "Booking No")
    is_folio = fields.Boolean(
        "Hotel Guest", help="is customer reside in hotel or not"
    )
    invoice_count = fields.Integer(string="Invoice", compute="_compute_invoice_count")


    def _compute_invoice_count(self):
        for invoice in self:
            invoice.invoice_count = self.env['account.move'].search_count([('reservation_id','=', self.reservation_id.id)])

    @api.model
    def create(self, vals):
        seq_obj = self.env["ir.sequence"]
        res_oder = seq_obj.next_by_code("hotel.reservation.order") or "New"
        vals["order_number"] = res_oder
        return super(HotelReservationOrder, self).create(vals)



class HotelRestaurantOrderList(models.Model):
    _name = "hotel.restaurant.order.list"
    _description = "Includes Hotel Restaurant Order"

    @api.depends("item_qty", "item_rate")
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.item_rate * int(line.item_qty)

    @api.onchange("menucard_id")
    def _onchange_item_name(self):
        self.item_rate = self.menucard_id.price

    booking_id = fields.Many2one('hotel.booking')
    restaurant_order_id = fields.Many2one("hotel.restaurant.order", "Restaurant Order")
    reservation_order_id = fields.Many2one("hotel.reservation.order", "Reservation Order")
    kot_order_id = fields.Many2one(
        "hotel.restaurant.kitchen.order.tickets", "Kitchen Order Tickets"
    )
    menucard_id = fields.Many2one("food.item", "Item Name", required=True)
    item_qty = fields.Integer("Qty", required=True, default=1)
    item_rate = fields.Float("Rate")
    price_subtotal = fields.Float(compute="_compute_price_subtotal", string="Subtotal")
    current = fields.Boolean(string="Invoice" ,readonly=True)
    kot = fields.Boolean(string="KOT" ,readonly=True)




class HotelServiceLine(models.Model):

    _name = "hotel.service.line"
    _description = "hotel Service line"

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        return super(HotelServiceLine, self).copy(default=default)

    service_line_id = fields.Many2one("sale.order.line" ,"Service Line", required=True, delegate=True, ondelete="cascade")
    booking_id = fields.Many2one("hotel.booking", ondelete="cascade")
    ser_checkin_date = fields.Datetime("From Date")
    ser_checkout_date = fields.Datetime("To Date")

    @api.model
    def create(self, vals):
        if "booking_id" in vals:
            booking_id = self.env["hotel.booking"].browse(vals["booking_id"])
            vals.update({"order_id": booking_id.order_id.id})
        return super(HotelServiceLine, self).create(vals)


    @api.onchange("ser_checkin_date", "ser_checkout_date")
    def _on_change_checkin_checkout_dates(self):
        if not self.ser_checkin_date:
            time_a = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.ser_checkin_date = time_a
        if not self.ser_checkout_date:
            self.ser_checkout_date = time_a
        if self.ser_checkout_date < self.ser_checkin_date:
            raise ValidationError(_("Checkout must be greater or equal checkin date"))
        if self.ser_checkin_date and self.ser_checkout_date:
            diffDate = self.ser_checkout_date - self.ser_checkin_date
            qty = diffDate.days + 1
            self.product_uom_qty = qty

    def copy_data(self, default=None):
        return self.service_line_id.copy_data(default=default)
