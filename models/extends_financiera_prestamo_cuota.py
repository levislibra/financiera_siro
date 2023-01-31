# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime, timedelta, date
import logging
import math

_logger = logging.getLogger(__name__)


RELLENO = "0000000000000000000000000000000"
SECUENCIA_VERIFICADORA = [
	1,3,5,7,9,3,5,7,9,3,
	5,7,9,3,5,7,9,3,5,7,
	9,3,5,7,9,3,5,7,9,3,
	5,7,9,3,5,7,9,3,5,7,
	9,3,5,7,9,3,5,7,9,3,
	5,7,9,3
]
DIGITO_VERIFICADOR_ADICIONAL = 5

class ExtendsFinancieraPrestamoCuota(models.Model):
	_inherit = 'financiera.prestamo.cuota' 
	_name = 'financiera.prestamo.cuota'

	siro_codigo_barras = fields.Char(string='Codigo de Barras')
	siro_codigo_barras_transform = fields.Char(string='Codigo de Barras Transformado')

	def replace_special_characters(self, code):
		code = code.replace(chr(60) , "&#60;")
		code = code.replace(chr(61) , "&#61;")
		code = code.replace(chr(62) , "&#62;")
		code = code.replace(chr(63) , "&#63;")
		code = code.replace(chr(197) , "&#197;")
		code = code.replace(chr(198) , "&#198;")
		code = code.replace(chr(199) , "&#199;")
		code = code.replace(chr(200) , "&#200;")
		code = code.replace(chr(201) , "&#201;")
		code = code.replace(chr(202) , "&#202;")
		code = code.replace(chr(209) , "&#209;")
		return code
	
	def create_codebar_font(self, string_code):
		# separate string in two characters
		code_numbers = [string_code[i:i+2] for i in range(0, len(string_code), 2)]
		returning_codebar_font = '\313'
		for number in code_numbers:
			if int(number) > 93:
				returning_codebar_font = returning_codebar_font + chr(int(number)+103)
			else:
				returning_codebar_font = returning_codebar_font + chr(int(number)+33)
		returning_codebar_font = returning_codebar_font + "\314"
		return returning_codebar_font

	@api.one
	def siro_generar_codigo_barras(self):
		siro_id = self.company_id.siro_id
		primer_digito_verificador = 0
		segundo_digito_verificador = 0
		if siro_id and siro_id.codigo_barras:
			codigo_barras = siro_id.empresa_servicio
			codigo_barras += siro_id.identificador_concepto
			codigo_barras += str(self.id).zfill(8)
			codigo_barras += RELLENO
			codigo_barras += siro_id.identificador_cuenta
		suma_de_productos = 0
		i = 0
		for digito in SECUENCIA_VERIFICADORA:
			suma_de_productos += digito * int(codigo_barras[i])
			i += 1
		primer_digito_verificador = math.trunc(suma_de_productos / 2)
		primer_digito_verificador = primer_digito_verificador % 10
		codigo_barras += str(primer_digito_verificador)
		suma_de_productos = suma_de_productos + primer_digito_verificador * DIGITO_VERIFICADOR_ADICIONAL
		segundo_digito_verificador = math.trunc(suma_de_productos / 2)
		segundo_digito_verificador = segundo_digito_verificador % 10
		codigo_barras += str(segundo_digito_verificador)
		self.siro_codigo_barras = codigo_barras
		self.siro_codigo_barras_transform = self.create_codebar_font(codigo_barras)

	@api.one
	def siro_cobrar_y_facturar(self, payment_date, journal_id, factura_electronica, amount, invoice_date, punitorio_stop_date, solicitud_id=None):
		partner_id = self.partner_id
		fpcmc_values = {
			'partner_id': partner_id.id,
			'company_id': self.company_id.id,
		}
		multi_cobro_id = self.env['financiera.prestamo.cuota.multi.cobro'].create(fpcmc_values)
		partner_id.multi_cobro_ids = [multi_cobro_id.id]
		# Fijar fecha punitorio
		self.punitorio_fecha_actual = punitorio_stop_date
		if self.saldo > 0:
			self.confirmar_cobrar_cuota(payment_date, journal_id, amount, multi_cobro_id)
			if len(multi_cobro_id.payment_ids) > 0:
				if solicitud_id:
					solicitud_id.payment_id = multi_cobro_id.payment_ids[0]
		# Facturacion cuota
		if not self.facturada:
			fpcmf_values = {
				'invoice_type': 'interes',
				'company_id': self.company_id.id,
			}
			multi_factura_id = self.env['financiera.prestamo.cuota.multi.factura'].create(fpcmf_values)
			self.facturar_cuota(invoice_date, factura_electronica, multi_factura_id, multi_cobro_id)
			if multi_factura_id.invoice_amount == 0:
				multi_factura_id.unlink()
		multi_factura_punitorio_id = None
		if self.punitorio_a_facturar > 0:
			fpcmf_values = {
				'invoice_type': 'punitorio',
				'company_id': self.company_id.id,
			}
			multi_factura_punitorio_id = self.env['financiera.prestamo.cuota.multi.factura'].create(fpcmf_values)
			self.facturar_punitorio_cuota(invoice_date, factura_electronica, multi_factura_punitorio_id, multi_cobro_id)
			if multi_factura_punitorio_id != None and multi_factura_punitorio_id.invoice_amount == 0:
				multi_factura_punitorio_id.unlink()

