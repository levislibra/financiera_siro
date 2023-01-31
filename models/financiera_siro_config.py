 # -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime, timedelta
from openerp.exceptions import UserError, Warning
import requests
import logging
import json

import logging
_logger = logging.getLogger(__name__)

TEST_AUTH_API_URL = "https://apisesionhomologa.bancoroela.com.ar:49221/auth/Sesion"
PROD_AUTH_API_URL = "https://apisesion.bancoroela.com.ar:49221/auth/Sesion"

TEST_API_SIRO_URL = "https://apisirohomologa.bancoroela.com.ar:49220"
PROD_API_SIRO_URL = "https://apisiro.bancoroela.com.ar:49220/"

SIRO_LISTADO_PROCESO = "https://apisiro.bancoroela.com.ar:49220/siro/Listados/proceso"
SIRO_PAGO_ID = "https://apisiro.bancoroela.com.ar:49220/siro/Pagos/"

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
	empresa_cuit = fields.Char('Empresa CUIT')
	
	journal_id = fields.Many2one('account.journal', 'Diario de Cobro', domain="[('type', 'in', ('cash', 'bank'))]")
	factura_electronica = fields.Boolean('Factura electronica')

	set_default_payment = fields.Boolean("Marcar como medio de pago por defecto")
	cobros_days_check = fields.Integer('Dias para chequear cobros', default=7)
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
	def _siro_get_token(self):
		print("siro_get_token")
		# self.ensure_one()
		print("self.token_expires: ", self.token_expires)
		print("fields.Datetime.now(): ", fields.Datetime.now())
		# if self.token and self.token_expires and self.token_expires > fields.Datetime.now():
		# 	print("No se renueva el token")
		# 	return self.token
		# else:
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

	def siro_get_token(self):
		self.ensure_one()
		self._siro_get_token()
		return self.token

	@api.onchange('state')
	def _onchange_state(self):
		self.token = False
		self.token_expires = False

	@api.one
	def test_siro_connection(self):
		raise Warning("El token es %s" % self.siro_get_token())

	@api.one
	def siro_obtener_cobros(self):
		headers = {
			'Authorization': "Bearer " + self.siro_get_token(),
			'Content-type': 'application/json',
		}
		# fecha actual
		datenow = datetime.now()
		body = {
			'fecha_desde': (datenow - timedelta(days=self.cobros_days_check)).strftime("%Y/%m/%dT%H:%M:%S"),
			'fecha_hasta': (datenow - timedelta(hours=3)).strftime("%Y/%m/%dT%H:%M:%S"),
			'cuit_administrador': self.company_id.siro_id.empresa_cuit,
			'nro_empresa': self.company_id.siro_id.identificador_cuenta,
		}
		print("body: ", body)
		r = requests.post(SIRO_LISTADO_PROCESO, data=json.dumps(body), headers=headers)
		data = r.json()
		print("data: ", data)
		if 'Message' in data:
			raise UserError("Siro error: %s" % data['Message'])
		for cobro in data:
			# Id de cobro
			id_cobro_string = cobro[-46:-36]
			print("id_cobro_string: ", id_cobro_string)
			# Verifico si el cobro ya existe
			cobro_ids = self.env['financiera.siro.cobro'].search([
				('id_cobro', '=', id_cobro_string)
			])
			if not cobro_ids:
				fecha_cobro_string = cobro[0:8]
				fecha_cobro = datetime.strptime(fecha_cobro_string, '%Y%m%d')
				print("fecha_cobro: ", fecha_cobro)
				fecha_acreditacion_string = cobro[8:16]
				fecha_acreditacion = datetime.strptime(fecha_acreditacion_string, '%Y%m%d')
				print("fecha_acreditacion: ", fecha_acreditacion)
				# Para cupon abierto no hay fecha de vencimiento
				# fecha_vencimiento = cobro[16:24]
				# importe pagado es de 11 digitos, ultimos dos son decimales
				importe_pagado_string = cobro[24:35]
				importe_pagado = float(importe_pagado_string[:-2]) + float(importe_pagado_string[-2:])/100.0
				print("importe_pagado: ", importe_pagado)
				# 8 digitos, identificador de cuota
				nro_cuota_string = cobro[35:43]
				nro_cuota = int(nro_cuota_string)
				print("nro_cuota: ", nro_cuota)
				# crear cobro
				cobro_id = self.env['financiera.siro.cobro'].create({
					'name': 'COBRO/' + id_cobro_string,
					'id_cobro': id_cobro_string,
					'cuota_id': nro_cuota,
					'fecha_cobro': fecha_cobro,
					'fecha_acreditacion': fecha_acreditacion,
					'total': importe_pagado,
					'company_id': self.company_id.id,
				})
				journal_id = self.company_id.siro_id.journal_id
				factura_electronica = self.company_id.siro_id.factura_electronica
				cobro_id.cuota_id.siro_cobrar_y_facturar(fecha_cobro, journal_id, factura_electronica, importe_pagado, datetime.now(), fecha_cobro, cobro_id)