
from openerp import models, fields, api
from datetime import datetime, timedelta
import logging
import requests
import json

SIRO_LISTADO_PROCESO = "https://apisiro.bancoroela.com.ar:49220/siro/Listados/proceso"
SIRO_PAGO_ID = "https://apisiro.bancoroela.com.ar:49220/siro/Pagos/"

_logger = logging.getLogger(__name__)

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
	
	@api.one
	def siro_obtener_cobros(self):
		headers = {
			'Authorization': "Bearer " + self.company_id.siro_id.token,
			'Content-type': 'application/json',
		}
		body = {
			'fecha_desde': "2023-01-01T15:00:00.000Z",
			'fecha_hasta': "2023-01-27T15:00:00.000Z",
			'cuit_administrador': self.company_id.siro_id.empresa_cuit,
			'nro_empresa': self.company_id.siro_id.identificador_cuenta,
		}
		print("body: ", body)
		r = requests.post(SIRO_LISTADO_PROCESO, data=json.dumps(body), headers=headers)
		data = r.json()
		print("data: ", data)
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
				})
				journal_id = self.company_id.siro_id.journal_id
				factura_electronica = self.company_id.siro_id.factura_electronica
				cobro_id.cuota_id.siro_cobrar_y_facturar(fecha_cobro, journal_id, factura_electronica, importe_pagado, datetime.now(), fecha_cobro, self)
