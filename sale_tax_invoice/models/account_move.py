# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT


class account_move(models.Model):
    _inherit = 'account.move'


    tax_sequence= fields.Char(string='Tax sequence')
    is_final_invoice= fields.Boolean(string="Final invoice")
    final_invoice_id = fields.Many2one('account_move')

    def open_final_invoice(self):
        result ={}
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        result['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        result['context'] = {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'}
        for rec in self:
            result['res_id'] = rec.final_invoice_id.id        
            return result


    def print_final_invoice_report(self):
        return self.env.ref('sale_tax_invoice.report_print_final_invoice').report_action(self)