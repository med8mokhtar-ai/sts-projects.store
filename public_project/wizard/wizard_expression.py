from odoo import models, fields, Command

class WizardAddProductTemplate(models.TransientModel):
    _name = "wizard.add.product.template"
    _description = "Add Products to Quotation Template"

    template_id = fields.Many2one(
        'sale.order.template',
        string="Quotation Template",
        required=True
    )

    product_ids = fields.Many2many(
        'product.template',
        string="Produits",
        readonly=True
    )

    def action_add_products(self):
        self.ensure_one()

        self.template_id.write({
            'sale_order_template_line_ids': [
                Command.create({
                    'product_id': product.product_variant_id.id,
                    'name': product.name,
                    'product_uom_id': product.uom_id.id,
                    # 'price_unit': product.list_price,
                })
                for product in self.product_ids
            ]
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotation Template',
            'res_model': 'sale.order.template',
            'view_mode': 'form',
            'res_id': self.template_id.id,
            'target': 'current',
        }