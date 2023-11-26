from odoo import models, fields

class TermsAndConditions(models.Model):
    _name = 'terms.and.conditions'
    _description = 'Terms and Conditions'

    name = fields.Char(string='Title', required=True)
    content = fields.Text(string='Content', required=True)
