 # -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime, timedelta
from openerp.exceptions import UserError, ValidationError
import base64

class ExtendsFinancieraPrestamo(models.Model):
	_inherit = 'financiera.prestamo' 
	_name = 'financiera.prestamo'

	siro_pago_voluntario = fields.Boolean('Siro - Pago Voluntario')
	siro_cupon_sent = fields.Boolean('Siro - Cupon enviado por mail', default=False)

	@api.model
	def default_get(self, fields):
		rec = super(ExtendsFinancieraPrestamo, self).default_get(fields)
		if len(self.env.user.company_id.siro_id) > 0:
			rec.update({
				'siro_pago_voluntario': self.env.user.company_id.siro_id.set_default_payment,
			})
		return rec

	@api.one
	def siro_crear_codigo_barras(self):
		if self.siro_pago_voluntario:
			for cuota_id in self.cuota_ids:
				cuota_id.siro_generar_codigo_barras()

	@api.one
	def enviar_a_acreditacion_pendiente(self):
		super(ExtendsFinancieraPrestamo, self).enviar_a_acreditacion_pendiente()
		if self.siro_pago_voluntario:
			self.siro_crear_codigo_barras()

	@api.multi
	def siro_action_cupon_sent(self):
		""" Open a window to compose an email, with the edi payment template
			message loaded by default
		"""
		self.ensure_one()
		siro_id = self.company_id.siro_id
		template = siro_id.email_template_id
		compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
		report_name = siro_id.report_name
		pdf = self.pool['report'].get_pdf(self._cr, self._uid, [self.id], report_name, context=None)
		new_attachment_id = self.env['ir.attachment'].create({
			'name': 'Cuponera ' + self.display_name + '.pdf',
			'datas_fname': 'Cuponera ' + self.display_name + '.pdf',
			'type': 'binary',
			'datas': base64.encodestring(pdf),
			'res_model': 'financiera.prestamo',
			'res_id': self.id,
			'mimetype': 'application/x-pdf',
		})
		ctx = dict(
			default_model='financiera.prestamo',
			default_res_id=self.id,
			default_use_template=bool(template),
			default_template_id=template and template.id or False,
			default_composition_mode='comment',
			default_attachment_ids=[new_attachment_id.id],
			sub_action='cupon_sent',
		)
		return {
			'name': _('Compose Email'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form.id, 'form')],
			'view_id': compose_form.id,
			'target': 'new',
			'context': ctx,
		}

	@api.one
	def siro_enviar_email_cuponera_prestamo(self):
		if len(self.company_id.siro_id) > 0:
			siro_id = self.company_id.siro_id
			if len(siro_id.email_template_id) > 0:
				template = siro_id.email_template_id
				report_name = siro_id.report_name
				if report_name:
					pdf = self.pool['report'].get_pdf(self._cr, self._uid, [self.id], report_name, context=None)
					new_attachment_id = self.env['ir.attachment'].create({
						'name': 'Cuponera ' + self.display_name+'.pdf',
						'datas_fname': 'Cuponera ' + self.display_name+'.pdf',
						'type': 'binary',
						'datas': base64.encodestring(pdf),
						'res_model': 'financiera.prestamo',
						'res_id': self.id,
						'mimetype': 'application/x-pdf',
					})
					template.attachment_ids = [(6, 0, [new_attachment_id.id])]
				# context = self.env.context.copy()
				template.send_mail(self.id, raise_exception=False, force_send=True)

	@api.multi
	def siro_cuponera_de_pagos_report(self):
		self.ensure_one()
		siro_id = self.company_id.siro_id
		if len(siro_id) > 0 and siro_id.report_name:
			return self.env['report'].get_action(self, siro_id.report_name)
		else:
			raise UserError("Reporte de cuponera no configurado.")
