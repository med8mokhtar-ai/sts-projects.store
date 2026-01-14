from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    project_id = fields.Many2one('public.project', string="Projet")
    
    