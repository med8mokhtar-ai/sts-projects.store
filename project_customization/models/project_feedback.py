from odoo import models, fields, api,Command,_
from odoo.tools import config
from collections import defaultdict
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError,UserError
from markupsafe import Markup

oui_no_selection=[('yes', 'OUI'), ('no', 'NO')]
projects_status=[('pre_reception', 'Pré-réception technique'), ('reception_pro', 'Réception provisoire'), ('reception_def', 'Réception définitive')]
class ProjectFeedback(models.Model):
    _name = 'project.feedback'
    _description = 'Mise à jour'

    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
    ]
    _mail_post_access = 'read'
    _order = "id desc"
    _primary_email = 'email_from'
    _systray_view = 'activity'
    _track_duration_field = 'state'
    
    name = fields.Char(string='Titre', tracking=True, required=True)
    feedback_date = fields.Date(string='Date de mise à jour',default=fields.Date.today(),tracking=True)
    # state = fields.Selection([('draft', 'Brouillon'), ('sent', 'Envoyé'), ('valide', 'Validé'), ('cancelled', 'Annulé')],default="draft")
    state = fields.Selection([('draft', 'Brouillon'), ('sent', 'Envoyé'), ('valide', 'Validé')],default="draft", string="Statut de validation",tracking=True,group_expand='_expand_states')
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self.sudo()).state.selection]
   
    project_id = fields.Many2one('project.project', string='Projet')
    company_id = fields.Many2one(related="project_id.company_id")
    currency_id = fields.Many2one(related='project_id.currency_id')
    numero_marche = fields.Char(string="Numéro du marché",related="project_id.numero_marche",store=True)
    # description = fields.Html(string='Qualité et Recommandations' , 
    #     default='''<div>
    #         <h4><strong>Qualité des travaux</strong></h4>
    #         <p><strong>Travaux géotechnique : tous les essais sont déclarés</strong><br/>
    #         conformes par la mission de contrôle</p>
    #         <p><strong>Topographie : toutes les quantités sont déclarés</strong><br/>
    #         conformes par la mission de contrôle.</p>
    #         <p><strong>Inspection visuelle des travaux effectuée par la</strong><br/>
    #         <strong>mission de suivi de la CNCMP : l'inspection visuelle</strong><br/>
    #         fait ressortir 02 observations visuelles des travaux.</p>
    #     </div>'''
    # )
    description = fields.Html(string='Qualité et Recommandations' , 
        default='''<div>
            <h4><strong>Qualité des travaux</strong></h4><br/>
            <p><strong>Travaux géotechnique</strong><br/>
             <p><strong>Inspection visuelle des travaux</strong><br/>
        </div>'''
    )
    montant_initial = fields.Monetary(currency_field='currency_id', string='Montant du marché', group_operator="sum",related="project_id.montant_initial",store=True)
    funding_mode_ids = fields.Many2many('project.funding_mode', string='Sources.Fin')
    titulaires = fields.Many2many('res.partner', string='Titulaire',  compute='_compute_titulaires', store=True)
    @api.depends('project_id.titulaires')
    def _compute_titulaires(self):
        for feedback in self.sudo():
            feedback.titulaires = feedback.project_id.titulaires
    autorite_contractante=fields.Many2one('res.partner',related="project_id.autorite_contractante",store=True)
    # bureau_de_suivi=fields.Many2one('res.partner', string='Bureau de suivi')
    # bureau_de_control=fields.Many2one('res.partner', string='Bureau de contrôle')
    date_signature = fields.Date(string='Date signature', tracking=True)
    date_notification = fields.Date(string='Date notification', tracking=True)
    date_noti_deb_ex = fields.Date(string='Date de notification de l’ordre du début de l’exécution', tracking=True)
    date_p_a_demarrage = fields.Date(string='Date de paiement avance de démarrage', tracking=True)
    date_mise_mission_c = fields.Date(string='Date de la mise en place de la mission de contrôle', tracking=True)
    date_remise_site = fields.Date(string='Date remise du site', tracking=True)
    date_entr_vig = fields.Selection([('date_signature', 'Signature'), ('date_notification', 'Notification'), ('date_remise_site', 'Remise du site'), ('date_noti_deb_ex', "Notification de l'ordre d'exécution"), ('date_p_a_demarrage', 'Paiement avance démarrage'),('date_mise_mission_c', 'Mission de contrôle'),('other_date','Autre')],string="Entrée en vigueur / Début d'exécution contractuel", tracking=True)
    other_date_description= fields.Char(string="Autre date à définir")
    other_date= fields.Date(string="Autre")
    project_debit_dec = fields.Float(string="Taux de Facturation", tracking=True)

    calculated_achievement = fields.Float(string='Avancement',group_operator="avg", tracking=True)
    avancement_prevue = fields.Float(string='Avancement Prévue',group_operator="avg", tracking=True)
    delai_consomme = fields.Float(string='Délai consommé',group_operator="avg",compute="_compute_delai_consomme",store=1, tracking=True)
    @api.depends('date_entr_vig', 'project_id.delai_execution_apres_avenant', 'feedback_date', 'project_id.reception_pro_date', 'project_id.last_update_consom_delai')
    def _compute_delai_consomme(self):
        for record in self:
            project=record.project_id
            if project.reception_pro_date:
                record.delai_consomme = project.last_update_consom_delai
            elif record.date_entr_vig and record[record['date_entr_vig']] and project.delai_execution_apres_avenant and record.feedback_date:
                record.delai_consomme=(record.feedback_date-record[record['date_entr_vig']]).days*100/ project.delai_execution_apres_avenant
            else:
               record.delai_consomme=project.delai_consomme
                
    anteced_ret_exec = fields.Selection(oui_no_selection,string='Antécédent ?', tracking=True)
    # retard_constate = fields.Integer(related="project_id.retard_constate",store=True, tracking=True)
    sous_traitance = fields.Selection(oui_no_selection,string='Sous traitance', tracking=True)
    sous_traitance_gap = fields.Float(string='% Montant Sous traitance', tracking=True)
    resiliation = fields.Selection(oui_no_selection,string='Résiliation', tracking=True)
    resiliation_date = fields.Date(string='Date résiliation', tracking=True)

    

    nationnalite_titulaire=fields.Many2one('res.country',string="Nationnalié titulaire ?", tracking=True)
    nationnalite_titulaire_project=fields.Many2one('res.country',related="project_id.nationnalite_titulaire",string="Nationnalié titulaire",store=True)
    project_status = fields.Selection(projects_status,string='Réception', tracking=True)
    status = fields.Selection(selection=[
        ('on_track', 'En bonne voie'),
        ('at_risk', 'Retard modéré à majeur'),
        ('off_track', 'Retard critique à catastrophique'),
        ('on_hold', 'Retard mineur'),
        ('to_define', 'À définir'),
        ('done', 'Fait'),
    ],string="Statut", tracking=True,compute="_compute_status")
    status_prevue = fields.Selection(selection=[
        ('on_track', 'En bonne voie'),
        ('at_risk', 'Retard modéré à majeur'),
        ('off_track', 'Retard critique à catastrophique'),
        ('on_hold', 'Retard mineur'),
        ('to_define', 'À définir'),
        ('done', 'Fait'),
    ],string="Statut avancement prévisionnel", tracking=True,compute="_compute_status_prevue")

    def action_view_task_history(self):
        self.ensure_one()
        # Determine which views to use based on project template
        if self.project_id.project_template_id:
            # Use the simplified views (second set in your XML)
            form_view_ref = 'project_customization.view_task_realisee_form_simplified'
            tree_view_ref = 'project_customization.view_task_realisee_tree_simplified'
        else:
            # Use the full views (first set in your XML)
            form_view_ref = 'project_customization.view_task_realisee_form'
            tree_view_ref = 'project_customization.view_task_realisee_tree'
        
        # Get the view IDs
        form_view_id = self.env.ref(form_view_ref).id
        tree_view_id = self.env.ref(tree_view_ref).id
        
        return {
            'name': 'Tâches',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'task.realisee',
            'domain': [('milestone_id.project_id', '=', self.project_id.id), 
                    ('station_date', '=', self.feedback_date)],
            'context': {
                'create': False,
            },
            'target': 'current',
        }

    @api.depends('delai_consomme', 'calculated_achievement')
    def _compute_status(self):
        for feedback in self:
            if feedback.calculated_achievement >= 100:
                feedback.status = 'done'  # Statut = « Fait »
            else:
                delay_percentage = (feedback.delai_consomme - feedback.calculated_achievement)

                if delay_percentage <= 0:
                    feedback.status = 'on_track'  # Pas de retard
                elif 0 < delay_percentage <= 10:
                    feedback.status = 'on_hold'  # Retard mineur
                elif 10 < delay_percentage <= 50:
                    feedback.status = 'at_risk'  # Retard modéré à majeur
                # elif 50 < delay_percentage <= 100:
                elif 50 < delay_percentage:
                    feedback.status = 'off_track'  # Retard critique à catastrophique
                else:
                    feedback.status = 'to_define'  # À définir
    @api.depends('calculated_achievement', 'avancement_prevue')
    def _compute_status_prevue(self):
        for feedback in self:
            delay_percentage = (feedback.avancement_prevue - feedback.calculated_achievement)
            # if feedback.avancement_prevue >= 100:
            #     feedback.status_prevue = 'done'  # Statut = « Fait »
            # else:
            if delay_percentage <= 0:
                feedback.status_prevue = 'on_track'  # Pas de retard
            elif 0 < delay_percentage <= 10:
                feedback.status_prevue = 'on_hold'  # Retard mineur
            elif 10 < delay_percentage <= 50:
                feedback.status_prevue = 'at_risk'  # Retard modéré à majeur
            # elif 50 < delay_percentage <= 100:
            elif 50 < delay_percentage:
                feedback.status_prevue = 'off_track'  # Retard critique à catastrophique
            else:
                feedback.status_prevue = 'on_track'  # À définir
    # def action_recompute_status(self):
    #     for record in self.search([]):
    #         record._compute_status()
    #         record.write({'status': record.status})
    # def _compute_status(self):
    #     for feedback in self:
    #         if feedback.calculated_achievement >= 100:
    #             feedback.status = 'done'  # Statut = «Réceptionné»
    #         elif feedback.delai_consomme >= 100:
    #             feedback.status = 'off_track'  # Statut = «En Retard»
    #         elif (feedback.delai_consomme - feedback.calculated_achievement) < 11:
    #             feedback.status = 'on_track'  # Statut = «En bonne voie»
    #         elif (feedback.delai_consomme - feedback.calculated_achievement) >= 11 and (feedback.delai_consomme - feedback.calculated_achievement) < 30:
    #             feedback.status = 'on_hold'  # Statut = «A Suivre»
    #         elif (feedback.delai_consomme - feedback.calculated_achievement) >= 30 and (feedback.delai_consomme - feedback.calculated_achievement) < 70:
    #             feedback.status = 'at_risk'  # Statut = «En Danger»
    #         elif (feedback.delai_consomme - feedback.calculated_achievement) >= 70:
    #             feedback.status = 'off_track'  # Statut = «En Retard»

    #         # else:
    #         #     feedback.status='on_hold'

    pre_reception_date = fields.Date(string='Date pré-réception technique', tracking=True)
    reception_pro_date = fields.Date(string='Date réception provisoire', tracking=True)
    reception_def_date = fields.Date(string='Date réception définitive', tracking=True)
    market_type_id = fields.Many2one(string="Type du marché", store=True, related='project_id.market_type_id')


    

    display_in_project = fields.Boolean(default=True, readonly=True)
    color = fields.Integer(string='Color Index')
    @api.model
    def open_my_projects(self):
        # Redirect to "/my/projects" URL
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/projects',
             # 'target': 'self', Open in the same tab
        }
            
    @api.depends_context('company')
    @api.depends('company_id')
    def _compute_currency_id(self):
        default_currency_id = self.env.company.currency_id
        for project in self:
            project.currency_id = project.company_id.currency_id or default_currency_id
    



    attachment_number = fields.Integer('Nombre de pièces jointes', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        totals =dict(
            self.env['ir.attachment'].sudo()._read_group(
            [('res_model', '=', 'project.feedback'), ('res_id', 'in', self.ids)],
            groupby=['res_id'],
            aggregates=['id:count'],
            )
        )
        
        self.attachment_number = totals.get(self.id) or 0

    percentage_conf_personnels = fields.Float(string="Conformité du personnel")
    percentage_conf_materiel = fields.Float(string="Conformité du matériel")
    

    def action_sent(self):
        feedback_sudo = self.sudo()
        feedback_sudo.activity_unlink(["project_customization.mail_activity_data_feedback"])  # Close open activities
        if not feedback_sudo.attachment_number:
            raise UserError("Vous devez joindre au moins un document vérifiant l'état d'avancement du projet.")
        feedback_sudo.write({'state': 'sent'})
        # Notify relevant users
        if feedback_sudo.project_id.user_id:
            notification_message = f"Un document de mise à jour est envoyé pour le projet: {feedback_sudo.project_id.name}."
            feedback_sudo.activity_schedule(
                activity_type_id=feedback_sudo.env.ref("project_customization.mail_activity_data_feedback").id,
                summary=notification_message,
                user_id=feedback_sudo.project_id.user_id.id,
                date_deadline=fields.Date.today())
        
    

    def action_back_to_draft(self):
        feedback_sudo = self.sudo()
        feedback_sudo.activity_unlink(["project_customization.mail_activity_data_feedback"])  # Close open activities
        feedback_sudo.write({'state': 'draft'})
        # Optionally, you can notify or perform other actions on state change
        if feedback_sudo.autorite_contractante:
            notification_message = f"Le mise à jour du projet {feedback_sudo.project_id.name} a été rétabli en 'Brouillon'."
            feedback_sudo.sudo().activity_schedule(
                act_type_xmlid='project_customization.mail_activity_data_feedback',
                user_id=feedback_sudo.autorite_contractante.user_id.id,  # Assuming the `autorite_contractante` has a user_id
                summary=notification_message,
                date_deadline=fields.Date.today()
            )
        # Notify the user that the feedback has been reverted to draft state
        

    def action_confirm(self):

        self.ensure_one()
        feedback_sudo = self.sudo()
        feedback_sudo.activity_unlink(["project_customization.mail_activity_data_feedback"])  # Close open activities
        project= feedback_sudo.project_id
        project.partner_id.write({'country_id':feedback_sudo.nationnalite_titulaire if feedback_sudo.nationnalite_titulaire else project.nationnalite_titulaire})

        project.write({
            # 'bureau_de_suivi': feedback_sudo.bureau_de_suivi if feedback_sudo.bureau_de_suivi else project.bureau_de_suivi,
            # 'bureau_de_control': feedback_sudo.bureau_de_control if feedback_sudo.bureau_de_control else project.bureau_de_control,
            # 'calculated_achievement': feedback_sudo.calculated_achievement if feedback_sudo.calculated_achievement else project.calculated_achievement,
            'date_entr_vig': feedback_sudo.date_entr_vig if feedback_sudo.date_entr_vig else project.date_entr_vig,
            'date_signature': feedback_sudo.date_signature if feedback_sudo.date_signature else project.date_signature,
            'date_notification': feedback_sudo.date_notification if feedback_sudo.date_notification else project.date_notification,
            'date_noti_deb_ex': feedback_sudo.date_noti_deb_ex if feedback_sudo.date_noti_deb_ex else project.date_noti_deb_ex,
            'date_p_a_demarrage': feedback_sudo.date_p_a_demarrage if feedback_sudo.date_p_a_demarrage else project.date_p_a_demarrage,
            'date_mise_mission_c': feedback_sudo.date_mise_mission_c if feedback_sudo.date_mise_mission_c else project.date_mise_mission_c,
            'date_remise_site': feedback_sudo.date_remise_site if feedback_sudo.date_remise_site else project.date_remise_site,
            'funding_mode_ids': feedback_sudo.funding_mode_ids if feedback_sudo.funding_mode_ids else project.funding_mode_ids,
            'anteced_ret_exec': feedback_sudo.anteced_ret_exec if feedback_sudo.anteced_ret_exec else project.anteced_ret_exec,
            'sous_traitance': feedback_sudo.sous_traitance if feedback_sudo.sous_traitance else project.sous_traitance,
            'resiliation': feedback_sudo.resiliation if feedback_sudo.resiliation else project.resiliation,
            'resiliation_date':feedback_sudo.resiliation_date if feedback_sudo.resiliation_date else project.resiliation_date,
            'sous_traitance_gap':feedback_sudo.sous_traitance_gap if feedback_sudo.sous_traitance_gap else project.sous_traitance_gap,
            'project_status':feedback_sudo.project_status if feedback_sudo.project_status else project.project_status,
            'pre_reception_date':feedback_sudo.pre_reception_date if feedback_sudo.pre_reception_date else project.pre_reception_date,
            'reception_pro_date':feedback_sudo.reception_pro_date if feedback_sudo.reception_pro_date else project.reception_pro_date,
            'reception_def_date':feedback_sudo.reception_def_date if feedback_sudo.reception_def_date else project.reception_def_date,
            # 'last_update_date':feedback_sudo.feedback_date if feedback_sudo.feedback_date else project.last_update_date,
            # 'last_update_consom_delai':feedback_sudo.delai_consomme if feedback_sudo.delai_consomme else project.last_update_consom_delai,
            'update_ids': [
                Command.create({
                    'name': 'Mise à jour du :',
                    'date': feedback_sudo.feedback_date,
                    'user_id': feedback_sudo.env.user.id,
                    'status': feedback_sudo.status,
                    'categorie_id': feedback_sudo.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect').id,
                    'state': 'valide',
                    'measure': 'calculated_achievement',
                    'new_value': feedback_sudo.calculated_achievement,
                    'old_value': feedback_sudo.env['project.update'].search([
                        ('project_id', '=', feedback_sudo.project_id.id),
                        ('measure', '=', 'calculated_achievement'),
                    ], order='date desc', limit=1).new_value or project.calculated_achievement,
                }),
                Command.create({
                    'name': 'Mise à jour du :',
                    'date': feedback_sudo.feedback_date,
                    'user_id': feedback_sudo.env.user.id,
                    'status': feedback_sudo.status,
                    'categorie_id': feedback_sudo.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect').id,
                    'state': 'valide',
                    'measure': 'project_debit_dec',
                    'new_value': feedback_sudo.project_debit_dec,
                    'old_value': feedback_sudo.env['project.update'].search([
                        ('project_id', '=', feedback_sudo.project_id.id),
                        ('measure', '=', 'project_debit_dec'),
                    ], order='date desc', limit=1).new_value or project.project_debit_gap,
                }),
                Command.create({
                    'name': 'Mise à jour du :',
                    'date': feedback_sudo.feedback_date,
                    'user_id': feedback_sudo.env.user.id,
                    'status': feedback_sudo.status,
                    'categorie_id': feedback_sudo.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect').id,
                    'state': 'valide',
                    'measure': 'rapport_delais',
                    'new_value': feedback_sudo.delai_consomme,
                    'old_value': feedback_sudo.env['project.update'].search([
                        ('project_id', '=', feedback_sudo.project_id.id),
                        ('measure', '=', 'rapport_delais'),
                    ], order='date desc', limit=1).new_value or project.last_update_consom_delai,
                }),
                Command.create({
                        'name': 'Mise à jour du :',
                        'date': feedback_sudo.feedback_date,
                        'user_id': feedback_sudo.env.user.id,
                        'status': feedback_sudo.status,
                        'categorie_id': feedback_sudo.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect').id,
                        'state': 'valide',
                        'measure': 'percentage_conf_personnels',
                        'new_value': feedback_sudo.percentage_conf_personnels,
                        'old_value': self.env['project.update'].search([
                            ('project_id', '=', feedback_sudo.project_id.id),
                            ('measure', '=', 'percentage_conf_personnels'),
                        ], order='date desc', limit=1).new_value or feedback_sudo.percentage_conf_personnels,
                    }),
                    Command.create({
                        'name': 'Mise à jour du :',
                        'date': feedback_sudo.feedback_date,
                        'user_id': feedback_sudo.env.user.id,
                        'status': feedback_sudo.status,
                        'categorie_id': feedback_sudo.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect').id,
                        'state': 'valide',
                        'measure': 'percentage_conf_materiel',
                        'new_value': feedback_sudo.percentage_conf_materiel,
                        'old_value': self.env['project.update'].search([
                            ('project_id', '=', feedback_sudo.project_id.id),
                            ('measure', '=', 'percentage_conf_materiel'),
                        ], order='date desc', limit=1).new_value or feedback_sudo.percentage_conf_materiel,
                    }),
            ],

        })
        # Perform other actions

        feedback_sudo.write({'state': 'valide'})
        # Optionally, you can send a notification or perform additional actions
        
        if feedback_sudo.autorite_contractante:
            email_body = Markup(
                "<div class='o_mail_notification o_hide_author'>"
                f"Veuillez être informé que votre mise à jour <b>{feedback_sudo.name}</b> du "
                f"<b>{feedback_sudo.project_id.name}</b> a été confirmée et validée.</div>"
            )
            feedback_sudo.autorite_contractante.message_post(
                body=email_body,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                partner_ids=feedback_sudo.autorite_contractante.user_ids.mapped('partner_id').ids,
            )
        
    def unlink(self):

        for record in self:
            if record.state in ['sent','valide']:
                raise ValidationError(_("Vous ne pouvez pas supprimer une mise à jour à l'état de validation et d'envoi."))
        res = super(ProjectFeedback, self).unlink()
        return res