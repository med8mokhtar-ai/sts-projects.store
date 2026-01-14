from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, date
from odoo.tools import LazyTranslate

_lt = LazyTranslate(__name__)

class PublicProject(models.Model):
    _inherit = [
        'portal.mixin',
        'rating.parent.mixin',
        'mail.activity.mixin',
        'mail.tracking.duration.mixin',
        'analytic.plan.fields.mixin',
    ]
    _name = 'public.project'
    _description = 'Projet Public - Vue Exécutant'
    _rec_name = 'numero_marche'
    _rec_names_search = ['name', 'numero_marche']

    user_id = fields.Many2one('res.users', string='Chef de projet', default=lambda self: self.env.user, tracking=True, falsy_value_label=_lt("👤 Non assigné"))    
    
    # === IDENTIFICATION ===
    name = fields.Char(string='Objet du Projet', required=True)
    numero_marche = fields.Char(string='Numéro du Marché', required=True)
    
    # === TYPE DE MARCHE ===
    type_marche = fields.Selection([
        ('travaux', 'Marché de Travaux'),
        ('fournitures', 'Marché de Fournitures'),
        ('services', 'Marché de Services'),
        ('mixte', 'Marché Mixte'),
    ], string='Type de Marché', default='travaux', required=True)
    
    mode_passation = fields.Selection([
        ('appel_offres', 'Appel d\'offres'),
        ('appel_offres_restreint', 'Appel d\'offres restreint'),
        ('appel_offres_international', 'Appel d\'offres international'),
        ('appel_offres_national', 'Appel d\'offres national'),
        ('appel_offres_international_restreint', 'Appel d\'offres international restreint'),
        ('appel_offres_national_restreint', 'Appel d\'offres national restreint'),
        ('appel_offres_ouvert', 'Appel d\'offres ouvert'),
        ('appel_offres_international_ouvert', 'Appel d\'offres international ouvert'),
        
        ('procedure_negociee', 'Procédure négociée'),
        ('procedure_negociee_avec_publicite', 'Procédure négociée avec publicité'),
        ('procedure_negociee_sans_publicite', 'Procédure négociée sans publicité'),
        
        ('dialogue_competitif', 'Dialogue compétitif'),
        ('contrat_conception_construction', 'Contrat de conception-construction'),
        ('contrat_fourniture', 'Contrat de fourniture'),
        
        ('marche_commande', 'Marché à commande'),
        ('marche_cloture', 'Marché à clause de fermeture'),
        
        ('selection_consultants', 'Sélection de consultants'),
        ('selection_consultants_individuels', 'Sélection des consultants individuels'),
        ('selection_based_qualifications', 'Sélection fondée sur les qualifications'),
        ('selection_based_qualifications_consultants', 'Sélection fondée sur les qualifications des consultants'),
        ('selection_qualite_prix', 'Sélection qualité-prix'),
        ('selection_qualite_cout', 'Sélection qualité-coût'),
        ('selection_meilleur_qualite', 'Sélection de la meilleure qualité'),
        ('selection_meilleur_qualite_consultants', 'Sélection de la meilleure qualité des consultants'),
        
        ('comparaison_cv', 'Comparaison de CV'),
        ('comparaison_cv_offres', 'Comparaison de CV et offres'),
        
        ('consultation_prestataires', 'Consultation de prestataires'),
        ('prestations_intellectuelles', 'Prestations intellectuelles'),
        ('demande_proposition', 'Demande de proposition'),
        ('demande_cotation', 'Demande de cotation'),
        
        ('accord_cadre', 'Accord-cadre'),
        ('contrat_cadre', 'Contrat-cadre'),
    ], string='Mode de Passation', default='appel_offres')
    
    # === PARTIES PRENANTES ===
    titulaire_id = fields.Many2one(
        'res.partner', 
        string='Titulaire du Marché',
        domain=[('is_company', '=', True)],
        tracking=True,
        help="Entreprise ou entité titulaire du marché"
    )
    
    autorite_contractante_id = fields.Many2one(
        'res.partner', 
        string='Autorité Contractante',
        domain=[('is_company', '=', True)],
        tracking=True,
        help="Organisme public ou privé passant le marché"
    )
    
    commission_pasation_id = fields.Many2one(
        'res.partner',
        string='Commission de Passation',
        tracking=True,
        help="Commission responsable de la passation du marché"
    )
    
    # === DATE D'ENTREE EN VIGUEUR ===
    date_entree_vigueur = fields.Selection([
        ('date_signature', 'Date de Signature'),
        ('date_notification', 'Date de Notification'),
        ('date_remise_site', 'Date de Remise du Site'),
        ('date_ordre_debut', 'Date de l\'Ordre de Début'),
        ('date_paiement_avance', 'Date de Paiement de l\'Avance')
    ], string='Date d\'Entrée en Vigueur', required=True, default='date_signature')
    
    # === DATES CONTRACTUELLES ===
    date_signature = fields.Date(string='Date de Signature')
    date_notification = fields.Date(string='Date de Notification')
    date_remise_site = fields.Date(string='Date de Remise du Site')
    date_ordre_debut = fields.Date(string='Date de l\'Ordre de Début')
    date_paiement_avance = fields.Date(string='Date de Paiement de l\'Avance')
    date_debut_reel = fields.Date(
        string='Date de Début Réel',
        compute='_compute_date_debut_reel',
        store=True
    )

    date_fin_prevue = fields.Date(
        string='Date de Fin Prévue',
        compute='_compute_date_fin_prevue',
        store=True,
    )
    @api.depends('date_debut_reel', 'delai_contractuel_revise', 'delai_contractuel_unit')
    def _compute_date_fin_prevue(self):
        """Calcule la date de fin prévue basée sur la date de début et le délai révisé"""
        for project in self:
            if project.date_debut_reel and project.delai_contractuel_revise:
                # Convert delai_contractuel_revise to days
                delai_days = project._convert_delai_to_days(
                    project.delai_contractuel_revise,
                    project.delai_contractuel_unit
                )
                # Calculate end date
                project.date_fin_prevue = project.date_debut_reel + timedelta(days=delai_days)
            else:
                # If not computed, keep the manually set value or False
                project.date_fin_prevue = project.date_fin_prevue

    date_reception_provisoire = fields.Date(string='Date de Réception Provisoire')
    date_reception_definitive = fields.Date(string='Date de Réception Définitive')
    
    # === DELAIS ET AVANCEMENT ===
    delai_consomme = fields.Integer(
        string='Délai Consommé (jours)',
        compute='_compute_delai_consomme',
        store=True
    )
    delai_contractuel_value = fields.Integer(string="Délai Contractuel", required=True, default=1)
    delai_contractuel_unit = fields.Selection([("day", "Jours"), ("week", "Semaines"), ("month", "Mois"), ('year', 'Années')], string="Unité de mesure du delai", required=True, default='month')
    delai_restant = fields.Integer(
        string='Délai Restant (jours)',
        compute='_compute_delai_restant',
        store=True
    )
    avenant_count = fields.Integer(compute='_compute_avenant_count')
    # Compute methods
    
    @api.depends('avenant_ids')
    def _compute_avenant_count(self):
        for record in self:
            record.avenant_count = len(record.avenant_ids)
    
    
    @api.depends('update_ids', 'update_ids.progress_physique', 'update_ids.date_update')
    def _compute_last_update_and_progress(self):
        """Calcule la dernière mise à jour et l'avancement physique en une seule passe"""
        for project in self:
            if project.update_ids:
                # Récupérer la dernière mise à jour par date
                last_update = project.update_ids.sorted('date_update', reverse=True)[0]
                project.last_update_id = last_update.id
                project.progress_physique = last_update.progress_physique
            else:
                project.last_update_id = False
                project.progress_physique = 0.0



    
    # === INFORMATION FINANCIERE ===
    montant_contrat = fields.Monetary(currency_field='currency_id',string='Montant du Contrat', required=True)
    montant_avance_demarrage = fields.Monetary(currency_field='currency_id',string='Avance de Démarrage')
    montant_caution_bonne_execution = fields.Monetary(currency_field='currency_id', string='Caution Bonne Exécution')
    montant_caution_avance_demarrage = fields.Monetary(currency_field='currency_id', string='Caution Avance Démarrage')
    montant_frais_banque = fields.Monetary(currency_field='currency_id', string='Frais de Banque')
    # === CHAMPS FINANCIERS ===
    total_decaissements = fields.Monetary(currency_field='currency_id',
        string='Total Décaissements',
        compute='_compute_total_decaissements',
    )
    
    solde_a_recevoir = fields.Monetary(currency_field='currency_id',
        string='Solde à Recevoir',
        compute='_compute_solde_a_recevoir',
        store=True
    )

    
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
        
    # === INDICATEURS DE PERFORMANCE ===
    taux_decaissement = fields.Float(
        string='Taux de Décaissement (%)',
        compute='_compute_progress_financier',
    )
    
    
    # === ETAT ET STATUT ===
    state = fields.Selection([
        ('signe', 'Signé'),
        ('en_cours', 'En Cours d\'Exécution'),
        ('suspendu', 'Suspendu'),
        ('reception_provisoire', 'Réception Provisoire'),
        ('reception_definitive', 'Réception Définitive'),
        ('acheve', 'Achevé'),
        ('resilie', 'Résilié'),
    ], string="État du Projet", default='en_cours', tracking=True)
        
    
    
    # === OBSERVATIONS ET COMMENTAIRES ===
    observations_suivi = fields.Html(string='Observations et Suivi')
    
    # === COMPTE ANALYTIQUE ===
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Compte Analytique',
        copy=False,
        readonly=True
    )
    
    # === RELATIONS ===
    avenant_ids = fields.One2many('public.project.avenant', 'project_id', string='Avenants')
    sale_order_ids = fields.One2many('sale.order', 'partner_id', 'Sales Order')
    # === METHODES DE CALCUL ===
    
    @api.depends('date_entree_vigueur', 'date_signature', 'date_notification', 
                 'date_remise_site', 'date_ordre_debut', 'date_paiement_avance')
    def _compute_date_debut_reel(self):
        """Calcule la date de début réelle basée sur la sélection d'entrée en vigueur"""
        for project in self:
            date_debut = False
            if project.date_entree_vigueur == 'date_signature':
                date_debut = project.date_signature
            elif project.date_entree_vigueur == 'date_notification':
                date_debut = project.date_notification
            elif project.date_entree_vigueur == 'date_remise_site':
                date_debut = project.date_remise_site
            elif project.date_entree_vigueur == 'date_ordre_debut':
                date_debut = project.date_ordre_debut
            elif project.date_entree_vigueur == 'date_paiement_avance':
                date_debut = project.date_paiement_avance
            
            project.date_debut_reel = date_debut
    
    @api.depends(
    'date_debut_reel',
    'date_fin_prevue',
    'date_reception_definitive',
    'state'
    )
    def _compute_delai_consomme(self):
        """Calcule le délai consommé depuis la date d'entrée en vigueur"""
        today = date.today()
        for project in self:
            if project.date_debut_reel:
                if project.state in ['reception_definitive', 'acheve']:
                    # Si le projet est terminé, utiliser la date de fin réelle si disponible
                    end_date = project.date_reception_definitive or project.date_fin_prevue or today
                else:
                    end_date = today
                
                delta = end_date - project.date_debut_reel
                project.delai_consomme = max(delta.days, 0)
            else:
                project.delai_consomme = 0
    def _convert_delai_to_days(self, value, unit):
        """Convert delai from unit to days (same logic as in PublicProject)"""
        if unit == 'week':
            return value * 7
        elif unit == 'month':
            return value * 30  # Approximation: 30 days per month
        elif unit == 'year':
            return value * 365  # Approximation: 365 days per year
        return value  # Default to days (if unit is not specified)
    @api.depends('date_debut_reel', 'date_fin_prevue', 'delai_contractuel_revise', 'delai_contractuel_unit')
    def _compute_delai_restant(self):
        """Calcule le délai restant"""
        today = date.today()
        for project in self:
            if project.date_debut_reel and project.date_fin_prevue:
                # Calcul basé sur la date de fin prévue
                delta = project.date_fin_prevue - today
                project.delai_restant = max(delta.days, 0)
            elif project.delai_contractuel_revise and project.date_debut_reel:
                # Convert delai_contractuel_revise to days first
                delai_days = project._convert_delai_to_days(
                    project.delai_contractuel_revise,
                    project.delai_contractuel_unit
                )
                # Calcul basé sur le délai contractuel
                delta_fin_theorique = project.date_debut_reel + timedelta(days=delai_days)
                delta = delta_fin_theorique - today
                project.delai_restant = max(delta.days, 0)
            else:
                project.delai_restant = 0
    
    @api.depends('total_decaissements', 'montant_contrat_revise')
    def _compute_progress_financier(self):
        for project in self:
            project.taux_decaissement = (project.total_decaissements * 100/ project.montant_contrat_revise) if project.montant_contrat_revise else 0


    @api.depends('analytic_account_id', 'analytic_account_id.line_ids','analytic_account_id.line_ids.amount','analytic_account_id.debit')
    def _compute_total_decaissements(self):
        """Calcule le total des décaissements à partir des lignes analytiques"""
        for project in self:
            total_decaissements = 0.0
            if project.analytic_account_id and project.analytic_account_id.debit:
                total_decaissements =  project.analytic_account_id.debit
            project.total_decaissements = total_decaissements


    @api.depends('montant_contrat_revise', 'total_decaissements')
    def _compute_solde_a_recevoir(self):
        """Calcule le solde à recevoir"""
        for project in self:
            solde = project.montant_contrat_revise - project.total_decaissements
            project.solde_a_recevoir = max(solde, 0.0)
    
    @api.model
    def create(self, vals):
        """Crée automatiquement le compte analytique à la création du projet"""
        project = super().create(vals)
        if not project.analytic_account_id:
            analytic_account = self.env['account.analytic.account'].sudo().create({
                'name': f"{project.numero_marche} - {project.name}",
                'plan_id': self.env.ref('analytic.analytic_plan_projects').id,
            })
            project.analytic_account_id = analytic_account.id
        return project


    
    def action_view_financial(self):
        """Action pour visualiser la situation financière détaillée"""
        self.ensure_one()
        
        # Récupérer le compte analytique
        if not self.analytic_account_id:
            raise UserError(_('Aucun compte analytique n\'est associé à ce projet.'))
        
        # Retourner un tableau de bord financier personnalisé
        return {
            'type': 'ir.actions.act_window',
            'name': _('Situation Financière - %s') % self.name,
            'res_model': 'account.analytic.line',
            'view_mode': 'list,pivot,graph',
            'domain': [
                ('account_id', '=', self.analytic_account_id.id),
            ],
            
            'context': {
                'default_project_id': self.id,
                'default_account_id': self.analytic_account_id.id,
                'search_default_group_by_date': 1,
                'search_default_group_by_category': 1,
                'search_default_last_30_days': 1,
                'graph_measure': 'amount',
                'graph_mode': 'bar',
                'create':False,
                'edit':False,
                'delete':False
            },
            
        }
    
   
    # === ADDITIONAL SMART BUTTON ACTIONS ===
    
    def action_view_avenants(self):
        """Action pour visualiser les avenants du projet"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Avenants - %s') % self.name,
            'res_model': 'public.project.avenant',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_date_avenant': fields.Date.today(),
                'search_default_group_by_type': 1,
            },
            'target': 'current',
            # 'views': [
            #     (False, 'list'),
            #     (False, 'form')
            # ],
        }
    # === AVENANTS – IMPACT CONTRACTUEL ===


    montant_contrat_revise = fields.Monetary(
        currency_field='currency_id',
        string="Montant Contractuel Révisé",
        compute='_compute_avenant_totals',
        store=True
    )

    delai_contractuel_revise = fields.Integer(
        string="Délai Contractuel Révisé",
        compute='_compute_avenant_totals',
        store=True
    )
    def _convert_days_to_unit(self, days, unit):
        """Convert days to specified unit"""
        if unit == 'week':
            return days / 7
        elif unit == 'month':
            return days / 30  # Approximation: 30 days per month
        elif unit == 'year':
            return days / 365  # Approximation: 365 days per year
        return days  # If no unit specified or unit is days

    @api.depends(
        'montant_contrat',
        'delai_contractuel_value',  # Keep this
        'delai_contractuel_unit',   # Add this
        'avenant_ids.montant_ajustement',
        'avenant_ids.delai_ajustement_value',  # Change this
        'avenant_ids.delai_ajustement_unit',   # Add this
        'avenant_ids.state'
    )
    def _compute_avenant_totals(self):
        for project in self:
            # Filter avenants by confirmed state only
            confirmed_avenants = project.avenant_ids.filtered(
                lambda a: a.state == 'confirmed'
            )
            
            # Sum with safe defaults
            total_montant = sum(
                a.montant_ajustement 
                for a in confirmed_avenants 
                if a.montant_ajustement
            ) or 0.0
            
            # Calculate total delai in project's unit
            total_delai_adjustment = 0.0
            for avenant in confirmed_avenants:
                if avenant.delai_ajustement_value and avenant.delai_ajustement_unit:
                    # Convert avenant delai to project's unit
                    if avenant.delai_ajustement_unit == project.delai_contractuel_unit:
                        # Same unit, no conversion needed
                        total_delai_adjustment += avenant.delai_ajustement_value
                    else:
                        # Convert avenant unit to project's unit
                        # First convert avenant to days
                        avenant_days = avenant._convert_delai_to_days(
                            avenant.delai_ajustement_value,
                            avenant.delai_ajustement_unit
                        )
                        # Then convert days to project's unit
                        total_delai_adjustment += project._convert_days_to_unit(
                            avenant_days,
                            project.delai_contractuel_unit
                        )
            
            project.montant_contrat_revise = project.montant_contrat + total_montant
            project.delai_contractuel_revise = project.delai_contractuel_value + total_delai_adjustment
    

class PublicProjectAvenant(models.Model):
    _name = 'public.project.avenant'
    _description = 'Avenant au Contrat'
    _inherit = ['portal.mixin', 'mail.thread.main.attachment', 'mail.activity.mixin', 'account.document.import.mixin']
    name = fields.Char(string='Numéro Avenant', default=_lt("New"))
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
    ], string="Statut", default='draft', tracking=True)

    project_id = fields.Many2one('public.project', string='Projet', required=True)
    date_avenant = fields.Date(string='Date Avenant', required=True)
    objet = fields.Html(string='Objet de l\'Avenant', required=True)
    montant_ajustement = fields.Monetary(currency_field='currency_id',string='Ajustement Montant')
    delai_ajustement_value = fields.Integer(string='Ajustement Délai')
    delai_ajustement_unit = fields.Selection([
        ("day", "Jours"),
        ("week", "Semaines"),
        ("month", "Mois"),
        ('year', 'Années'),
    ], string="Unité de mesure du delai", default='month')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id')
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('project_id'):
                # Get the last sequence number for this project
                last_avenant = self.search(
                    [('project_id', '=', vals['project_id'])],
                    order='id desc',
                    limit=1
                )
                sequence = 1
                if last_avenant and last_avenant.name:
                    # Extract number from name like "AV-001", "Avenant 1", etc.
                    import re
                    numbers = re.findall(r'\d+', last_avenant.name)
                    if numbers:
                        sequence = int(numbers[-1]) + 1
                
                # Always generate name with sequence
                vals['name'] = f"AV-{sequence:03d}"
        
        return super().create(vals_list)
    def _convert_delai_to_days(self, value, unit):
        """Convert delai from unit to days (same logic as in PublicProject)"""
        if unit == 'week':
            return value * 7
        elif unit == 'month':
            return value * 30  # Approximation: 30 days per month
        elif unit == 'year':
            return value * 365  # Approximation: 365 days per year
        return value  # Default to days (if unit is not specified)
    @api.constrains('montant_ajustement', 'delai_ajustement_value')
    def _check_avenant_content(self):
        for rec in self:
            if not rec.montant_ajustement and not rec.delai_ajustement_value:
                raise ValidationError(
                    _("Un avenant doit modifier soit le montant soit le délai.")
                )

    