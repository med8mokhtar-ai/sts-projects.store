from odoo import models, fields, api, exceptions


class ProjectFundingMode(models.Model):
    _name = 'project.funding_mode'
    _description = 'Project funding methods'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
