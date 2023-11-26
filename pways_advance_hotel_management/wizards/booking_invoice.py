from odoo import fields, api, models


class HotelBookingInvoice(models.TransientModel):
    _name = "hotel.booking.invoice"
    _description = "Hotel Booking Invoice Details"
    _rec_name = 'booking_id'

    booking_id = fields.Many2one('hotel.booking', string="Booking")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    room_total_charges = fields.Monetary(string="Room Charged", related='booking_id.room_total_charges', store=True)
    transportation_charges = fields.Monetary(string="Transportation Charges",
                                             related='booking_id.transport_total_charges', store=True)
    advance_amount = fields.Monetary(string="Advance Amount", related='booking_id.advance_amount')
    laundry_charges = fields.Monetary(string="Laundry Charges", related='booking_id.laundry_total_charges', store=True)
    restaurant_charges = fields.Monetary(string="Restaurant Charges", related='booking_id.restaurant_services_charges',
                                         store=True)
    extra_service_charges = fields.Monetary(string="Extra Service Charges", related='booking_id.all_service_amount',
                                            store=True)
    room_charges_desc = fields.Text(string="Room Charges Desc", compute="_compute_room_charge_desc")
    transport_charges_desc = fields.Text(string="Transport Charges Desc", compute="_compute_transport_charge_desc")
    laundry_charges_desc = fields.Text(string="Laundry Charges Desc", compute="_compute_laundry_charge_desc")
    restaurant_charges_desc = fields.Text(string="Restaurant Charges Desc", compute="_compute_restaurant_charge_desc")
    extra_charges_desc = fields.Text(string="Extra Service Charges Desc", compute="_compute_extra_charge_desc")
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_payable_amount")
    payable_amount = fields.Monetary(string="Payable Amount", compute="_compute_payable_amount")
    remaining_amount = fields.Monetary(string="Remaining Amount", compute="_compute_remaining_amount")
    agent_commission = fields.Monetary(string="Agent Commission", compute="_compute_agent_commission")
    invoice_payment_type = fields.Selection(related="booking_id.invoice_payment_type", string="Invoice Payment")
    amiment_charges_desc = fields.Text(string="Animent Charges Desc", compute="_compute_amiment_charge_desc")
    price = fields.Monetary(string="Animent Service", related='booking_id.price')
    bar_charges_desc = fields.Text(string="Bar Charges Desc", compute="_compute_bar_charge_desc")
    price_subtotal = fields.Monetary(string="Bar Service", related='booking_id.price_subtotal')

    @api.depends('total_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.total_amount - rec.advance_amount
      

    @api.depends('booking_id')
    def _compute_bar_charge_desc(self):
        for rec in self:
            bar = ""
            for data in rec.booking_id.product_line_ids:
                bar = bar + " " + str( data.product_id.name) + "-" +str(data.price_subtotal) + rec.currency_id.symbol + "\n"
            rec.bar_charges_desc = bar

    @api.depends('booking_id')
    def _compute_amiment_charge_desc(self):
        for rec in self:
            aminites = ""
            for data in rec.booking_id.room_amenities_ids:
                aminites = aminites + " " +str( data.product_id.name)+"-" +str(data.price) + rec.currency_id.symbol + "\n"
            rec.amiment_charges_desc = aminites



    @api.depends('booking_id')
    def _compute_room_charge_desc(self):
        for rec in self:
            room = ""
            if rec.booking_id.invoice_payment_type == "by_night":
                room = room + " -No Invoice Generated of Room Charges Because Invoice Posted by Every Night- " + "\n"
            for data in rec.booking_id.room_ids:
                room = room + " " + str((data.room_id.room_no + " - " + data.room_id.room_type_id.name)) + " - " + str(
                    data.total_price) + rec.currency_id.symbol + "\n"
            rec.room_charges_desc = room
    
    @api.depends('booking_id')
    def _compute_transport_charge_desc(self):
        for rec in self:
            transport = ""
            for data in rec.booking_id.transport_ids:
                transport = transport + " " + str(data.transport_type) + " - " + str(data.km) + " KM" + " - " + str(
                    data.total_charges) + rec.currency_id.symbol + "\n"
            rec.transport_charges_desc = transport

    @api.depends('booking_id')
    def _compute_laundry_charge_desc(self):
        for rec in self:
            laundry = ""
            for data in rec.booking_id.laundry_ids:
                laundry = laundry + " " + str(data.service_name_id.service_name) + " - " + str(
                    data.quantity) + " Item" + " - " + str(data.total_charges) + rec.currency_id.symbol + "\n"
            rec.laundry_charges_desc = laundry

    @api.depends('booking_id')
    def _compute_restaurant_charge_desc(self):
        for rec in self:
            restaurant = ""
            for data in rec.booking_id.restaurant_ids:
                restaurant = restaurant + " " + str(data.reservation_number) + " - " + str(
                    data.total_charges) + rec.currency_id.symbol + "\n"
            rec.restaurant_charges_desc = restaurant

    @api.depends('booking_id')
    def _compute_extra_charge_desc(self):
        # for rec in self:
        extra = ""
        for data in self.booking_id.service_ids:
            if data.hall_id:
                if not data.hall_id.feast_invoice_id:
                    extra = extra + " " + \
                            str(data.service) + " - " + str(data.all_amount) + \
                            self.currency_id.symbol + "\n"
                else:
                    extra = extra + " " + \
                            str(data.service) + " - " + str(0) + \
                            self.currency_id.symbol + "\n"
            else:
                extra = extra + " " + \
                            str(data.service) + " - " + str(data.all_amount) + \
                            self.currency_id.symbol + "\n"
               
        self.extra_charges_desc = extra

    @api.depends('room_total_charges', 'transportation_charges', 'laundry_charges',
                 'restaurant_charges', 'price_subtotal','price','extra_service_charges', 'booking_id')
    def _compute_payable_amount(self):
        for rec in self:
            total_amount = 0.0
            if rec.booking_id.invoice_payment_type == "by_night":
                room_charges = 0
            else:
                room_charges = rec.room_total_charges
            total_amount = room_charges + rec.transportation_charges + \
                           rec.laundry_charges + rec.restaurant_charges +rec.price_subtotal +rec.price +rec.extra_service_charges
            rec.total_amount = total_amount
            rec.payable_amount = total_amount

    @api.depends('booking_id')
    def _compute_agent_commission(self):
        for rec in self:
            if rec.booking_id:
                if rec.booking_id.is_any_agent:
                    if rec.booking_id.agent_commission_type == "fix":
                        rec.agent_commission = rec.booking_id.agent_commission
                    else:
                        rec.agent_commission = rec.booking_id.agent_percentage_commission
                else:
                    rec.agent_commission = 0.0
            else:
                rec.agent_commission = 0.0

    def action_create_booking_invoice(self):
        for rooms in self.booking_id.room_ids:
            room = self.env['hotel.room'].sudo().search([('room_no','=', rooms.room_id.room_no)])
            room.stages = 'Available'

        Attachment = self.env['ir.attachment']
        manager_id = self.env['ir.model.data'].sudo()._xmlid_lookup('base.group_system')[2]
        group_manager = self.env['res.groups'].sudo().browse(manager_id)
        super_user = group_manager.users[0]
        if not group_manager.users:
            internal_user_id = self.env['ir.model.data'].sudo().get_object_reference('base', 'group_user')[1]
            group_internal_user = self.env['res.groups'].sudo().browse(internal_user_id)
            super_user = group_internal_user.users[0]

        if self.booking_id.is_advance:
            deposit = {
                'payment_type': 'inbound',
                'partner_id': self.booking_id.customer_id.id,
                'amount': self.advance_amount,
                'journal_id': self.booking_id.journal_id.id
            }
            payment_id = self.env['account.payment'].create(deposit)
            payment_id.action_post()
        self.booking_id.confirm_to_done()
        invoice_lines = []
        if self.booking_id.invoice_payment_type == 'once':
            product_id = self.env.ref('pways_advance_hotel_management.hotel_room_charge')
            room_data = {
                'product_id': product_id.id,
                'name': self.room_charges_desc,
                'quantity': 1,
                'price_unit': self.room_total_charges,
                'tax_ids': [(4, x) for x in product_id.taxes_id.ids],
            }
            invoice_lines.append((0, 0, room_data))
        if self.transportation_charges > 0:
            product_id = self.env.ref('pways_advance_hotel_management.hotel_transportation_charge')
            transportation_data = {
                'product_id': product_id.id,
                'name': self.transport_charges_desc,
                'quantity': 1,
                'price_unit': self.transportation_charges,
                'tax_ids': [(4, x) for x in product_id.taxes_id.ids],
            }
            invoice_lines.append((0, 0, transportation_data))
        if self.restaurant_charges > 0:
            product_id = self.env.ref('pways_advance_hotel_management.hotel_restaurant_charge')
            restaurant_data = {
                'product_id': product_id.id,
                'name': self.restaurant_charges_desc,
                'quantity': 1,
                'price_unit': self.restaurant_charges,
                'tax_ids': [(4, x) for x in product_id.taxes_id.ids],
            }
            invoice_lines.append((0, 0, restaurant_data))
        if self.price_subtotal > 0:
            product_id = self.env.ref('pways_advance_hotel_management.hotel_bar_charge')
            bar_data = {
                'product_id': product_id.id,
                'name': self.bar_charges_desc,
                'quantity': 1,
                'price_unit': self.price_subtotal,
                'tax_ids': [(4, x) for x in product_id.taxes_id.ids],
            }
            invoice_lines.append((0, 0, bar_data))
        if self.laundry_charges > 0:
            product_id = self.env.ref('pways_advance_hotel_management.hotel_laundry_charge')
            laundry_data = {
                'product_id': product_id.id,
                'name': self.laundry_charges_desc,
                'quantity': 1,
                'price_unit': self.laundry_charges,
                'tax_ids': [(4, x) for x in product_id.taxes_id.ids],
            }
            invoice_lines.append((0, 0, laundry_data))
        if self.extra_service_charges > 0:
            product_id = self.env.ref('pways_advance_hotel_management.hotel_extra_services_charge')
            extra_service_data = {
                'product_id': product_id.id,
                'name': self.extra_charges_desc,
                'quantity': 1,
                'price_unit': self.extra_service_charges,
            }
            invoice_lines.append((0, 0, extra_service_data))
        if self.price > 0:
            product_id = self.env.ref('pways_advance_hotel_management.hotel_aminities_charge')
            amimities_service_data = {
                'product_id': product_id.id,
                'name': self.amiment_charges_desc,
                'quantity': 1,
                'price_unit': self.price,
                'tax_ids': [(4, x) for x in product_id.taxes_id.ids],
            }
            invoice_lines.append((0, 0, amimities_service_data))
        record = {
            'partner_id': self.booking_id.customer_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'move_type': 'out_invoice',
        }
        invoice_id = self.env['account.move'].sudo().create(record)
        self.booking_id.invoice_id = invoice_id.id

        if self.booking_id.is_any_agent:
            data = {
                'product_id': self.env.ref('pways_advance_hotel_management.agent_invoice').id,
                'name': 'Commission of ' + self.booking_id.booking_number + " Booking",
                'quantity': 1,
                'price_unit': self.booking_id.agent_commission,
            }
            agent_bill_line = [(0, 0, data)]
            agent = {
                'partner_id': self.booking_id.agent_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': agent_bill_line,
                'move_type': 'in_invoice',
            }
            bill_id = self.env['account.move'].sudo().create(agent)
            self.booking_id.agent_bill_id = bill_id.id

        template_id = self.env['ir.model.data']._xmlid_lookup('pways_advance_hotel_management.email_template_hotel_booking_check_out')[2]
        email_template_obj = self.env['mail.template'].sudo().browse(template_id)
        values = email_template_obj.generate_email(self.booking_id.id, ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
       
        values['attachment_ids'] = [Command.link(aid) for aid in values.get('attachment_ids', list())]
        attachment_ids = values.pop('attachment_ids', [])
        attachments = values.pop('attachments', [])

        values['email_from'] = super_user.partner_id.email
        values['email_to'] = self.booking_id.customer_id.email
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)

        # manage attachments
        for attachment in attachments:
            attachment_data = {
                'name': attachment[0],
                'datas': attachment[1],
                'type': 'binary',
                'res_model': 'mail.message',
                'res_id': msg_id.mail_message_id.id,
            }
            attachment_ids.append((4, Attachment.create(attachment_data).id))

        if attachment_ids:
            msg_id.write({'attachment_ids': attachment_ids})

        if msg_id:
            mail_mail_obj.send([msg_id])
        self.booking_id.check_in_booking_status()
