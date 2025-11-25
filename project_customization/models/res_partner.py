from odoo import models, fields, api,_

from odoo.exceptions import UserError, ValidationError


class resPartner(models.Model):
    _inherit = 'res.partner'

    count_projects = fields.Integer(string='Nombre des Projets',compute='action_count_projects', store=False)
    @api.model
    def action_count_projects(self):
        for record in self:
            record.count_projects = self.env['project.project'].search_count(['|','|',('titulaires', 'in', [record.id]),('commission_passation', '=', record.id),('autorite_contractante', '=', record.id)])
    
    full_description=fields.Char(string="Description")
    vat = fields.Char(string="NIF")


    

    def open_view_projects(self):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Projets',
                'res_model': 'project.project',
                'view_mode': 'kanban,tree,form,calendar,activity',
                'domain': ['|','|',('titulaires', 'in', [self.id]),('commission_passation', '=', self.id),('autorite_contractante', '=', self.id)],
                'context': {'create': False,}
            }
  