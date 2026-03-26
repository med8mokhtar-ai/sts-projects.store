from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    project_id = fields.Many2one('public.project', string="Projet")
    # In your sale.order model
    def action_open_project(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError(_("No project linked to this sale order."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'res_model': 'public.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    