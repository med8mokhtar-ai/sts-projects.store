from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.safe_eval import datetime
from markupsafe import Markup


class MilestoneCustom(models.Model):
    _inherit = 'project.milestone'
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related="project_id.company_id",
    )


    currency_id = fields.Many2one(
        related="company_id.currency_id",store=True,
        string="Currency",
    )
    numero_marche = fields.Char(string="Numéro du marché",related="project_id.numero_marche",store=True)
    autorite_contractante=fields.Many2one('res.partner',related="project_id.autorite_contractante",store=True)
    titulaires = fields.Many2many('res.partner', string='Titulaire',  compute='_compute_titulaires', store=True)
    @api.depends('project_id.titulaires')
    def _compute_titulaires(self):
        for m in self.sudo():
            m.titulaires = m.project_id.titulaires
    market_type_id = fields.Many2one(string="Type du marché", store=True, related='project_id.market_type_id')
    funding_mode_ids = fields.Many2many('project.funding_mode', string='Sources de Financement',related="project_id.funding_mode_ids")
    date = fields.Date(string="Date",tracking=True,required=True,default=fields.Date.today())
    montant_initial = fields.Monetary(currency_field='currency_id', string='Montant du marché', group_operator="sum",related="project_id.montant_initial",store=True)
    
    date_start = fields.Date(string='Date début')
    date_end = fields.Date(string='Date fin')
    planned_weight = fields.Float(string='Pondération', store=True,tracking=True)
    cumulated_weight = fields.Float(string='Réalisation cumulé', store=True,tracking=True, readonly=True, group_operator="sum")
    effectif_rate = fields.Float(string='Réalisation', tracking=True)
    gap = fields.Float(string='Ecart de réalisation', default=0.0, store=True, tracking=True, readonly=True, group_operator=False)
    
    color = fields.Integer(string='Color Index')

    
    state = fields.Selection([('draft', 'Brouillon'), ('sent', 'Envoyé'), ('valide', 'Validé')],default="draft", string="Statut",group_expand='_expand_states')
    
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self.sudo()).state.selection]
    attachment_number = fields.Integer('Nombre de pièces jointes', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        totals =dict(
            self.env['ir.attachment'].sudo()._read_group(
            [('res_model', '=', 'project.milestone'), ('res_id', 'in', self.ids)],
            groupby=['res_id'],
            aggregates=['id:count'],
            )
        )
        self.attachment_number = totals.get(self.id) or 0
        
    activity_user_id = fields.Many2one('res.users', 'Responsable activite', related='project_id.user_id')
    

    def _delete_activity(self):
        """Deletes related activities for the milestone."""
        activity_type = self.env.ref("project_customization.mail_activity_data_feedback", raise_if_not_found=False)
        if activity_type:
            self.env["mail.activity"].sudo().search([
                ('res_model', '=', 'project.milestone'),
                ('res_id', 'in', self.ids),
                ('activity_type_id', '=', activity_type.id),
            ]).unlink()

    def _create_activity(self, user_id, summary):
        """Creates a new activity for the milestone."""
        activity_type = self.env.ref("project_customization.mail_activity_data_feedback", raise_if_not_found=False)
        if activity_type:
            self.env["mail.activity"].sudo().create({
                'res_id': self.id,
                'res_model_id': self.env["ir.model"].sudo().search([('model', '=', 'project.milestone')]).id,
                'user_id': user_id,
                'summary': summary,
                'activity_type_id': activity_type.id,
                'date_deadline': datetime.date.today(),
            })


    @api.depends('planned_weight', 'effectif_rate')
    def _compute_cumulated_weight(self):
        for record in self:
            record.cumulated_weight=(record.planned_weight)*(record.effectif_rate/100)
            record.is_reached=(record.effectif_rate==100 )or False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('date_end') and not vals.get('deadline'):
                vals['deadline'] = vals['date_end']
        return super(MilestoneCustom, self).create(vals_list)
    
    
    @api.constrains('date_start', 'date_end')
    def _check_milestone_dates(self):
        project = self.project_id
        if self.date_start > self.date_end:
            raise ValidationError(
                "La date de début du jalon %s doit être inférieure à la date de fin prévue" % self.name)
        if project.date_start and project.date:
            if self.date_start and self.date_end and ((self.date_start < project.date_start) or (self.date_end > project.date)):
                raise ValidationError(
                    "Les dates planifiées du jalon doivent être comprises dans les dates planifiées du projet  %s, %s" % (project.date_start, project.date))


    
    pourcentage_realise = fields.Float(string="Pourcentage d’avancement physique valorisé", compute="_compute_pourcentage_realise", store=True, group_operator="avg")
    montant_jalon = fields.Float(string="Montant du jalon", compute="_compute_montant_jalon")
    montant_realise = fields.Float(string="Montant de l’avancement physique valorisé", compute="_compute_montant_realise")
    pourcentage_prevue_realise = fields.Float(string="Pourcentage d’avancement prévu", compute="_compute_pourcentage_prevue_realise")
    montant_prevue_realise = fields.Float(string="Montant Prévu", compute="_compute_montant_prevue_realise")
    station_date = fields.Date(string="Date de la situation")
    


    @api.depends('montant_prevue_realise', 'task_ids.percentage', 'task_ids.montant_prevue')
    def _compute_pourcentage_prevue_realise(self):
        for milestone in self:
            if milestone.montant_prevue_realise > 0:
                milestone.pourcentage_prevue_realise = milestone.montant_prevue_realise * 100 / milestone.project_id.budget
            else:
                # Calculate the sum of each task's percentage multiplied by the ratio of consumed days to planned days
                total_montant_prevue = sum(task.montant_prevue for task in milestone.task_ids if task.montant_prevue)
                milestone.pourcentage_prevue_realise = (total_montant_prevue * 100) / milestone.project_id.budget

    @api.depends('task_ids.quantite_prevue', 'task_ids.unit_price')
    def _compute_montant_prevue_realise(self):
        for milestone in self:
            if milestone.task_ids:
                milestone.montant_prevue_realise = sum(task.quantite_prevue * task.unit_price for task in milestone.task_ids)
            else:
                milestone.montant_prevue_realise = 0.0
                
    @api.depends('task_ids.montant_realise')
    def _compute_montant_realise(self):
        for milestone in self:
            total_tasks = len(milestone.task_ids)
            if total_tasks > 0:
                milestone.montant_realise = sum(milestone.task_ids.mapped('montant_realise'))
            else:
                milestone.montant_realise = 0.0

    @api.depends('montant_realise', 'project_id.budget', 'task_ids.pourcentage_realise', 'task_ids.percentage')
    def _compute_pourcentage_realise(self):
        for milestone in self:
            total_tasks = len(milestone.task_ids)
            project_montant = milestone.project_id.budget or 0.0
            if total_tasks > 0 and milestone.montant_realise and project_montant > 0:
                milestone.pourcentage_realise = milestone.montant_realise * 100 / project_montant
            elif total_tasks > 0:
                # sum task percentages safely
                total_percentage = sum(
                    (task.percentage or 0.0) * ((task.pourcentage_realise or 0.0) / 100)
                    for task in milestone.task_ids
                )
                milestone.pourcentage_realise = total_percentage or 0.0
            else:
                milestone.pourcentage_realise = 0.0


    @api.depends('task_ids.total_price')
    def _compute_montant_jalon(self):
        for milestone in self:
            total_tasks = len(milestone.task_ids)
            if total_tasks > 0:
                milestone.montant_jalon = sum(milestone.task_ids.mapped('total_price'))
            else:
                milestone.montant_jalon = 0.0
    def unlink(self):
        for record in self:
            if record.state in ['sent','valide']:
                raise ValidationError(_("Vous ne pouvez pas supprimer un jalon à l'état de validation et d'envoi."))
        return super().unlink()
    percentage = fields.Float(string='Pourcentage', compute="_compute_percentage", group_operator="avg")
    @api.depends('task_ids.percentage')
    def _compute_percentage(self):
        for record in self: 
            record.percentage = sum(record.task_ids.mapped('percentage'))
    sequence = fields.Char(string="Sequence")

    @api.constrains('percentage')
    def _check_percentage(self):
        for record in self:
            if record.percentage != 100:
                raise ValidationError("Le pourcentage total doit être exactement égal à 100.")
    
    def action_save(self):
        """Save task snapshots for milestone at current station date"""
        self.ensure_one()
        if not self.station_date:
            raise UserError(_("Date de situation requise avant sauvegarde"))
        # Check for existing situations (including those in current transaction)
        existing_count = self.env['task.realisee'].search_count([
            ('milestone_id', '=', self.id),
            ('station_date', '=', self.station_date)
        ])
        
        if existing_count > 0:
            raise UserError(
                _("Une situation existe déjà pour la date %s. Veuillez choisir une autre date.") 
                % self.station_date.strftime('%d/%m/%Y')
            )
        # Field mapping for task snapshot
        task_fields = {
            'percentage', 'num_poste', 'unit', 'unit_price', 'total_price',
            'dao_a_realiser', 'realisee', 'montant_realise', 'reste_a_realiser',
            'pourcentage_realise', 'date_debut', 'date_fin', 'consumed_months',
            'rendement_mensuel', 'quantite_prevue', 'montant_prevue'
        }

        # Prepare and create snapshots in bulk
        snapshots = [{
            'milestone_id': self.id,
            'task_id': task.id,
            'station_date': self.station_date,
            'state': 'valid',
            **{field: task[field] for field in task_fields}
        } for task in self.task_ids]

        created_records = self.env['task.realisee'].sudo().create(snapshots)

        # Update state if in draft
        if self.state == 'draft':
            self.state = 'sent'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sauvegarde réussie'),
                'message': _("%d tâches sauvegardées (%s)") % (
                    len(created_records),
                    self.station_date.strftime('%d/%m/%Y')
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
    
    def action_view_task_history(self):
        self.ensure_one()
        # Determine which views to use based on project template
        if self.project_id.project_template_id:
            # Use the simplified views
            form_view_ref = 'project_customization.view_task_realisee_form_simplified'
            tree_view_ref = 'project_customization.view_task_realisee_tree_simplified'
            graph_view_ref = 'project_customization.view_task_realisee_graph_simplified'
        else:
            # Use the full views
            form_view_ref = 'project_customization.view_task_realisee_form'
            tree_view_ref = 'project_customization.view_task_realisee_tree'
            graph_view_ref = 'project_customization.view_task_realisee_graph_simplified'
        
        # Get the view IDs
        form_view_id = self.env.ref(form_view_ref).id
        tree_view_id = self.env.ref(tree_view_ref).id
        graph_view_id = self.env.ref(graph_view_ref).id
        
        return {
            'name': 'Historique des tâches',
            'type': 'ir.actions.act_window',
            'view_mode': 'graph,tree,form',
            'views': [
                (graph_view_id, 'graph'),
                (tree_view_id, 'tree'), 
                (form_view_id, 'form')
            ],
            'res_model': 'task.realisee',
            'domain': [('milestone_id', '=', self.id)],
            'context': {
                'default_milestone_id': self.id,
                'group_by': ['task_id', 'station_date:day', 'pourcentage_realise'],
                'create': False,
            },
            'target': 'current',
        }
