
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HotelRestaurantReservation(models.Model):

    _name = "hotel.restaurant.reservation"
    _description = "Includes Hotel Restaurant Reservation"
    _rec_name = "reservation_id"
    _order = 'id desc'

    def action_open(self):
        order_ids = self.env['hotel.reservation.order'].search([('reservation_id', '=', self.reservation_id)])
        return {
            'name': _('Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'view_id': False,
            # 'context':"{}",
            'res_model': 'hotel.reservation.order',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', order_ids.ids)],

        }
    order_count = fields.Integer(string="Order", compute="_compute_order_count")


    def _compute_order_count(self):
        for order in self:
            order.order_count = self.env['hotel.restaurant.reservation'].search_count([('reservation_id','=', self.reservation_id)])


    def create_order(self):
        reservation_order = self.env["hotel.reservation.order"]
        for record in self:
            table_ids = record.table_nos_ids.ids
            values = {
                "reservation_id": record.id,
                "order_date": record.start_date,
                "booking_id": record.booking_id.id,
                "table_nos_ids": [(6, 0, table_ids)],
                "is_folio": record.is_folio,
            }
            reservation_order.create(values)
        self.write({"state": "order"})
        return True

    @api.onchange("customer_id")
    def _onchange_partner_id(self):
        if not self.customer_id:
            self.partner_address_id = False
        else:
            addr = self.customer_id.address_get(["default"])
            self.partner_address_id = addr["default"]

    @api.onchange("booking_id")
    def _onchange_folio_id(self):
        for rec in self:
            if rec.booking_id:
                rec.customer_id = rec.booking_id.customer_id.id
                rec.room_id = rec.booking_id.room_ids.room_id

    def action_set_to_draft(self):
        self.write({"state": "draft"})

    def table_reserved(self):
        for reservation in self:
            if not reservation.table_nos_ids:
                raise ValidationError(_("Please Select Tables For Reservation"))
            reservation._cr.execute(
                "select count(*) from "
                "hotel_restaurant_reservation as hrr "
                "inner join reservation_table as rt on \
                             rt.reservation_table_id = hrr.id "
                "where (start_date,end_date)overlaps\
                             ( timestamp %s , timestamp %s ) "
                "and hrr.id<> %s and state != 'done'"
                "and rt.name in (select rt.name from \
                             hotel_restaurant_reservation as hrr "
                "inner join reservation_table as rt on \
                             rt.reservation_table_id = hrr.id "
                "where hrr.id= %s) ",
                (
                    reservation.start_date,
                    reservation.end_date,
                    reservation.id,
                    reservation.id,
                ),
            )
            res = self._cr.fetchone()
            roomcount = res and res[0] or 0.0
            if roomcount:
                raise ValidationError(
                    _(
                        """You tried to confirm reservation """
                        """with table those already reserved """
                        """in this reservation period"""
                    )
                )
            reservation.state = "confirm"
        return True

    def table_cancel(self):
        self.write({"state": "cancel"})

    def table_done(self):
        self.write({"state": "done"})

    reservation_id = fields.Char("Reservation No", readonly=True, index=True)
    room_id = fields.Many2one("hotel.room", "Room No")
    booking_id = fields.Many2one("hotel.booking", "Booking No")
    start_date = fields.Datetime(
        "Start Time", required=True, default=lambda self: fields.Datetime.now()
    )
    end_date = fields.Datetime("End Time")
    # customer_name = fields.Char(string="Customer Name")
    customer_id = fields.Many2one("res.partner", "Customer Name", required=True)
    partner_address_id = fields.Many2one("res.partner", "Address")
    table_nos_ids = fields.Many2many(
        "table.details",
        "reservation_table",
        "reservation_table_id",
        "name",
        string="Table Number",
        help="Table reservation detail.",
        domain =[('stages','=','Available')]
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("order", "Order Created"),
        ],
        "state",
        required=True,
        readonly=True,
        copy=False,
        default="draft",
    )
    is_folio = fields.Boolean("Hotel Guest")

    @api.model
    def create(self, vals):
        seq_obj = self.env["ir.sequence"]
        reserve = seq_obj.next_by_code("hotel.restaurant.reservation") or "New"
        vals["reservation_id"] = reserve
        return super(HotelRestaurantReservation, self).create(vals)

    @api.constrains("start_date", "end_date")
    def _check_start_dates(self):
        if self.start_date >= self.end_date:
            raise ValidationError(_("Start Date Should be less than the End Date!"))
        if self.is_folio:
            for line in self.booking_id.room_ids:
                if self.start_date < line.check_in:
                    raise ValidationError(
                        _(
                            """Start Date Should be greater """
                            """than the Folio Check-in Date!"""
                        )
                    )
                if self.end_date > line.check_out:
                    raise ValidationError(
                        _("End Date Should be less than the Folio Check-out Date!")
                    )

class HotelRestaurantKitchenOrderTickets(models.Model):

    _name = "hotel.restaurant.kitchen.order.tickets"
    _description = "Includes Hotel Restaurant Order"
    _rec_name = "order_ids"
    _order = 'id desc'

    order_number = fields.Char("Reservation No")
    order_ids = fields.Char("KOT Number",readonly=True )
    reservation_number = fields.Char()
    kot_date = fields.Datetime("Date")
    room_no = fields.Char(readonly=True)
    waiter_name = fields.Char(readonly=True)
    kot = fields.Boolean(string="KOT", readonly=True)

    table_nos_ids = fields.Many2many(
        "table.details",
        "restaurant_kitchen_order_rel",
        "table_no",
        "name",
        help="Table reservation detail.",
    )
    kot_list_ids = fields.One2many(
        "hotel.restaurant.order.list",
        "kot_order_id",
        "Order List",
        help="Kitchen order list",
    )


    @api.model
    def create(self, vals):
        vals['order_ids'] = self.env['ir.sequence'].next_by_code('hotel.restaurant.kitchen.order.tickets') or 'New'
        return super(HotelRestaurantKitchenOrderTickets, self).create(vals)
