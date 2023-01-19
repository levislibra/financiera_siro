# -*- coding: utf-8 -*-
{
    'name': "Financiera Siro (Banco Roela)",

    'summary': """
        Integracion con pasarela de cobros Siro del Banco Roela. Unicamente integra medios de pago voluntario.""",

    'description': """
        Integracion con pasarela de cobros Siro del Banco Roela. Unicamente integra medios de pago voluntario.
    """,

    'author': "Librasoft",
    'website': "https://libra-soft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','financiera_prestamos'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/extends_res_company.xml',
        'views/financiera_siro_config.xml',
        'views/extends_financiera_prestamo.xml',
        'views/extends_financiera_prestamo_cuota.xml',
        'views/generic_reports.xml',
    ],
    'css': [
		'static/src/css/siro.css',
	],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}