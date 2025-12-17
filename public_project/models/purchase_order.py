from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    project_id = fields.Many2one('public.project', string="Projet")
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        related='project_id.analytic_account_id',
        store=True,
        string="Compte Analytique"
    )
    categ_ids = fields.Many2many(
        'product.category',
        string="Catégories",
        help="Sélectionnez pour filtrer et grouper les produits"
    )
    @api.onchange('project_id')
    def _onchange_project_id(self):
        """Propager le compte analytique à toutes les lignes"""
        for order in self:
            if order.project_id.analytic_account_id:
                analytic_id = order.project_id.analytic_account_id.id
                for line in order.order_line:
                    # Mettre 100% sur ce compte analytique
                    line.analytic_distribution = {str(analytic_id): 100.0}
            else:
                for line in order.order_line:
                    line.analytic_distribution = False

    @api.onchange('categ_ids')
    def _onchange_categ_ids(self):
        if not self.categ_ids:
            return

        Product = self.env['product.product']
        Category = self.env['product.category']

        lines = []
        sequence = 10  # start sequence

        analytic_distribution = False
        if self.analytic_account_id:
            analytic_distribution = {
                str(self.analytic_account_id.id): 100.0
            }

        categories = Category.search(
            [('id', 'child_of', self.categ_ids.ids)],
            order='parent_path'
        )

        for categ in categories:
            products = Product.search([
                ('categ_id', '=', categ.id),
                ('purchase_ok', '=', True),
            ])

            if not products:
                continue

            # 🔹 Section FIRST
            lines.append((0, 0, {
                'display_type': 'line_section',
                'name': categ.complete_name,
                'sequence': sequence,
            }))
            sequence += 1

            # 🔹 Products AFTER section
            for product in products:
                lines.append((0, 0, {
                    'product_id': product.id,
                    'name': product.display_name,
                    'product_qty': 0,
                    'product_uom_id': product.uom_id.id,
                    'price_unit': product.standard_price,
                    'date_planned': self.date_planned,
                    'sequence': sequence,
                    'analytic_distribution': analytic_distribution,
                }))
                sequence += 1

        self.order_line = [(5, 0, 0)] + lines
