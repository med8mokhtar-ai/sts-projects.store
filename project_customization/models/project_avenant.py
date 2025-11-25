from odoo import api,fields, models,_
from odoo.exceptions import UserError, ValidationError
from datetime import date
from markupsafe import Markup

class ProjectAvenant(models.Model):
    _name = "project.avenant"
    _description = "Avenant du projet"
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
    ]
    _mail_post_access = 'read'
    _order = "id desc"
    _primary_email = 'email_from'
    _systray_view = 'activity'
    _track_duration_field = 'state'


    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )


    currency_id = fields.Many2one(
        related="company_id.currency_id",store=True,
        string="Currency",
    )

    description = fields.Html(string="Description")
    name = fields.Char(string='Titre', tracking=True, required=True)

    project_id = fields.Many2one('project.project', string="Projet", readonly=True)
    numero_marche = fields.Char(string="Numéro du marché",related="project_id.numero_marche",store=True)
    autorite_contractante=fields.Many2one('res.partner',related="project_id.autorite_contractante",store=True)
    titulaires = fields.Many2many('res.partner', string='Titulaire',  compute='_compute_titulaires', store=True)
    @api.depends('project_id.titulaires')
    def _compute_titulaires(self):
        for a in self.sudo():
            a.titulaires = a.project_id.titulaires
    market_type_id = fields.Many2one(string="Type du marché", store=True, related='project_id.market_type_id')
    funding_mode_ids = fields.Many2many('project.funding_mode', string='Sources de Financement',related="project_id.funding_mode_ids")
    date = fields.Date(string="Date",tracking=True,required=True,default=fields.Date.today())
    montant_initial = fields.Monetary(currency_field='currency_id', string='Montant du marché', group_operator="sum",related="project_id.montant_initial",store=True)
    amount = fields.Monetary(currency_field='currency_id',string="Montant d'avenant",tracking=True,group_operator="sum",
                             groups="",
                             )
    percentage = fields.Float(string="Pourcentage",compute='_compute_percentage',store=True,group_operator="avg", tracking=True)
    type_avenant = fields.Selection([('ordre_service','Ordre de service'),('avenant','Avenant')],
                                    string="Type d'avenant",required=True,tracking=True)
    color = fields.Integer(string='Color Index')

    #
    state = fields.Selection([('draft', 'Brouillon'), ('sent', 'Envoyé'), ('valide', 'Validé')],default="draft", string="Statut",group_expand='_expand_states', tracking=True)
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self.sudo()).state.selection]
    #Ebnou notes
    date_signature = fields.Date(string='Date signature')
    date_notification = fields.Date(string='Date notification')
    date_noti_deb_ex = fields.Date(string='Date de l’ordre de commencement des travaux')
    delai_execution = fields.Integer(string='Délai execution(jours)')
    funding_mode_ids_a = fields.Many2many('project.funding_mode', string='Sources de financement')
    regime_fiscal = fields.Selection([('ht','HT'),('ttc','TTC')], string='Régime fiscal')
    credit_impot = fields.Monetary(currency_field='currency_id', string='crédit impot')
    attachment_number = fields.Integer('Nombre de pièces jointes', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        totals =dict(
            self.env['ir.attachment'].sudo()._read_group(
            [('res_model', '=', 'project.avenant'), ('res_id', 'in', self.ids)],
            groupby=['res_id'],
            aggregates=['id:count'],
            )
        )
        
        self.attachment_number = totals.get(self.id) or 0
    @api.constrains('project_id', 'amount')
    def _check_avenent_amount(self):
        if self.project_id and self.amount:
            if self.project_id.montant_total_avenants_gap+self.project_id.montant_total_ordre_services_gap > 20:
                raise ValidationError(
                    "Le total des avenants doit être inférieur à 20%")
            if self.project_id.montant_total_ordre_services_gap > 10:
                raise ValidationError(
                    "Le total des ordres de service doit être inférieur à 10%")

    #______________________________________________________________________________________
   
    def action_back_to_draft(self):
        self.ensure_one()
        av_sudo = self.sudo()
        av_sudo.activity_unlink(["project_customization.mail_activity_data_feedback"])
        av_sudo.write({'state': 'draft'})
        if av_sudo.autorite_contractante:
            av_sudo.activity_schedule(
                activity_type_id=av_sudo.env.ref("project_customization.mail_activity_data_feedback").id,
                summary="Votre avenant '{}' a été rétabli en 'Brouillon'.".format(av_sudo.name),
                user_id=av_sudo.autorite_contractante.user_ids.ids[0],
                date_deadline=fields.Date.today()
            )

    def action_sent(self):
        self.ensure_one()
        av_sudo = self.sudo()
        # Close any open activities
        activity_type = av_sudo.env.ref("project_customization.mail_activity_data_feedback")
        
        av_sudo.activity_unlink(["project_customization.mail_activity_data_feedback"])  # This will close any open activities
        
        if not av_sudo.attachment_number:
            raise UserError("Vous devez joindre au moins un document vérifiant cette situation de l'avenant.")
        av_sudo.write({'state': 'sent'})
        # Notify the project user if it exists
        if av_sudo.project_id.user_id:
            user_id = av_sudo.project_id.user_id
            notification_message = (
                "Votre avenant '{}' du '{}' a été marqué comme 'Envoyé'."
                .format(av_sudo.name, av_sudo.project_id.name)
            )
            av_sudo.activity_schedule(
                activity_type_id=activity_type.id,
                summary=notification_message,
                user_id=user_id.id,
                date_deadline=fields.Date.today()
            )

    def action_confirm(self):
        self.ensure_one()
        av_sudo = self.sudo()
        av_sudo.activity_unlink(["project_customization.mail_activity_data_feedback"])
        av_sudo.write({'state': 'valide'})
        if av_sudo.project_id.autorite_contractante:
            email_body = Markup(
                "<div class='o_mail_notification o_hide_author'>"
                f"Veuillez être informé que votre avenant <b>{av_sudo.name}</b> du "
                f"<b>{av_sudo.project_id.name}</b> a été confirmé et validé.</div>"
            )
            av_sudo.project_id.autorite_contractante.message_post(
                body=email_body,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                partner_ids=av_sudo.project_id.autorite_contractante.user_ids.mapped('partner_id').ids,
            )


            
    def unlink(self):
        for record in self:
            if record.state in ['sent','valide']:
                raise ValidationError(_("Vous ne pouvez pas supprimer un avenant à l'état de validation et d'envoi."))
        return super().unlink()






    @api.depends('amount','montant_initial')
    def _compute_percentage(self):
        for record in self:
            if record.montant_initial!=0:
                record.percentage = record.amount*100/record.montant_initial
            else:
                record.percentage = 0
    @api.constrains('percentage','type_avenant','funding_mode_ids')
    def _check_percentage_ordre_service_and_avenant_less_than(self):
        for avenant in self:
            if self.env.ref('project_customization.funding_mode_0').id in avenant.project_id.funding_mode_ids.ids:
                if (avenant.project_id.montant_total_ordre_services_gap+avenant.project_id.montant_total_avenants_gap)>20:
                    raise ValidationError('Le total des avenants doit être inférieure à 20% du montant du marché')
                elif avenant.type_avenant=='ordre_service' and avenant.project_id.montant_total_ordre_services_gap+avenant.percentage>10:
                    raise ValidationError('Le total des ordres de service doit être inférieure à 10% du montant du marché')
                