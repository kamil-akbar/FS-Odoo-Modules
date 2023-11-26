class HotelRestaurantOrder(models.Model):

    _name = "hotel.restaurant.order"
    _description = "Includes Hotel Restaurant Order"
    _rec_name = "order_no"
    _order = 'id desc'

    @api.depends("order_list_ids")
    def _compute_amount_all_total(self):
        for sale in self:
            sale.amount_subtotal = sum(
                line.price_subtotal for line in sale.order_list_ids
            )
            sale.amount_total = 0.0
            if sale.amount_subtotal:
                sale.amount_total = (
                    sale.amount_subtotal + (sale.amount_subtotal * sale.tax) / 100
                )

    def done_cancel(self):
        self.write({"state": "cancel"})

    def set_to_draft(self):
        self.write({"state": "draft"})

    def generate_kot(self):
        res = []
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        restaurant_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            if not order.order_list_ids:
                raise ValidationError(_("Please Give an Order"))
            if not order.table_nos_ids:
                raise ValidationError(_("Please Assign a Table"))
            table_ids = order.table_nos_ids.ids
            kot_data = order_tickets_obj.create(
                {
                    "order_number": order.order_no,
                    "kot_date": order.o_date,
                    "room_no": order.room_id.name,
                    "waiter_name": order.waiter_id.name,
                    "table_nos_ids": [(6, 0, table_ids)],
                }
            )

            for order_line in order.order_list_ids:
                o_line = {
                    "kot_order_id": kot_data.id,
                    "menucard_id": order_line.menucard_id.id,
                    "item_qty": order_line.item_qty,
                    "item_rate": order_line.item_rate,
                }
                restaurant_order_list_obj.create(o_line)
                res.append(order_line.id)
            order.update(
                {
                    "kitchen": kot_data.id,
                    "rest_item_id": [(6, 0, res)],
                    "state": "order",
                }
            )
        return True

    order_no = fields.Char("Order Number", readonly=True)
    o_date = fields.Datetime(
        "Order Date", required=True, default=lambda self: fields.Datetime.now()
    )
    room_id = fields.Many2one("product.product", "Room No")
    folio_id = fields.Many2one("hotel.folio", "Folio No")
    waiter_id = fields.Many2one("res.partner", "Waiter")
    table_nos_ids = fields.Many2many(
        "hotel.restaurant.tables",
        "restaurant_table_order_rel",
        "table_no",
        "name",
        "Table Number",
    )
    order_list_ids = fields.One2many(
        "hotel.restaurant.order.list", "restaurant_order_id", "Order List"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", string="Subtotal"
    )
    amount_total = fields.Float(compute="_compute_amount_all_total", string="Total")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("order", "Order Created"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        required=True,
        readonly=True,
        copy=False,
        default="draft",
    )
    is_folio = fields.Boolean(
        "Is a Hotel Guest??", help="is customer reside in hotel or not"
    )
    customer_id = fields.Many2one("res.partner", "Customer Name", required=True)
    kitchen = fields.Integer()
    rest_item_id = fields.Many2many(
        "hotel.restaurant.order.list",
        "restaurant_kitchen_rel",
        "restau_id",
        "kit_id",
        "Rest",
    )

    @api.model
    def create(self, vals):
        seq_obj = self.env["ir.sequence"]
        rest_order = seq_obj.next_by_code("hotel.restaurant.order") or "New"
        vals["order_no"] = rest_order
        return super(HotelRestaurantOrder, self).create(vals)

    @api.onchange("folio_id")
    def _onchange_folio_id(self):
        if self.folio_id:
            self.update(
                {
                    "customer_id": self.folio_id.partner_id.id,
                    "room_id": self.folio_id.room_line_ids[0].product_id.id,
                }
            )

    def generate_kot_update(self):
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            line_data = {
                "order_number": order.order_no,
                "kot_date": fields.Datetime.to_string(fields.datetime.now()),
                "room_no": order.room_id.name,
                "waiter_name": order.waiter_id.name,
                "table_nos_ids": [(6, 0, order.table_nos_ids.ids)],
            }
            kot_id = order_tickets_obj.browse(self.kitchen)
            kot_id.write(line_data)
            for order_line in order.order_list_ids:
                if order_line.id not in order.rest_item_id.ids:
                    kot_data = order_tickets_obj.create(line_data)
                    order.kitchen = kot_data.id
                    o_line = {
                        "kot_order_id": kot_data.id,
                        "menucard_id": order_line.menucard_id.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    order.rest_item_id = [(4, order_line.id)]
                    rest_order_list_obj.create(o_line)
        return True

    def done_order_kot(self):
        hsl_obj = self.env["hotel.service.line"]
        so_line_obj = self.env["sale.order.line"]
        for order_obj in self:
            for order in order_obj.order_list_ids:
                if order_obj.folio_id:
                    values = {
                        "order_id": order_obj.folio_id.order_id.id,
                        "name": order.menucard_id.name,
                        "product_id": order.menucard_id.product_id.id,
                        "product_uom": order.menucard_id.uom_id.id,
                        "product_uom_qty": order.item_qty,
                        "price_unit": order.item_rate,
                        "price_subtotal": order.price_subtotal,
                    }
                    sol_rec = so_line_obj.create(values)
                    hsl_obj.create(
                        {
                            "folio_id": order_obj.folio_id.id,
                            "service_line_id": sol_rec.id,
                        }
                    )
                    order_obj.folio_id.write(
                        {"hotel_restaurant_orders_ids": [(4, order_obj.id)]}
                    )
            self.write({"state": "done"})
        return True