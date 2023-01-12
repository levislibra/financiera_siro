# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime, timedelta, date
import logging
import math

_logger = logging.getLogger(__name__)


RELLENO = "0000000000000000000000000000000"
SECUENCIA_VERIFICADORA = [
	1,3,5,9,3,5,9,3,5,9,
	3,5,9,3,5,9,3,5,9,3,
	5,9,3,5,9,3,5,9,3,5,
	9,3,5,9,3,5,9,3,5,9,
	3,5,9,3,5,9,3,5,9,3,
	5,9,3,5
]
DIGITO_VERIFICADOR_ADICIONAL = 9

class ExtendsFinancieraPrestamoCuota(models.Model):
	_inherit = 'financiera.prestamo.cuota' 
	_name = 'financiera.prestamo.cuota'

	siro_codigo_barras = fields.Char(string='Codigo de Barras')
	siro_codigo_barras_transform = fields.Char(string='Codigo de Barras Transformado')

	# static function create_codebar_font($string_code) {

	# 	$code_numbers = str_split($string_code, 2);

	# 	$returning_codebar_font = 'Ë';
	# 	foreach ($code_numbers as $key => $number) {
	# 		if ($number > 93) {
	# 			$returning_codebar_font = $returning_codebar_font . chr(intval($number)+103);
	# 		} else {
	# 			$returning_codebar_font = $returning_codebar_font . chr(intval($number)+33);
	# 		}
			
	# 	}
	# 	$returning_codebar_font = $returning_codebar_font . 'Ì';
	# 	$returning_codebar_font = RoelaBarcodeUtils::replace_special_characters($returning_codebar_font);
		
	# 	return $returning_codebar_font;
	# }


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
		_logger.info("Generando Codigo de Barras")
		siro_id = self.company_id.siro_id
		primer_digito_verificador = 0
		segundo_digito_verificador = 0
		if siro_id and siro_id.codigo_barras:
			codigo_barras = siro_id.empresa_servicio
			codigo_barras += siro_id.identificador_concepto
			codigo_barras += str(self.id).zfill(8)
			codigo_barras += RELLENO
			codigo_barras += siro_id.identificador_cuenta
		print("Codigo de Barras: " + codigo_barras)
		suma_de_productos = 0
		i = 0
		for digito in SECUENCIA_VERIFICADORA:
			suma_de_productos += digito * int(codigo_barras[i])
			i += 1
		_logger.info("suma_de_productos: %s" % str(suma_de_productos))
		primer_digito_verificador = math.trunc(suma_de_productos / 2)
		primer_digito_verificador = primer_digito_verificador % 10
		codigo_barras += str(primer_digito_verificador)
		suma_de_productos = suma_de_productos + primer_digito_verificador * DIGITO_VERIFICADOR_ADICIONAL
		segundo_digito_verificador = math.trunc(suma_de_productos / 2)
		segundo_digito_verificador = segundo_digito_verificador % 10
		codigo_barras += str(segundo_digito_verificador)
		print("Codigo de Barras: " + codigo_barras)
		self.siro_codigo_barras = codigo_barras
		self.siro_codigo_barras_transform = self.create_codebar_font("04440000132671207300093700060098385000000000515000934600")