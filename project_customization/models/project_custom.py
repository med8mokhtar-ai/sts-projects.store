from odoo import models, fields, api, _
from collections import defaultdict
from datetime import datetime, timedelta
from odoo.exceptions import UserError
# import PyPDF2
import html2text
from io import BytesIO
from base64 import b64encode, b64decode
import qrcode
import hashlib
# import re
# import io
# import pdfplumber
# import unicodedata

oui_no_selection = [('yes', 'OUI'), ('no', 'NO')]

ADDRESS_FIELDS = ('city', 'state_id', 'country_id')


class ProjectCustom(models.Model):
    _inherit = 'project.project'
    _rec_name ='numero_marche'
    _rec_names_search = ['numero_marche', 'name']
    def _compute_attached_docs_count(self):
        docs_count = {}
        if self.ids:
            self.env.cr.execute(
                """
                WITH docs AS (
                    SELECT res_id as id, count(*) as count
                    FROM ir_attachment
                    WHERE (res_model = 'project.project'
                        AND res_id IN %(project_ids)s)
                        OR (res_model = 'project.avenant'
                        AND res_id IN %(avenant_ids)s)
                        OR (res_model = 'project.feedback'
                        AND res_id IN %(feedback_ids)s)
                        OR (res_model = 'project.update'
                        AND res_id IN %(update_ids)s)
                        OR (res_model = 'account.analytic.line.project'
                        AND res_id IN %(analytic_line_project_ids)s)
                        OR (res_model = 'abc.exp.besoin.mission.projects'
                        AND res_id IN %(mission_ids)s)
                GROUP BY res_id
                )
                SELECT id, sum(count)
                FROM docs
            GROUP BY id
                """,
                {
                    "project_ids": tuple(self.ids) or tuple([0]), 
                    "avenant_ids": tuple(self.avenant_ids.ids) or tuple([0]),
                    "feedback_ids": tuple(self.feedbacks.ids) or tuple([0]),
                    "update_ids": tuple(self.update_ids.ids) or tuple([0]),
                    "mission_ids": tuple(self.mission_ids.ids) or tuple([0]),
                    "analytic_line_project_ids": tuple(self.financial_transaction_ids.ids) or tuple([0])
                }
            )
            docs_count = dict(self.env.cr.fetchall())
        for project in self:
            project.doc_count = int(sum(docs_count.values()))

    
    prerequisite = fields.Char(string='Prérequis')
    # stage_id = fields.Many2one(groups="project.group_project_stages,project.group_project_manager")
    # stage_name = fields.Char(string='Nom du stage', related='stage_id.name', store=True,readonly=False)
    stage_id = fields.Many2one(groups="project.group_project_stages,project.group_project_manager")
    
    # @api.model
    # def fields_get(self, allfields=None, attributes=None):
    #     fields = super().fields_get(allfields=allfields, attributes=attributes)

    #     # Bypass restrictions for admin users
    #     if self.env.user.has_group('project.group_project_manager'):
    #         return fields

    #     # Get the "Numbering" stage ID
    #     numbering_stage_id = self.env.ref('project.project_project_stage_0').id

    #     # Check if the project stage is "Numbering"
    #     if not any(rec.stage_id.id == numbering_stage_id for rec in self):
    #         # Set all fields to readonly
    #         for field_name, description in fields.items():
    #             description['readonly'] = True

    #         return fields

    #     # Return all fields if in "Numbering" stage
    #     return fields

    # tag_ids = fields.Many2many(readonly=lambda self:not self.user.has_group('base.group_system'), string="Catégorie")
    tag_ids = fields.Many2many(string="Catégorie")
    done_description = fields.Html(string="Description d'achèvement")
    user_id = fields.Many2one(string="Responsable de suivi")

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.sudo().stage_id == self.env.ref(
                'project_customization.project_project_stage_2') and self.sudo().market_type_id == self.env.ref(
                'project_customization.project_market_type_0'):
            # You can construct the HTML content here based on your requirements
            table_content = """
                <table class="table">
                    <tr style="margin: 0px; border: 2px solid black;">
                        <th style="margin: 0px; border: 2px solid black;">Désignation</th>
                        <th style="margin: 0px; border: 2px solid black;">Précision</th>
                        <th style="margin: 0px; border: 2px solid black;">Remarques</th>
                    </tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Consistances par ouvrage</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Etat</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Date d'occupation</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">DQE</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Métré/Surface</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Situation financière(décompte final)</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Spécifications techniques requises</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Avenant en plus ou en moins-value ou ajournement</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Défauts de structure/Fissures/Malfacons</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Résiliation</td><td style="margin: 0px; border: 2px solid black;">{}/{}</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Vérification des secondes oeuvres(Miniserie...)</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Pv de réception</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Assurence décennale</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Pv de réception définitive</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Caution de bonne exécution ou bonne fin</td><td style="margin: 0px; border: 2px solid black;">{} {}</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Respect du délai</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">État général du bâtiment</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>

                    
                </table>
                <hr/>
                <b>Conclusion Générale:</b>
                <table>
                <ul>
                <li/>
                <li/>
                <li/>
                </ul>
                </table>
                <hr/>
                <b>Signature:</b><br/>
            """.format(self.resiliation, self.resiliation_date, self.montant_total_cautions_bonne_ex,
                       self.montant_total_cautions_bon_fin)

            # Update the HTML field with the constructed HTML content
            self.done_description = table_content
        elif self.sudo().stage_id == self.env.ref(
                'project_customization.project_project_stage_2') and self.sudo().market_type_id == self.env.ref(
                'project_customization.project_market_type_1'):
            # You can construct the HTML content here based on your requirements
            table_content = """
                <table class="table">
                    <tr style="margin: 0px; border: 2px solid black;">
                        <th style="margin: 0px; border: 2px solid black;">Désignation</th>
                        <th style="margin: 0px; border: 2px solid black;">Précision</th>
                        <th style="margin: 0px; border: 2px solid black;">Remarques</th>
                    </tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Nature</td><td style="margin: 0px; border: 2px solid black;">Consistances par ouvrage</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Etat</td><td style="margin: 0px; border: 2px solid black;">Bon/Mauvais/Acceptable</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Fonctionnement</td><td style="margin: 0px; border: 2px solid black;">Oui/Non</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">DQE(Quantité)</td><td style="margin: 0px; border: 2px solid black;">Conformité au prévue?(Oui/Non)</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Utilisation</td><td style="margin: 0px; border: 2px solid black;">En stock/utilisé(décharge)</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Accessoires</td><td style="margin: 0px; border: 2px solid black;">(Oui/Non)</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Spécifications techniques requises</td><td style="margin: 0px; border: 2px solid black;">Conformité aux Spécifications(Oui/Non)</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Avenant en plus ou en moins-value ou ajournement</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Résiliation</td><td style="margin: 0px; border: 2px solid black;">{}/{}</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Pv de réception</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;">précision des réserves signalés, le cas échéant</td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Bordereau de livraison(destination finale)</td><td style="margin: 0px; border: 2px solid black;">Date/Signature</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Bon de commande</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Situation financière(décompte final)</td><td style="margin: 0px; border: 2px solid black;">{}</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Caution de bonne exécution ou bonne fin</td><td style="margin: 0px; border: 2px solid black;">{} {}</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Respect du délai</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">État général du bâtiment</td><td style="margin: 0px; border: 2px solid black;"></td><td style="margin: 0px; border: 2px solid black;"></td></tr>

                    
                </table>
                <hr/>
                <b>Conclusion Générale:</b>
                <table>
                <ul>
                <li/>
                <li/>
                <li/>
                </ul>
                </table>
                <hr/>
                <b>Signature:</b><br/>
            """.format(self.resiliation, self.resiliation_date, self.project_debit,
                       self.montant_total_cautions_bonne_ex, self.montant_total_cautions_bon_fin)

            # Update the HTML field with the constructed HTML content
            self.done_description = table_content
        elif self.sudo().stage_id == self.env.ref(
                'project_customization.project_project_stage_2') and self.sudo().market_type_id not in [
            self.env.ref('project_customization.project_market_type_0'),
            self.env.ref('project_customization.project_market_type_1')]:
            # You can construct the HTML content here based on your requirements
            table_content = """
                <table class="table">
                    <tr style="margin: 0px; border: 2px solid black;">
                        <th style="margin: 0px; border: 2px solid black;">Désignation</th>
                        <th style="margin: 0px; border: 2px solid black;">Précision</th>
                        <th style="margin: 0px; border: 2px solid black;">Remarques</th>
                    </tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Etat</td><td style="margin: 0px; border: 2px solid black;">Consistances par ouvrage</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Etat</td><td style="margin: 0px; border: 2px solid black;">Bon/Mauvais/Acceptable</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">Fonctionnement</td><td style="margin: 0px; border: 2px solid black;">Oui/Non</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    <tr style="margin: 0px; border: 2px solid black;"> <td style="margin: 0px; border: 2px solid black;">DQE(Quantité)</td><td style="margin: 0px; border: 2px solid black;">Conformité au prévue?(Oui/Non)</td><td style="margin: 0px; border: 2px solid black;"></td></tr>
                    
                    
                </table>
                <hr/>
                <b>Conclusion Générale:</b>
                <table>
                <ul>
                <li/>
                <li/>
                <li/>
                </ul>
                </table>
                <hr/>
                <b>Signature:</b><br/>
            """

            # Update the HTML field with the constructed HTML content
            self.done_description = table_content

    # Newly added fields
    # strategic_targets = fields.Char(string='Objectifs stratégiques', store=True)
    # specific_objectives = fields.Char(string='Objectifs spécifiques', store=True)
    # priority = fields.Selection([
    #     ('1', '3'),
    #     ('2', '2'),
    #     ('3', '1')], string='Classification des activités  ', tracking=True,
    #     index=True)
    # intervention_zone = fields.Char(string="Zone d'intervention", store=True)
    # referred_by = fields.Char(string='Référée par', store=True)

    project_indicators = fields.One2many('project.indicator', 'project_id', string="Indicateurs",
                                         help="Attachments that don't come from a message.")

    company_id = fields.Many2one(string='Structure')
    impacts = fields.Char(string='Impacts')
    risks = fields.Char(string='Risques')
    remarks = fields.Char(string='Remarques')

    handling_type = fields.Selection(
        [('PAA', 'Plan d’achat annuel (PAA)'), ('PPM', 'Plan de Passation de Marche (PPM)')],
        string='Type de passation')
    funding_mode_ids = fields.Many2many('project.funding_mode', string='Sources de financement')
    handling_mode_ids = fields.Many2many('project.handling_mode', string='Modes de passation')

    # alignment_ids = fields.One2many('strategy.alignment', 'project_id', string='Alignemnts strategiques')

    update_count = fields.Integer(string='Update Count', compute='_compute_update_count', store=True)
    feedbacks = fields.One2many('project.feedback', 'project_id', string='Mises à jour')
    feedback_count = fields.Integer(string='Nombres des mises à jour', compute='_compute_feedback_count', store=True)
    stop_stations = fields.One2many('project.stop.station', 'project_id', string='Arrêts')
    stop_station_count = fields.Integer(string='Nombres des arrêts d’exécution', compute='_compute_stop_station_count',
                                        store=True)
    
    tracking_count = fields.Integer(string='Tracking Count', compute='_compute_tracking_count', store=True)
    # Define the new computed fields
    status_collect = fields.Selection(
        selection=[
            ('on_track', 'En bonne voie'),
            ('at_risk', 'Retard modéré à majeur'),
            ('off_track', 'Retard critique à catastrophique'),
            ('on_hold', 'Retard mineur'),
            ('to_define', 'À définir'),
            ('done', 'Fait'),
        ],
        string="Statut Collecte",
        default='to_define',
        compute='_compute_collect_fields',
        store=True,
    )
    achievement_collect = fields.Float(string="Avancement Collecte", compute='_compute_collect_fields', store=True,group_operator="avg")
    decaissement_collect = fields.Float(string="Décaissement Collecte", compute='_compute_collect_fields', store=True,group_operator="avg")
    delai_consomme_collect = fields.Float(string="Délai Consommé Collecte", compute='_compute_collect_fields', store=True,group_operator="avg")
    date_derniere_mise_a_jour_collect = fields.Date(string="Date de la Dernière Mise à Jour Collecte", compute='_compute_collect_fields', store=True)

    @api.depends('update_ids.categorie_id')
    def _compute_collect_fields(self):
        for project in self:
            # Filter updates by the specific category
            categorie_id=self.sudo().env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect')
            updates = project.update_ids.filtered(lambda u: u.categorie_id == categorie_id).sorted('date', reverse=True)
            # Get the most recent update if available
            achievement = decaissement = delai_consomme = False
            
            if len(updates)>0:
                project.status_collect = updates[0].status
                project.date_derniere_mise_a_jour_collect = updates[0].date
                
                # Initialize variables to store the latest values for each field
                # Iterate through the updates and assign values based on the measure
                for update in updates:
                    if update.measure == 'calculated_achievement' and not achievement:
                        achievement = update.new_value
                        
                    elif update.measure == 'project_debit_dec' and not decaissement:
                        decaissement = update.new_value
                    elif update.measure == 'rapport_delais' and not delai_consomme:
                        delai_consomme = update.new_value
                # Assign the values to the fields only once
                project.achievement_collect = achievement
                project.decaissement_collect = decaissement
                project.delai_consomme_collect = delai_consomme
            else:
                project.status_collect = 'to_define'  # Default or fallback status
                project.date_derniere_mise_a_jour_collect=False


    numero_marche = fields.Char(string="Numéro du marché")
    _sql_constraints = [
        ('unique_numero_marche', 'unique (numero_marche)', "Le numéro de marché doit être unique."),
    ]
    description = fields.Html(string='Objet du Marché',
                              help="Description pour fournir plus d'informations et de contexte sur ce projet")

    commission_passation = fields.Many2one('res.partner', string='Commission de passation')
    autorite_contractante = fields.Many2one('res.partner', string='Autorité contractante')
    # bureau_de_suivi=fields.Many2one('res.partner', string='Bureau de suivi')
    # bureau_de_control=fields.Many2one('res.partner', string='Bureau de contrôle')
    market_type_id = fields.Many2one('project.market_type', string='Type du marché')
    market_type_name = fields.Char(related='market_type_id.name', string='Nom du marché')
    secteur_id = fields.Many2one('project.sector', string='Secteur')
    montant_initial = fields.Monetary(currency_field='currency_id', string='Montant initial', group_operator="sum")
    budget = fields.Monetary(string='Montant total (MRU)', currency_field='currency_id', compute="_compute_budget",
                             group_operator="sum", store=True, help="Montant initial + Avenants")
    regime_fiscal = fields.Selection([('ht', 'HT'), ('ttc', 'TTC')], string='Régime fiscal')
    credit_impot = fields.Monetary(currency_field='currency_id', string='crédit impot')

    delai_execution = fields.Integer(string='Délai execution (jours)',group_operator=False)
    # Ebnou notes
    delai_execution_apres_avenant = fields.Integer(string="Délai d'exécution actualisé (MI+AV)",
                                                   compute="_compute_delai_execution_apres_avenant")
    marches_control = fields.Many2many(
        'project.project',  # Target model
        'marches_control_rel',  # Relation table
        'project_id',  # Column representing current model
        'control_id',  # Column representing the target model
        string="Marchés de Contrôles")
    subprojects_count = fields.Integer("Nbr de Marchés de Contrôle", compute='_compute_subprojects_counts')
    est_un_marche_de_control = fields.Boolean("Est un Marché de Contrôle", default=False)

    @api.depends('marches_control')
    def _compute_subprojects_counts(self):
        for project in self:
            project.subprojects_count = len(project.marches_control)

    def action_open_sub_projects(self):
       # Define the context with the active_id
        self.ensure_one()
        context = {
            'default_marches_control': [(6, 0, [self.id])],
        }
        # Return the action
        return {
            'type': 'ir.actions.act_window',
            'name': 'Marchés de Contrôle',
            'res_model': 'project.project',
            'view_mode': 'tree,kanban,form,calendar,pivot,graph,activity',
            'domain': [('id', 'in',self.mapped('marches_control').ids)],
            'context': context,
        }
    # _____________________________________________________________________________________
    delai_consomme = fields.Integer(string='Délai consommé(jours)', compute="_compute_delai_consomme", store=True,group_operator=False)
    # rapport_delais = fields.Float(string='% Délai consommé', help="Délai consommé / delai_execution",
    #                               compute="_compute_rapport_delais", group_operator="avg", store=True)
    observation = fields.Html(help="Observation pour fournir des informations et un contexte sur ce projet.",
                              string='Observsation')
    date_signature = fields.Date(string='Date signature')
    date_notification = fields.Date(string='Date notification')
    date_noti_deb_ex = fields.Date(string='Date de notification de l’ordre du début de l’exécution')
    date_p_a_demarrage = fields.Date(string='Date de paiement avance de démarrage')
    # Ebnou notes
    date_mise_mission_c = fields.Date(string='Date de la mise en place de la mission de contrôle', tracking=True)
    # ____________________________________________________________________________________________________________
    date_remise_site = fields.Date(string='Date remise du site')
    date = fields.Date(index=True, tracking=True, store=True, compute="_compute_date",
                       help="Date à laquelle ce projet se termine. égale au délai d'exécution plus la date de signature.",
                       readonly=True)
    date_publication_avis = fields.Date(string='Date publication avis')
    date_ouverture_offres = fields.Date(string='Date ouverture des offres')
    date_evaluation_offres = fields.Date(string='Date évaluation des offres')
    date_attribution = fields.Date(string='Date attribution')
    date_start = fields.Date(compute="_compute_date_start",store=True)
    # Ebnou et aghrebett notes
    date_entr_vig = fields.Selection(
        [('date_signature', 'Signature'), ('date_notification', 'Notification'), ('date_remise_site', 'Remise du site'),
         ('date_noti_deb_ex', "Notification de l'ordre d'exécution"), ('date_p_a_demarrage', 'Paiement avance démarrage'),
         ('date_mise_mission_c', 'Mission de contrôle'),('other_date','Autre')], string="Entrée en vigueur / Début d'exécution contractuel")
    other_date_description= fields.Char(string="Autre date à définir")
    other_date= fields.Date(string="Autre")
    # __________________________________________________________________________________________________________________________________________
    
    calculated_achievement = fields.Float(string='Avancement mission', tracking=True, group_operator=False, compute='_compute_mission_fields', store=True)
    last_update_decaissement = fields.Float(string='Décaissement mission', compute='_compute_mission_fields', help="Décaissements / Globale", group_operator=False, store=True)
    last_update_consom_delai = fields.Float(string='Consommation du delai mission', compute='_compute_mission_fields', store=True,group_operator=False)
    last_update_status_mission = fields.Selection(string='dernière mise à jour du statut mission',selection=[
            ('on_track', 'On Track'),
            ('at_risk', 'At Risk'),
            ('off_track', 'Off Track'),
            ('on_hold', 'On Hold'),
            ('to_define', 'Set Status'),
            ('done', 'Done'),
        ],
        default='to_define', compute='_compute_mission_fields', store=True)
    percentage_conf_personnels = fields.Float(string="Conformité du personnel", compute='_compute_mission_fields', store=True,group_operator=False)
    percentage_conf_materiel = fields.Float(string="Conformité du matériel", compute='_compute_mission_fields', store=True,group_operator=False)
    observation_number = fields.Integer(string='Nombre des observations (anomalies)', compute='_compute_mission_fields', store=True,group_operator=False)
    last_update_date = fields.Date(string='date de la dernière mise à jour', compute='_compute_mission_fields', store=True)

    # @api.depends('update_ids.categorie_id')
    # def _compute_mission_fields(self):
    #     for project in self:
    #         # Get updates filtered by categories that are NOT "abc_exp_besoin.abc_exp_besoin_categorie_collect"
    #         updates = project.update_ids.filtered(
    #             lambda u: u.categorie_id != self.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect')
    #         ).sorted('date', reverse=True)
    #         achievement = decaissement = delai_consomme = personnels_conf = materiel_conf = qualite_travail = False
              
    #         if len(updates)>0: 
    #             project.last_update_status_mission = updates[0].status
    #             project.last_update_date = updates[0].date
                         
    #             # Initialize variables to store the latest values for each field
    #             # Iterate through the updates and assign values based on the measure
    #             for update in updates:
    #                 if update.measure == 'calculated_achievement' and not achievement:
    #                     achievement = update.new_value
    #                 elif update.measure == 'project_debit_dec' and not decaissement:
    #                     decaissement = update.new_value
    #                 elif update.measure == 'rapport_delais' and not delai_consomme:
    #                     delai_consomme = update.new_value
    #                 elif update.measure == 'percentage_conf_personnels' and not personnels_conf:
    #                     personnels_conf = update.new_value
    #                 elif update.measure == 'percentage_conf_materiel' and not materiel_conf:
    #                     materiel_conf = update.new_value
    #                 elif update.measure == 'observation_number' and not qualite_travail:
    #                     qualite_travail = update.new_value
    #         else:
    #             project.last_update_status_mission = 'to_define'  # Default or fallback status
    #             project.last_update_date=False
    #         # Assign the values to the fields only once
    #         project.calculated_achievement = achievement if achievement is not False else 0.0
    #         project.last_update_decaissement = decaissement if decaissement is not False else 0.0
    #         project.last_update_consom_delai = delai_consomme if delai_consomme is not False else 0.0
    #         project.percentage_conf_personnels = personnels_conf if personnels_conf is not False else 0.0
    #         project.percentage_conf_materiel = materiel_conf if materiel_conf is not False else 0.0
    #         project.observation_number = qualite_travail if qualite_travail is not False else 0.0
    @api.depends('update_ids.measure', 'update_ids.new_value', 'update_ids.date', 'update_ids.status', 'update_ids.categorie_id')
    def _compute_mission_fields(self):
        collect_ref = self.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect')
        
        for project in self:
            updates_all = project.update_ids.sorted('date', reverse=True)
            updates_filtered = updates_all.filtered(lambda u: u.categorie_id != collect_ref)

            # Most recent values
            get_latest = lambda updates, measure: next((u.new_value for u in updates if u.measure == measure), 0.0)

            # From filtered updates
            project.last_update_status_mission = updates_filtered[0].status if updates_filtered else 'to_define'
            project.last_update_date = updates_filtered[0].date if updates_filtered else False
            project.calculated_achievement = get_latest(updates_filtered, 'calculated_achievement')
            project.last_update_decaissement = get_latest(updates_filtered, 'project_debit_dec')
            project.last_update_consom_delai = get_latest(updates_filtered, 'rapport_delais')
            project.observation_number = get_latest(updates_filtered, 'observation_number')

            # From all updates
            project.percentage_conf_personnels = get_latest(updates_all, 'percentage_conf_personnels')
            project.percentage_conf_materiel = get_latest(updates_all, 'percentage_conf_materiel')

            
            
                                 
    last_update_status = fields.Selection(string="Statut")
    @api.depends('last_update_consom_delai', 'calculated_achievement')
    def _compute_last_update_status(self):
        for project in self:
            if len(project.update_ids.filtered(lambda u: u.categorie_id != self.env.ref('abc_exp_besoin.abc_exp_besoin_categorie_collect')))>0:
                if project.calculated_achievement >= 100:
                    project.last_update_status = 'done'  # Statut = «Réceptionné»
                elif project.last_update_consom_delai:
                    if project.last_update_consom_delai >= 100:
                        project.last_update_status = 'off_track'  # Statut = «En Retard»
                    elif (project.last_update_consom_delai - project.calculated_achievement) < 11:
                        project.last_update_status = 'on_track'  # Statut = «En bonne voie»
                    elif 11 <= (project.last_update_consom_delai - project.calculated_achievement) < 30:
                        project.last_update_status = 'on_hold'  # Statut = «A Suivre»
                    elif 30 <= (project.last_update_consom_delai - project.calculated_achievement) < 70:
                        project.last_update_status = 'at_risk'  # Statut = «En Danger»
                    elif (project.last_update_consom_delai - project.calculated_achievement) >= 70:
                        project.last_update_status = 'off_track'  # Statut = «En Retard»
            else:
                project.last_update_status = 'to_define'  # Default or fallback status
                

    stage_id = fields.Many2one('project.project.stage', string='Stage', compute='_compute_stage', store=True,readonly=False)
    # current_date = fields.Date(string="Current Date", compute='_compute_current_date', store=True)
    # def _compute_current_date(self):
    #     """Compute the current date."""
    #     for project in self:
    #         project.current_date = datetime.now().date()
    @api.depends('date_start', 'calculated_achievement','last_update_date')
    def _compute_stage(self):
        """Compute the stage of the project based on date_start and calculated_achievement."""
        for project in self:
            if project.calculated_achievement == 100:
                project.stage_id = self.env.ref('project_customization.project_project_stage_2').id  # Done
            elif project.calculated_achievement < 100 and project.date_start and project.last_update_date:
                if project.calculated_achievement < 100 and project.date_start and project.date_start <= project.last_update_date:
                    project.stage_id = self.env.ref('project.project_project_stage_1').id  # In Progress
            else:
                project.stage_id = self.env.ref('project.project_project_stage_1').id  # Numbering

    # lies avec les model en cours d'execution ,stored ne change pas
    montant_total_avenants = fields.Monetary(string='Avenants', currency_field='currency_id',
                                             compute="_compute_montant_total_avenants", store=True)
    montant_total_avenants_gap = fields.Float(string='% Avenants', compute="_compute_montant_total_avenants_gap",
                                              help="Avenant/Montant Initial", group_operator="avg", store=True)
    montant_total_ordre_services = fields.Monetary(string='Ordres de service', currency_field='currency_id',
                                                   compute="_compute_montant_total_ordre_services", store=True)
    montant_total_ordre_services_gap = fields.Float(string='% Ordres de service',
                                                    compute="_compute_montant_total_ordre_services_gap",
                                                    help="Ordre de service/Montant Initial", group_operator="avg",
                                                    store=True)
    montant_total_cautions_bonne_ex = fields.Monetary(string='Caution de B.Exéc', currency_field='currency_id',
                                                      compute="_compute_montant_total_cautions_bonne_ex", store=True)
    montant_total_cautions_bon_fin = fields.Monetary(string='Caution de B.Fin', currency_field='currency_id',
                                                     compute="_compute_montant_total_cautions_bon_fin", store=True)
    montant_total_cautions_bonne_ex_gap = fields.Float(string='% Caution de B.Exéc',
                                                       compute="_compute_montant_total_cautions_bonne_ex_gap",
                                                       help="Caution de B.Exéc/Montant total", group_operator="avg",
                                                       store=True)
    montant_total_cautions_bon_fin_gap = fields.Float(string='% Caution de B.Fin',
                                                      compute="_compute_montant_total_cautions_bon_fin_gap",
                                                      help="Caution de bon fin/Montant total", group_operator="avg",
                                                      store=True)
    montant_total_penalite = fields.Monetary(string='Pénalités de retard appliquées', currency_field='currency_id',
                                             compute="_compute_montant_total_penalite", store=True)
    montant_total_penalite_gap = fields.Float(string='% Pénalités de retard', compute="_compute_montant_total_penalite_gap",
                                               group_operator=False, store=True)
    montant_total_remise_penalite = fields.Monetary(string='Remise des pénalités', currency_field='currency_id',
                                                    compute="_compute_montant_total_remise_penalite", store=True)
    penalite_plafone = fields.Monetary(string='Pénalités de retard théoriques', currency_field='currency_id',
                                              compute="_compute_penalite_plafone", store=True)
                                              
    penalite_plafone_gap = fields.Float(string='% Pénalités de retard théoriques',
                                               compute="_compute_penalite_plafone_gap", group_operator=False,
                                               store=True)

    montant_total_remise_penalite_gap = fields.Float(string='% Remise des pénalités',
                                                     compute="_compute_montant_total_remise_penalite_gap", group_operator=False,
                                                     store=True)
    montant_total_avance_demarrage = fields.Monetary(string="Avance démarrage", currency_field='currency_id',
                                                     compute="_compute_montant_total_avance_demarrage", store=True)
    montant_total_avance_demarrage_gap = fields.Float(string="% Avance de démarrage",
                                                      compute="_compute_montant_total_avance_demarrage_gap",
                                                      help="Avance de démarrage/Montant Initial", group_operator="avg",
                                                      store=True)
    #Cheiger Notes
    montant_reimbursement_amount = fields.Monetary(string="Rembs Av Dem", currency_field='currency_id', compute="_compute_montant_reimbursement_amount", store=True, help="Remboursement Avance démarrage")
    montant_reimbursement_amount_gap = fields.Float(string="% Rembs Av Dem",
                                                      compute="_compute_montant_reimbursement_amount_gap",
                                                      help="Remboursement Avance démarrage/Montant total", group_operator="avg",
                                                      store=True)
    @api.depends('montant_reimbursement_amount', 'budget')
    def _compute_montant_reimbursement_amount_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_reimbursement_amount:
                record.montant_reimbursement_amount_gap = record.montant_reimbursement_amount * 100 / record.budget
            else:
                record.montant_reimbursement_amount_gap = 0

    decaissement = fields.Monetary(
        string="Décaissements-RADs",
        compute="_compute_decaissement",
        store=True,
        help="décaissement avec pris en compte les remboursements de l'avance de demarrage"
    )
    @api.depends('montant_total_avance_demarrage', 'project_debit', 'montant_reimbursement_amount')
    def _compute_decaissement(self):
        for project in self:
            project.decaissement = (
                project.montant_total_avance_demarrage or 0.0
            ) + (
                project.project_debit or 0.0
            ) - (
                project.montant_reimbursement_amount or 0.0
            )
    decaissement_percentage = fields.Float(
        string="Pourcentage de décaissement-RAD",
        compute="_compute_decaissement_percentage",
        store=True,
        help="Pourcentage de décaissement avec pris en compte le remboursement de l'avance de demarrage"
    )
    @api.depends('decaissement', 'budget')
    def _compute_decaissement_percentage(self):
        for project in self:
            if project.budget > 0:
                project.decaissement_percentage = (project.decaissement / project.budget) * 100
            else:
                project.decaissement_percentage = 0.0
    decaissement_budget = fields.Monetary(
        string="Décomptes (Budget)",
        store=True,
        help="décaissement Selon la Direction Général du Budget"
    )
    
    decaissement_budget_percentage = fields.Float(
        string="Pourcentage de décaissement",
        compute="_compute_decaissement_budget_percentage",
        store=True,
        help="Pourcentage de décaissement Selon la Direction Général du Budget"
    )
    @api.depends('decaissement_budget', 'budget')
    def _compute_decaissement_budget_percentage(self):
        for project in self:
            if project.budget > 0:
                project.decaissement_budget_percentage = (project.decaissement_budget / project.budget) * 100
            else:
                project.decaissement_budget_percentage = 0.0
    # Ebnou notes
    montant_total_caution_avance_de_demarrage_projet = fields.Monetary(string="Caution d’avance de démarrage",
                                                                       currency_field='currency_id',
                                                                       compute="_compute_montant_total_caution_avance_de_demarrage_projet",
                                                                       store=True)
    montant_total_caution_avance_de_demarrage_projet_gap = fields.Float(string="% Caution d’avance de démarrage",
                                                                        compute="_compute_montant_total_caution_avance_de_demarrage_projet_gap",
                                                                        help="Avance de démarrage/Montant Initial",
                                                                        group_operator="avg", store=True)
    # _______________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
    department_id = fields.Many2one('hr.department', string='Département')

    project_debit = fields.Monetary(string='Décomptes', currency_field='currency_id', compute="_compute_project_debit",
                                    group_operator="sum", store=True)
    project_debit_gap = fields.Float(string='% Décomptes', compute='_compute_project_debit_gap',
                                     help="Décomptes / Globale", group_operator=False, store=True)
    milestone_count = fields.Integer(compute='_compute_project_milestone_count')

    @api.depends('milestone_ids')
    def _compute_project_milestone_count(self):
        for record in self:
            if record:
                record.milestone_count = self.env['project.milestone'].search_count(
                    [('project_id', '=', record.id)])
            else:
                record.milestone_count = 0

    # Add text field comment
    financial_comment = fields.Text(string='Commentaire')
    # Budget splitting
    # state_budget = fields.Monetary(currency_field='currency_id', string="Etat")
    # ptf_budget = fields.Monetary(currency_field='currency_id', string="PTFs")
    # other_budget = fields.Monetary(currency_field='currency_id', string="Autres")
    decaissement_depasse_av = fields.Boolean("Décaissement dépasse Avancement ", compute='_compute_dec_av',
                                             help="Taux d'avancement - taux decaissement", store=True)
    delai_consomm_depasse_av = fields.Boolean("Délai Consommé dépasse Avancement", compute='_compute_del_cons_av',
                                              help="taux de consommation delais dépasse le taux d'avancement", store=True)

    # from json
    annee_marche = fields.Integer(string="Année du Marché")

    @api.model
    def fetch_geolocation_coordinates(self, partners):
        partners_data = defaultdict(list)

        for partner in partners:
            if partner['geolocation_ids']:
                for geo in partner['geolocation_ids']:
                    if 'id' in geo and 'latitude' in geo and 'longitude' in geo:
                        partners_data[partner['id']].append({
                            'point': geo['point'],
                            'id': geo['id'],
                            'latitude': geo['latitude'],
                            'longitude': geo['longitude'],
                        })

        return dict(partners_data)

    # financial_transaction
    def _filter_attributaire(self):
        return [("supplier_rank", ">", 0), ('category_id', '=', self.env.ref('project_customization.attributaire').id)]

    def _filter_autorite_contractante(self):
        return [('category_id', '=', self.env.ref('project_customization.autorite_contractante').id)]

    def _filter_commission_passation(self):
        return [('category_id', '=', self.env.ref('project_customization.commission_passation').id)]

    count_financial_transactions = fields.Integer(string='Situation financière',
                                                  compute='_compute_count_financial_transactions')
    avenant_ids = fields.One2many('project.avenant', 'project_id', string="Avenants du projet")
    count_project_avenant = fields.Integer(string='Nbr Avenants', compute='_compute_count_project_avenant')
    count_project_mission = fields.Integer(string='Nombre des Missions', compute='_compute_count_project_mission')
    financial_transaction_ids = fields.One2many('account.analytic.line.project', 'project_id',
                                                string="Situations financières")
    # count_project_problem = fields.Integer(string='Problemes', compute='_compute_count_project_problem')
    commission_passation = fields.Many2one('res.partner', string='Commission de passation',
                                           domain=_filter_commission_passation)
    autorite_contractante = fields.Many2one('res.partner', string='Autorité contractante',
                                            domain=_filter_autorite_contractante)

    titulaires = fields.Many2many(comodel_name='res.partner', relation='base_res_partner_project_rel',
                                  string='Titulaires')
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=False, tracking=False,
                                 domain="['|', ('company_id', '=?', company_id), ('company_id', '=', False)]")
    def fill_partner_id(self):
        for record in self:
            if not record.titulaires:
                continue

            # Get titulaires with valid NIF
            titulaires_with_nif = record.titulaires.filtered(lambda t: t.vat)
            titulaire_names = titulaires_with_nif.mapped('name')

            if not titulaire_names:
                continue  # Skip if no titulaire has a valid NIF

            if len(titulaire_names) == 1:
                # If only one titulaire name, find or create the corresponding partner
                single_name = titulaire_names[0]
                matching_partner = self.env['res.partner'].search([
                    ('name', '=', single_name)
                ], limit=1)

                if matching_partner:
                    record.partner_id = matching_partner
                else:
                    new_partner = self.env['res.partner'].create({
                        'name': single_name,
                        'vat': titulaires_with_nif[0].vat,
                        'supplier_rank': 1,
                        'category_id': self.env.ref('project_customization.attributaire'),
                        'is_company': True,
                    })
                    record.partner_id = new_partner
                continue

            # Search for partners with names containing all titulaire names
            partners = self.env['res.partner'].search([('is_company', '=', True)])
            matching_partner = None

            for partner in partners:
                if all(name in partner.name for name in titulaire_names):
                    matching_partner = partner
                    break

            if matching_partner:
                record.partner_id = matching_partner
            else:
                combined_name = " & ".join(titulaire_names)
                new_partner = self.env['res.partner'].create({
                    'name': combined_name,
                    'vat': titulaires_with_nif[0].vat,  # Use VAT of the first titulaire with NIF
                    'supplier_rank': 1,
                    'category_id': self.env.ref('project_customization.attributaire'),
                    'is_company': True,
                    'child_ids': [(0, 0, {'name': name, 'vat': t.vat}) for t, name in zip(titulaires_with_nif, titulaire_names)],
                })
                record.partner_id = new_partner

    @api.depends('financial_transaction_ids')
    def _compute_count_financial_transactions(self):
        for record in self:
            if record:
                record.count_financial_transactions = self.env['account.analytic.line.project'].search_count(
                    [('project_id', '=', record.id)])
            else:
                record.count_financial_transactions = 0

    @api.depends('avenant_ids')
    def _compute_count_project_avenant(self):
        for record in self:
            if record:
                record.count_project_avenant = self.env['project.avenant'].search_count(
                    [('project_id', '=', record.id)])
            else:
                record.count_project_avenant = 0

    

    def open_view_financial_transacrion(self):
        action = self.env['ir.actions.act_window']._for_xml_id('project_customization.account_analytic_line_action')
        action['context'] = {'create': True, 'default_account_id': self.analytic_account_id.id,
                             'default_project_id': self.id, 'active_id_chatter': self.id}
        action['display_name'] = 'Situation financière'
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def open_view_project_avenant(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Avenant',
            'res_model': 'project.avenant',
            'view_mode': 'tree,kanban,form,pivot,graph',
            'domain': [('project_id', '=', self.id)],
            'context': {'create': True, 'default_project_id': self.id, 'default_date': fields.Datetime.now()}
        }

    def open_view_project_mission(self):
        action = self.env['ir.actions.act_window']._for_xml_id('project_customization.action_mission_projects')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'create': False, 'default_project_id': self.id}
        return action

    appraisal_ids = fields.One2many('res.partner.appraisal', 'project_id')
    count_appraisal = fields.Integer(string='Evaluation', compute='_compute_count_appraisal')

    @api.depends('appraisal_ids')
    def _compute_count_appraisal(self):
        for record in self:
            if record:
                record.count_appraisal = self.env['res.partner.appraisal'].search_count(
                    [('project_id', '=', record.id)])
            else:
                record.count_appraisal = 0

    def open_view_res_partner_appraisal(self):
        action = self.env['ir.actions.act_window']._for_xml_id('project_customization.res_partner_appraisal_action')
        action['context'] = {'default_project_id': self.id, 'default_partner_id': self.partner_id}
        action['display_name'] = 'Antécédents'
        action['domain'] = [('project_id', '=', self.id)]
        return action

    # end financial_transaction___________________________________________________________________
    # reception___________________________________________________________________________________
    projects_status = [('pre_reception', 'Pré-réception technique'), ('reception_pro', 'Réception provisoire'),
                       ('reception_def', 'Réception définitive')]

    project_status = fields.Selection(projects_status, string='Réception')
    
    pre_reception_date = fields.Date(string='Date pré-réception technique')
    pv_de_reception_pre = fields.Binary(string='PV de pré-réception')

    reception_pro_date = fields.Date(string='Date réception provisoire')
    pv_de_reception_pro = fields.Binary(string='PV de réception provisoire')

    reception_def_date = fields.Date(string='Date réception définitive')
    pv_de_reception_def = fields.Binary(string='PV de réception définitive')

    
    # end_reception___________________________________________________________________________________
    @api.depends('date_start', 'date', 'delai_consomme')
    def _compute_retard_constate(self):
        for project in self:
            if project.date and project.delai_consomme and project.date_start:
                difference_dates = (project.date - project.date_start).days  # Convert timedelta to days
                difference = project.delai_consomme - difference_dates
                if difference > 0:
                    project.retard_constate = difference
                elif difference < 0:
                    project.retard_constate = 0  # Project is ahead of schedule, so no delay
                elif difference == 0:
                    project.retard_constate = 0
            else:
                project.retard_constate = 0

    @api.depends('date_start', 'date', 'delai_consomme')
    def _compute_duree_restante(self):
        for project in self:
            if project.date and project.delai_consomme and project.date_start:
                difference_dates = (project.date - project.date_start).days  # Convert timedelta to days
                difference = project.delai_consomme - difference_dates
                if difference > 0:
                    project.duree_restante = 0  # Set duree_restante to 0 since project is not behind schedule
                elif difference < 0:
                    project.duree_restante = abs(difference)  # Assign the remaining duration
                elif difference == 0:
                    project.duree_restante = 0
            else:
                project.duree_restante = 0

    @api.model_create_multi
    def create(self, vals_list):
        project = super().create(vals_list)
        plan_id = self.env['account.analytic.plan'].with_context(lang='en_EN').search([('name', '=', 'Projects')],
                                                                                      limit=1).id
        if plan_id:
            analytic_account = self.env['account.analytic.account'].create({
                'name': project.name,
                'company_id': project.company_id.id,
                'partner_id': project.partner_id.id,
                'plan_id': plan_id,
                'active': True,
            })
            project.write({'analytic_account_id': analytic_account.id})
        return project
    def action_get_attachment_view_report(self):
        """Display binary attachments (e.g., reports) for the current project."""
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('project_customization.action_attachment_kanban')
        # Retrieve all binary attachments for the project
        project_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.project'), ('res_id', '=', self.id), ('mimetype', '=', 'application/pdf')])
        if not project_documents:
            # Handle the case where no documents are found
            res['domain'] = [('id', '=', -1)]  # Use a domain that results in no records
        else:
            res['domain'] = [('id', 'in', project_documents.ids)]
        return res

    def action_get_attachment_view_video(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('project_customization.action_attachment_kanban')
        project_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.project'), ('res_id', '=', self.id), ('mimetype', '=', 'video/mp4')])
        if not project_documents:
            # Handle the case where no documents are found
            res['domain'] = [('id', '=', -1)]  # Use a domain that results in no records
        else:
            res['domain'] = [('id', 'in', project_documents.ids)]
        return res
    def action_get_attachment_view_galeries(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('project_customization.action_attachment_kanban')
        project_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.project'), ('res_id', '=', self.id), ('mimetype', '=', 'image/jpeg')])
        if not project_documents:
            # Handle the case where no documents are found
            res['domain'] = [('id', '=', -1)]  # Use a domain that results in no records
        else:
            res['domain'] = [('id', 'in', project_documents.ids)]
        return res
    financing_ids = fields.One2many('project.financing', 'project_id', string="Financements")
    def action_get_attachment_view(self):
        self.ensure_one()

        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')

        project_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.project'), ('res_id', '=', self.id)])
        avenant_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.avenant'), ('res_id', 'in', self.avenant_ids.ids)])
        feedback_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.feedback'), ('res_id', 'in', self.feedbacks.ids)])
        milestone__documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.milestone'), ('res_id', 'in', self.milestone_ids.ids)])
        financial_transaction_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'account.analytic.line.project'), ('res_id', 'in', self.financial_transaction_ids.ids)])
        mission_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'abc.exp.besoin.mission.projects'), ('res_id', 'in', self.mission_ids.ids)])

        documents = project_documents.ids + avenant_documents.ids + feedback_documents.ids + milestone__documents.ids + financial_transaction_documents.ids + mission_documents.ids
        res['domain'] = [('id', 'in', documents)]
        return res
    def action_get_attachment_view_autorite_reports(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('project_customization.action_attachment_kanban')
        project_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.project'), ('res_id', '=', self.id)])
        avenant_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.avenant'), ('res_id', 'in', self.avenant_ids.ids)])
        feedback_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.feedback'), ('res_id', 'in', self.feedbacks.ids)])
        milestone__documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'project.milestone'), ('res_id', 'in', self.milestone_ids.ids)])
        financial_transaction_documents = self.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'account.analytic.line.project'), ('res_id', 'in', self.financial_transaction_ids.ids)])
        
        documents = project_documents.ids + avenant_documents.ids + feedback_documents.ids + milestone__documents.ids + financial_transaction_documents.ids
        res['domain'] = [('id', 'in', documents)]
        res['context'] = {'search_default_group_by_autorite_document_type': 1, 'default_res_model': 'project.project', 'default_res_id': self.id}
        return res
    @api.depends('update_ids')
    def _compute_update_count(self):
        for project in self:
            project.update_count = len(project.update_ids)

    @api.depends('feedbacks')
    def _compute_feedback_count(self):
        for project in self:
            project.feedback_count = len(project.feedbacks)

    @api.depends('stop_stations')
    def _compute_stop_station_count(self):
        for project in self:
            project.stop_station_count = len(project.stop_stations)

    

    

    def _compute_tracking_count(self):
        for project in self:
            project.tracking_count = len(project.tracking_ids)

    @api.depends('budget', 'project_debit')
    def _compute_project_debit_gap(self):
        for record in self:
            if record.budget != 0:
                record.project_debit_gap = record.project_debit * 100 / record.budget
            else:
                record.project_debit_gap = 0

    @api.depends('montant_total_avenants', 'montant_initial')
    def _compute_montant_total_avenants_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_total_avenants:
                record.montant_total_avenants_gap = record.montant_total_avenants * 100 / record.montant_initial
            else:
                record.montant_total_avenants_gap = 0

    @api.depends('montant_total_avenants', 'montant_initial')
    def _compute_montant_total_ordre_services_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_total_ordre_services:
                record.montant_total_ordre_services_gap = record.montant_total_ordre_services * 100 / record.montant_initial
            else:
                record.montant_total_ordre_services_gap = 0

    @api.depends('montant_total_cautions_bonne_ex', 'montant_initial')
    def _compute_montant_total_cautions_bonne_ex_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_total_cautions_bonne_ex:
                record.montant_total_cautions_bonne_ex_gap = record.montant_total_cautions_bonne_ex * 100 / record.montant_initial
            else:
                record.montant_total_cautions_bonne_ex_gap = 0

    @api.depends('montant_total_cautions_bon_fin', 'montant_initial')
    def _compute_montant_total_cautions_bon_fin_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_total_cautions_bon_fin:
                record.montant_total_cautions_bon_fin_gap = record.montant_total_cautions_bon_fin * 100 / record.montant_initial
            else:
                record.montant_total_cautions_bon_fin_gap = 0

    @api.depends('montant_total_penalite', 'montant_initial')
    def _compute_montant_total_penalite_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_total_penalite:
                record.montant_total_penalite_gap = record.montant_total_penalite * 100 / record.montant_initial
            else:
                record.montant_total_penalite_gap = 0

    @api.depends('montant_total_remise_penalite', 'budget')
    def _compute_montant_total_remise_penalite_gap(self):
        for record in self:
            if record.budget != 0 and record.montant_total_remise_penalite:
                record.montant_total_remise_penalite_gap = record.montant_total_remise_penalite * 100 / record.budget
            else:
                record.montant_total_remise_penalite_gap = 0

    @api.depends('retard_constate', 'budget')
    def _compute_penalite_plafone(self):
        for record in self:
            if record.retard_constate > 0 and record.budget:
                record.penalite_plafone = record.retard_constate * record.budget / 1000
                if record.penalite_plafone > record.budget / 10:
                    record.penalite_plafone = record.budget / 10
            else:
                record.penalite_plafone = 0

    @api.depends('penalite_plafone', 'budget')
    def _compute_penalite_plafone_gap(self):
        for record in self:
            if record.penalite_plafone > 0 and record.budget > 0:
                record.penalite_plafone_gap = record.penalite_plafone * 100 / record.budget
            else:
                record.penalite_plafone_gap = 0

    @api.depends('montant_total_avance_demarrage', 'montant_initial')
    def _compute_montant_total_avance_demarrage_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_total_avance_demarrage:
                record.montant_total_avance_demarrage_gap = record.montant_total_avance_demarrage * 100 / record.montant_initial
            else:
                record.montant_total_avance_demarrage_gap = 0

    # Ebnou notes
    @api.depends('montant_total_caution_avance_de_demarrage_projet', 'montant_initial')
    def _compute_montant_total_caution_avance_de_demarrage_projet_gap(self):
        for record in self:
            if record.montant_initial != 0 and record.montant_total_caution_avance_de_demarrage_projet:
                record.montant_total_caution_avance_de_demarrage_projet_gap = record.montant_total_caution_avance_de_demarrage_projet * 100 / record.montant_initial
            else:
                record.montant_total_caution_avance_de_demarrage_projet_gap = 0

    @api.depends('date_entr_vig', 'reception_def_date','last_update_date')
    def _compute_delai_consomme(self):
        for project in self:
            try:
                # Now both operands are datetime.date objects
                delta = (project.reception_def_date or project.last_update_date) - project[project['date_entr_vig']]
                project.delai_consomme = delta.days if delta.days >= 0 else 0
            except:
                project.delai_consomme = 0
    # @api.model
    # def _cron_update_date_entr_vig(self):
    #     projects = self.search([])  # Adjust the domain as needed
    #     for project in projects:
    #         # Logic to update the date_based_field
    #         project._compute_current_date()
    #         # project.date_entr_vig = project.date_entr_vig  # Example update


    # ______________________________________________________________________________
    @api.depends('date_entr_vig')
    def _compute_date_start(self):
        for project in self:
            try:
                project.date_start = project[project['date_entr_vig']]
            except:
                project.date_start = False

    @api.depends('date_entr_vig', 'delai_execution_apres_avenant')
    def _compute_date(self):
        for project in self:
            try:
                date_entr_vig = project[project['date_entr_vig']]
                project.date = date_entr_vig + timedelta(days=project.delai_execution_apres_avenant)
            except:
                project.date = False

    # @api.depends('delai_consomme', 'delai_execution_apres_avenant')
    # def _compute_rapport_delais(self):
    #     for project in self:
    #         if project.delai_execution_apres_avenant != 0:
    #             project.rapport_delais = project.delai_consomme * 100 / project.delai_execution_apres_avenant
    #         else:
    #             project.rapport_delais = 0

    @api.depends('montant_initial', 'montant_total_avenants')
    def _compute_budget(self):
        for project in self:
            project.budget = project.montant_initial + project.montant_total_avenants

    # Ebnou notes
    @api.depends('avenant_ids','avenant_ids.state','avenant_ids.type_avenant','avenant_ids.delai_execution', 'delai_execution', 'stop_stations.state')
    def _compute_delai_execution_apres_avenant(self):
        for project in self:
            # Calculate total delay from valid avenants
            # total_delai = project.avenant_ids.filtered(lambda a: a.type_avenant == 'avenant' and a.state == 'valide')
            total_delai = project.avenant_ids.filtered(lambda a: a.state == 'valide')
            total_delai_amount = sum(avenant.delai_execution for avenant in total_delai)

            # Calculate total delay from valid stop stations
            total_stop_period = 0
            for stop in project.stop_stations.filtered(lambda s:s.state=='valide'):
                if stop.date_start and stop.date_end:
                    stop_duration = (stop.date_end - stop.date_start).days
                    total_stop_period += stop_duration

            # Sum up the delays and assign to delai_execution_apres_avenant
            project.delai_execution_apres_avenant = total_delai_amount + project.delai_execution - total_stop_period
    # ______________________________________________________________________________________
    @api.depends('avenant_ids','avenant_ids.amount','avenant_ids.state','avenant_ids.type_avenant')
    def _compute_montant_total_avenants(self):
        for project in self:
            avenants = project.avenant_ids.filtered(lambda a: a.type_avenant == 'avenant' and a.state=='valide')
            total_amount = sum(avenant.amount for avenant in avenants)
            project.montant_total_avenants = total_amount


    @api.depends('avenant_ids','avenant_ids.amount','avenant_ids.state','avenant_ids.type_avenant')
    def _compute_montant_total_ordre_services(self):
        for project in self:
            ordres_services = project.avenant_ids.filtered(lambda a: a.type_avenant == 'ordre_service' and a.state=='valide')
            total_amount = sum(avenant.amount for avenant in ordres_services)
            project.montant_total_ordre_services = total_amount


    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_montant_total_cautions_bonne_ex(self):
        for project in self:
            cautions = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'caution_bonne_ex' and t.state=='valide')
            project.montant_total_cautions_bonne_ex = sum(caution.amount for caution in cautions)

    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_montant_total_cautions_bon_fin(self):
        for project in self:
            cautions = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'caution_de_bon_fin' and t.state=='valide')
            total_amount = sum(caution.amount for caution in cautions)
            project.montant_total_cautions_bon_fin = total_amount


    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_montant_total_penalite(self):
        for project in self:
            penalities = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'penanlite_de_retard' and t.state=='valide')
            total_amount = sum(penality.amount for penality in penalities)
            project.montant_total_penalite = total_amount


    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_montant_total_remise_penalite(self):
        for project in self:
            remises = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'remise_sur_penalite' and t.state=='valide')
            total_amount = sum(remise.amount for remise in remises)
            project.montant_total_remise_penalite = total_amount


    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_montant_total_avance_demarrage(self):
        for project in self:
            avances = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'avance_de_demarrage_projet' and t.state=='valide')
            total_amount = sum(avance.amount for avance in avances)            
            project.montant_total_avance_demarrage = total_amount

    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_montant_reimbursement_amount(self):
        for project in self:
            avances = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'reimbursement_amount' and t.state=='valide')
            total_reimbursement_amount = sum(avance.amount for avance in avances)
            project.montant_reimbursement_amount = total_reimbursement_amount


    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_montant_total_caution_avance_de_demarrage_projet(self):
        for project in self:
            cautions = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'caution_avance_de_demarrage_projet' and t.state=='valide')
            total_amount = sum(caution.amount for caution in cautions)
            project.montant_total_caution_avance_de_demarrage_projet = total_amount

    @api.depends('count_financial_transactions', 'financial_transaction_ids.amount', 'financial_transaction_ids.transaction_type', 'financial_transaction_ids.state')
    def _compute_project_debit(self):
        for project in self:
            debits = project.financial_transaction_ids.filtered(lambda t: t.transaction_type == 'decaissement' and t.state=='valide')
            total_amount = sum(debit.amount for debit in debits)
            project.project_debit = total_amount


    

    @api.depends('calculated_achievement', 'last_update_decaissement')
    def _compute_dec_av(self):
        for record in self:
            if record.calculated_achievement < record.last_update_decaissement:
                record.decaissement_depasse_av = True
            else:
                record.decaissement_depasse_av = False

    @api.depends('calculated_achievement', 'last_update_consom_delai')
    def _compute_del_cons_av(self):
        for record in self:
            if record.last_update_consom_delai and record.calculated_achievement:
                if record.calculated_achievement < record.last_update_consom_delai:
                    record.delai_consomm_depasse_av = True
            else:
                record.delai_consomm_depasse_av = False

    @api.depends('calculated_achievement')
    def _compute_plage(self):
        for record in self:
            # Determine the maximum plage for the given number

            max_plage = (int(record.calculated_achievement) // 5 + 1) * 5 if int(record.calculated_achievement) not in [
                i for i in range(5, 105, 5)] else int(record.calculated_achievement)
            try:
                record.plage = str(max_plage)
            except:
                record.plage = False

    def action_project_changes(self):
        active_id = self.id
        trackes = self.sudo().env['mail.tracking.value'].search([
            ("mail_message_id.model", "=", 'project.project'),
            ("field_id.name", "in", ["calculated_achievement", "project_debit_gap", "last_update_consom_delai"])
        ])
        return {
            "name": "Historiques des changements",
            "type": "ir.actions.act_window",
            "res_model": "mail.tracking.value",
            "view_mode": "tree,form,graph,kanban,pivot",
            "domain": [
                ("mail_message_id.res_id", "in", [track.mail_message_id.res_id for track in trackes]),
                ("mail_message_id.model", "=", 'project.project'),
                ("field_id.name", "in", ["calculated_achievement", "project_debit_gap", "last_update_consom_delai"])

            ],
            "context": {'group_by': [], 'graph_measure': 'value', 'graph_mode': 'bar',
                        'graph_groupbys': ['document_id', 'date_change', 'new_value_float'], 'graph_order': None,
                        'graph_stacked': True,
                        'graph_cumulated': False},
        }

    def action_get_graph(self):
        data_to_remove = self.env['milestone.wizard'].search([('project_id', '=', self.id)])
        data_to_remove.unlink()
        for milestone in self.milestone_ids:
            self.env["milestone.wizard"].create(
                {
                    "project_id": self.id,
                    "date_start": milestone.date_start,
                    "date_end": milestone.date_end,
                    "milestone": milestone.name,
                    "type": "Planification",
                    "measure": milestone.planned_weight,
                }
            )

            self.env["milestone.wizard"].create(
                {
                    "project_id": self.id,
                    "date_start": milestone.date_start,
                    "date_end": milestone.date_end,
                    "milestone": milestone.name,
                    "type": "Avancement",
                    "measure": milestone.effectif_rate,
                }
            )
        return {
            "name": "Analyse des jalons",
            "type": "ir.actions.act_window",
            "res_model": "milestone.wizard",
            "view_mode": "graph,tree",
            "domain": [("project_id", "=", self.id)],
            "context": {'group_by': [], 'graph_measure': 'measure', 'graph_mode': 'line',
                        'graph_groupbys': ['milestone', 'type'], 'graph_order': None, 'graph_stacked': False,
                        'graph_cumulated': True},
        }

    @api.model
    def format_percentage(self, value):
        return "{:.2%}".format(value)

    def action_project_budgets(self):
        # Assuming the current object is a model class that has access to the necessary fields and methods
        # Define the values for the fields in the action
        name = "Project's budgets"
        type = "ir.actions.act_window"
        res_model = "crossovered.budget"
        view_mode = "tree,kanban,form"
        context = {
            'default_project_id': self.id,
            'default_department_id': self.department_id.id,
        }

        # Create the action record

        action = {
            'name': name,
            'type': type,
            'res_model': res_model,
            'view_mode': view_mode,
            'context': context,
        }

        # Perform any additional processing or operations if needed

        # Return the created action record
        return action

    def project_feedback_action(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('project_customization.project_feedback_action')
        action['context'] = {
            'default_project_id': self.id,
            # 'calculated_achievement': self.bureau_de_suivi.id,
            # 'default_bureau_de_control': self.bureau_de_control.id,
            'default_funding_mode_ids': self.funding_mode_ids.ids,
            'default_date_signature': self.date_signature,
            'default_date_notification': self.date_notification,
            'default_date_noti_deb_ex': self.date_noti_deb_ex,
            'default_date_p_a_demarrage': self.date_p_a_demarrage,
            'default_date_mise_mission_c': self.date_mise_mission_c,
            'default_date_remise_site': self.date_remise_site,
            'default_date_entr_vig': self.date_entr_vig,
            'default_other_date': self.other_date,
            'default_other_date_description': self.other_date_description,
            'default_project_debit_dec': self.decaissement_percentage,
            'default_calculated_achievement': sum(self.milestone_ids.mapped('pourcentage_realise')),
            'default_avancement_prevue': sum(self.milestone_ids.mapped('pourcentage_prevue_realise')),
            'default_anteced_ret_exec': self.anteced_ret_exec,
            'default_sous_traitance': self.sous_traitance,
            'default_sous_traitance_gap': self.sous_traitance_gap,
            'default_resiliation': self.resiliation,
            'default_resiliation_date': self.resiliation_date,
            'default_project_status': self.project_status,
            'default_status': self.last_update_status,
            'default_pre_reception_date': self.pre_reception_date,
            'default_reception_pro_date': self.reception_pro_date,
            'default_reception_def_date': self.reception_def_date,

            # 'delete': False,
            # 'search_default_open_tasks': True,
            'active_id_chatter': self.id,
        }
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def project_stop_station_action(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('project_customization.project_stop_station_action')
        action['context'] = {
            'default_project_id': self.id,
            'default_funding_mode_ids': self.funding_mode_ids.ids,
            'delete': False,
            # 'search_default_open_tasks': True,
            'active_id_chatter': self.id,
        }
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def action_milestone_sharing(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'project_customization.project_sharing_project_milestone_action')
        action['context'] = {
            'default_project_id': self.id,

            'delete': False,
            # 'search_default_open_tasks': True,
            'active_id_chatter': self.id,
            # 'no_breadcrumbs': True
        }
        action['domain'] = [('project_id', '=', self.id)]
        # action['flags']= {'form': {'action_buttons': True, 'options': {'clear_breadcrumbs':True } } }

        return action

    def action_feedback_sharing(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'project_customization.project_sharing_project_feedback_portal_action')
        action['context'] = {
            'default_project_id': self.id,
            # 'default_bureau_de_suivi': self.bureau_de_suivi.id or False,
            # 'default_bureau_de_control': self.bureau_de_control.id or False,
            'default_funding_mode_ids': self.funding_mode_ids.ids or False,
            'default_date_signature': str(self.date_signature) if self.date_signature else str(''),
            'default_date_notification': str(self.date_notification) if self.date_notification else str(''),
            'default_date_noti_deb_ex': str(self.date_noti_deb_ex) if self.date_noti_deb_ex else str(''),
            'default_date_p_a_demarrage': str(self.date_p_a_demarrage) if self.date_p_a_demarrage else str(''),
            'default_date_mise_mission_c': str(self.date_mise_mission_c) if self.date_mise_mission_c else str(''),
            'default_date_remise_site': str(self.date_remise_site) if self.date_remise_site else str(''),
            'default_date_entr_vig': self.date_entr_vig or False,
            'default_other_date': str(self.other_date) if self.other_date else str(''),
            'default_other_date_description': self.other_date_description,
            'default_project_debit_dec': self.project_debit_gap or False,
            'default_calculated_achievement': self.calculated_achievement or False,
            'default_anteced_ret_exec': self.anteced_ret_exec or False,
            'default_sous_traitance': self.sous_traitance or False,
            'default_sous_traitance_gap': self.sous_traitance_gap or False,
            'default_resiliation': self.resiliation or False,
            'default_resiliation_date': str(self.resiliation_date) if self.resiliation_date else str(''),
            'default_project_status': self.project_status or False,
            'default_status': self.last_update_status or False,
            'default_pre_reception_date': str(self.pre_reception_date) if self.pre_reception_date else str(''),
            'default_reception_pro_date': str(self.reception_pro_date) if self.reception_pro_date else str(''),
            'default_reception_def_date': str(self.reception_def_date) if self.reception_def_date else str(''),
            'delete': False,
            # 'search_default_open_tasks': True,
            'active_id_chatter': self.id,
        }
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def action_stop_station_sharing(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'project_customization.project_sharing_project_stop_station_portal_action')
        action['context'] = {
            'default_project_id': self.id,

            'default_funding_mode_ids': self.funding_mode_ids.ids or False,
            'delete': False,
            # 'search_default_open_tasks': True,
            'active_id_chatter': self.id,
        }
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def action_avenant_sharing(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('project_customization.action_project_sharing_avenant')
        action['context'] = {
            'default_project_id': self.id,
            'delete': False,
            # 'search_default_open_tasks': True,
            'active_id_chatter': self.id,
        }
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def action_financial_transaction_sharing(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'project_customization.account_analytic_line_sharing_action')
        action['context'] = {'delete': False, 'default_account_id': self.analytic_account_id.id,
                             'default_project_id': self.id, 'active_id_chatter': self.id}
        action['display_name'] = 'Situation financière'
        action['domain'] = [('project_id', '=', self.id)]
        return action
    
    #qr code code
    #QR code structure:
    qr_code = fields.Binary("QR Code", compute='_generate_qr_code')
    @api.depends('description', 'numero_marche', 'last_update_status_mission', 
                 'calculated_achievement', 'last_update_consom_delai', 
                 'percentage_conf_personnels', 'percentage_conf_materiel', 
                 'observation_number', 'last_update_date','message_ids','truncated_name')
    def _generate_qr_code(self):
        for record in self:
            # Generate URL for the QR Code
            qr_data = f"{self.env['ir.config_parameter'].sudo().get_param('project_customization.url')}/{record.id}/{record.truncated_name}"

            # Create QR Code
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)

            # Convert QR Code to an image
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            record.qr_code = b64encode(buffer.getvalue()) 
    truncated_name = fields.Char(
        string="code",
        compute="_compute_truncated_name",
        store=True,
        help="The truncated version of the project name, limited to 100 characters without cutting words."
    )
    quantity = fields.Integer(
        string="Quantité",
        default=1,
        help="An integer field to store quantity information for the project. Defaults to 1."
    )
    @api.depends('name')
    def _compute_truncated_name(self):
        for record in self:
            record.truncated_name = self._get_truncated_name(record.name)

    @staticmethod
    def _get_truncated_name(name, max_length=100):
        if not name:
            return ""
        if len(name) <= max_length:
            return name
        truncated = name[:max_length]
        if name[max_length:].strip():  # Check if we're in the middle of a word
            truncated = truncated.rsplit(' ', 1)[0]
        return truncated
    token = fields.Char(string="Token", compute="_compute_token", store=True)

    @api.depends('autorite_contractante')
    def _compute_token(self):
        for project in self:
            if project.autorite_contractante:
                # Create a token using the autorite_contractante.display_name field
                full_hash = hashlib.sha256(project.autorite_contractante.name.encode()).hexdigest()
                project.token = full_hash[:6]  # Truncate to the first 6 characters
            else:
                project.token = False
    # new concept of sharing

