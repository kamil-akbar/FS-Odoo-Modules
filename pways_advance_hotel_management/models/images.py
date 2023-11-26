from odoo import fields, models, api

class HotelImage(models.Model):
	_name = 'hotel.image'
	_description = "Hotel Image"

	name = fields.Char(string="name", required=True)
	hall_image = fields.Binary(string="Hotel Hall Image")
	rest_image = fields.Binary(string="Hotel Restaurant Homepage Image")
	room_image = fields.Binary(string="Hotel Room Image")
	rest_image1 = fields.Binary(string="Hotel Restaurant Image1")
	rest_image2 = fields.Binary(string="Hotel Restaurant Image2")
	rest_image3 = fields.Binary(string="Hotel Restaurant Image3")
