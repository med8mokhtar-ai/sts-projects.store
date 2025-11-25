from odoo import models, fields


class ProjectHandlingMode(models.Model):
    _name = 'project.handling_mode'
    _description = 'Project handling modes'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
