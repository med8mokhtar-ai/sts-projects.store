{
    'name': 'Public Project',
    'version': '1.0',
    'author': 'Mohamed Almoukhter Mohamed',
    'website': 'https://github.com/med8mokhtar-ai',
    'category': 'Services/Project',
    'summary': 'Custom module to manage public projects with advanced tracking',
    'description': """
        Public Project Management
        ========================
        
        Comprehensive public project management system with:
        - Project lifecycle management
        - Budget and financial tracking
        - Progress monitoring (physical & financial)
        - Timeline and deadline management
        - Purchase and material tracking
        - Advanced reporting and analytics
    """,
    'depends': [
        'analytic',
        'base_setup',
        'mail',
        'portal',
        'rating',
        'resource',
        'web',
        'web_tour',
        'digest',
        'purchase',
        'sale'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/public_project_views.xml',
        'views/project_menus_actions.xml',
        'views/purchase_order_views.xml',
        'views/public_project_avenant_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}