 # -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime, timedelta
from openerp.exceptions import UserError, Warning
import requests

import logging
_logger = logging.getLogger(__name__)

TEST_AUTH_API_URL = "https://apisesionhomologa.bancoroela.com.ar:49221/auth/Sesion"
PROD_AUTH_API_URL = "https://apisesionhomologa.bancoroela.com.ar:49221/auth/Sesion"

TEST_API_SIRO_URL = "https://apisirohomologa.bancoroela.com.ar:49220"
PROD_API_SIRO_URL = "https://apisirohomologa.bancoroela.com.ar:49220"

EMPRESA_SERVICIO = "0447"
IDENTIFICADOR_CONCEPTO = "0"
RELLENO = "0000000000000000000000000000000"

class FinancieraSiroConfig(models.Model):
	_name = 'financiera.siro.config'

	name = fields.Char('Nombre')
	company_id = fields.Many2one('res.company', 'Empresa', default=lambda self: self.env['res.company']._company_default_get('financiera.siro.config'))
	state = fields.Selection([('test', 'Test'), ('produccion', 'Produccion')], 'Estado', default='test')
	usuario = fields.Char('Usuario')
	password = fields.Char('Password')
	token = fields.Text('Token')
	token_expires = fields.Datetime('Token - Fecha de expiracion')
	# Configuracion codigo de barras
	codigo_barras = fields.Boolean('Generar codigo de barras')
	empresa_servicio = fields.Char('Empresa de Servicio', default=EMPRESA_SERVICIO, help="4 dígitos que no varían, otorgado por SIRO.")
	identificador_concepto = fields.Char('Identificador Concepto', default=IDENTIFICADOR_CONCEPTO)
	identificador_cuenta = fields.Char('Identificador Cuenta')
	
	journal_id = fields.Many2one('account.journal', 'Diario de Cobro', domain="[('type', 'in', ('cash', 'bank'))]")
	factura_electronica = fields.Boolean('Factura electronica')

	set_default_payment = fields.Boolean("Marcar como medio de pago por defecto")
	email_template_id = fields.Many2one('mail.template', 'Plantilla de cuponera')
	report_name = fields.Char('Pdf adjunto en email')

	def get_auth_url(self):
		self.ensure_one()
		if self.state == 'produccion':
			return PROD_AUTH_API_URL
		elif self.state == 'test':
			return TEST_AUTH_API_URL

	def get_api_siro_url(self):
		self.ensure_one()
		if self.state == 'produccion':
			return PROD_API_SIRO_URL
		elif self.state == 'test':
			return TEST_API_SIRO_URL
		else:
			raise UserError(_("Siro is disabled"))

	@api.one
	def siro_get_token(self):
		print("siro_get_token")
		# self.ensure_one()
		print("self.token_expires: ", self.token_expires)
		print("fields.Datetime.now(): ", fields.Datetime.now())
		if self.token and self.token_expires and self.token_expires > fields.Datetime.now():
			print("No se renueva el token")
			return self.token
		else:
			api_url = self.get_auth_url()

			request_data = {
				"Usuario": self.usuario,
				"Password": self.password
			}

			response = requests.post(api_url, json=request_data)

			if response.status_code == 200:
				print("response 200")
				res = response.json()
				print("res: ", res)
				if 'access_token' in res:
					self.token = res['access_token']
					self.token_expires = datetime.now() + timedelta(seconds=res['expires_in'] - 20)
				elif 'error' in res:
					raise UserError(_("Siro error: %s" % res['error_description']))
				return res['access_token']
			else:
				raise UserError(_("Siro can't login"))

	@api.onchange('state')
	def _onchange_state(self):
		self.token = False
		self.token_expires = False

	@api.one
	def test_siro_connection(self):
		raise Warning("El token es %s" % self.siro_get_token())
