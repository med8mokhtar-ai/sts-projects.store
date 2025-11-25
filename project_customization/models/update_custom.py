from odoo import models, fields, api, exceptions
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
class UpdateCustom(models.Model):
    _inherit = 'project.update'

    
    autorite_contractante = fields.Many2one('res.partner', string="Autorité contractante", store=True, related='project_id.autorite_contractante')
    titulaires = fields.Many2many('res.partner', string='Titulaire',  compute='_compute_titulaires', store=True)
    @api.depends('project_id.titulaires')
    def _compute_titulaires(self):
        for u in self.sudo():
            u.titulaires = u.project_id.titulaires
    partner_id = fields.Many2one('res.partner', tracking=False)
    market_type_id = fields.Many2one('project.market_type', string="Type du marché", store=True, related='project_id.market_type_id')
    currency_id = fields.Many2one(related="project_id.currency_id")
    montant_initial = fields.Monetary(currency_field='currency_id', string='Montant du marché', group_operator="avg",related="project_id.montant_initial",store=True)
    numero_marche = fields.Char(string="Numéro du Marché",related="project_id.numero_marche",store=True)
    
    
    measure = fields.Selection([
        ('calculated_achievement', 'Avancement'),
        ('project_debit_dec', 'Décaissement'),
        ('rapport_delais', 'Délai consommé'),
        ('percentage_conf_personnels', 'Conformité de personnels'),
        ('percentage_conf_materiel', 'Conformité de matériel'),
        ('observation_number', 'Noombre des observations')
    ], string="Mesure")
    new_value = fields.Float(string="Nouvelle Valeur",group_operator="avg")
    old_value = fields.Float(string="Anciennne Valeur",group_operator="avg")  

    difference = fields.Float(string="Difference",compute="_compute_difference",store=True,group_operator="avg")
    @api.depends('new_value','old_value')
    def _compute_difference(self):
        for update in self:
            update.difference=update.new_value-update.old_value
    # graph_date = fields.Char(string='Graph Date', readonly=True,
    #                          compute='_compute_graph_date', store=True)
    state = fields.Selection(
        [('draft', 'Brouillon'), ('sent', 'Provisoire'), ('valide', 'Validé')],
        string='Statut', default='draft', tracking=True, readonly=True)
    categorie_id = fields.Many2one('abc.exp.besoin.categorie', string="Categorie")
    reception_type=fields.Selection([('receipt_subject_to_reservation', 'Réception sous réserve'), ('reception_without_reservation','Réception sans réserve'), ('receipt_with_reservation', 'Réception avec réserve')],string='Type de reception')
    def action_back_to_draft(self):
        for record in self:
            if record.state in ["sent"]:
                record.write({'state':'draft'})

    def action_confirm(self):
        for record in self:
            if record.state in ["draft"]:
                record.write({'state':'sent'})

    def action_validate(self):
        for record in self:
            if record.state in ["sent"]:
                record.write({'state':'valide'})
            # if record.date and record.project_id:
            #    record.project_id.last_update_date=record.date
            #    record.project_id.last_update_consom_delai=record.delai_consomme
            if record.reception_type in ['reception_without_reservation','receipt_with_reservation']:
                self.env['project.task'].create({'name': 'Réception définitive du %s'%record.project_id.name, 'project_id': record.project_id.id,'user_ids':[record.project_id.user_id.id],'date_deadline':(record.date + relativedelta(years=1))})
    