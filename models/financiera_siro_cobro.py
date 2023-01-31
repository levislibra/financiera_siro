
from openerp import models, fields, api
from datetime import datetime, timedelta

class FinancieraSiroCobro(models.Model):
	_name = 'financiera.siro.cobro'

	_order = 'id desc'
	name = fields.Char('Nombre')
	partner_id = fields.Many2one('res.partner')
	cuota_id = fields.Many2one('financiera.prestamo.cuota', 'Cuota')
	total = fields.Float('Total')
	id_cobro = fields.Char('Id de cobro')
	fecha_cobro = fields.Date('Fecha de cobro')
	fecha_acreditacion = fields.Date('Fecha de acreditacion')
	payment_id = fields.Many2one('account.payment', 'Comprobante de cobro')
	company_id = fields.Many2one('res.company', 'Empresa', default=lambda self: self.env['res.company']._company_default_get('financiera.siro.cobro'))
	
	
