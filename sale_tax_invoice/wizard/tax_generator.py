# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
import logging
_logger = logging.getLogger(__name__)

class InvoiceGenerator(models.TransientModel):
    _name = 'account.invoice.generator'

    def generate_lines(self):
        _logger.info('********************** invoice %s' ,self.invoice_id)
        invoice=self.env.context.get('default_invoice_id', False)

        invoice_obj=self.env['account.move'].search([('id','=',invoice)])

        _logger.info('********************** invoice lines %s' ,invoice_obj.invoice_line_ids)
        val=[{'generator_id':self.id, 
                'quantity':line.quantity, 
                'product_uom_id':line.product_uom_id.id,
                'product_id': line.product_id.id,
                'price_unit': line.price_unit,
                'discount':line.discount,
                #'display_type': line.display_type,
                'sequence': line.sequence,
                'name': line.name,
                'invoice_line':line.id,          
                #'tax_ids': [(6, 0, line.tax_id.ids)],
                #'analytic_account_id': line.analytic_account_id.id,
                #'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                #'sale_line_ids': [(6, 0, line.sale_line_ids.ids)]
                } for line in invoice_obj.invoice_line_ids]
        result = self.env['move.generator.line'].create(val)
        _logger.info('********************** %s' ,result)
        for rec in result:
            _logger.info('********************** %s' ,rec.name)
            _logger.info('********************** %s' ,rec.generator_id)
        
        return result


    line_ids = fields.One2many('move.generator.line', 'generator_id', string='Generator Items',default=generate_lines)
    tax_sequence= fields.Char(string='Tax sequence')
    seperate_invoice = fields.Boolean(string='seperate invoice', default=True)
    invoice_id = fields.Many2one('account.move')

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(force_company=self.invoice_id.company_id.id, default_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
        invoice_vals = {
            'ref': self.invoice_id.ref or '',
            'type': 'out_invoice',
            'tax_sequence': self.tax_sequence,
            'is_final_invoice' : True,
            'narration': self.invoice_id.narration,
            'currency_id': self.invoice_id.currency_id.id,
            'campaign_id': self.invoice_id.campaign_id.id,
            'medium_id': self.invoice_id.medium_id.id,
            'source_id': self.invoice_id.source_id.id,
            'invoice_user_id': self.invoice_id.user_id and self.env.user.id,
            'team_id': self.invoice_id.team_id.id,
            'partner_id': self.invoice_id.partner_id.id,
            'partner_shipping_id': self.invoice_id.partner_shipping_id.id,
            'fiscal_position_id': self.invoice_id.fiscal_position_id.id or False,
            'invoice_origin': self.invoice_id.invoice_origin,
            'invoice_payment_term_id': self.invoice_id.invoice_payment_term_id.id,
            'invoice_payment_ref': self.invoice_id.invoice_payment_ref,
            #'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
        }
        return invoice_vals


    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        return {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }

    

    def create_final_invoice(self):
        invoice= self.env.context.get('active_id')
        invoice=self.env['account.move'].browse([invoice])
        line_vals=[]
        # Invoice values.
        invoice_vals = self._prepare_invoice()
        for line in self.line_ids:
            if line.new_qty>0:
                line_vals.append({
            #'display_type': line.display_type,
            'sequence': line.sequence,
            'name': line.name,
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom_id.id,
            'quantity': line.new_qty,
            'discount': line.discount,
            'price_unit': line.price_unit,
            #'tax_ids': [(6, 0, line.invoice_line.tax_ids.ids)],
            'analytic_account_id': line.invoice_line.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, line.invoice_line.analytic_tag_ids.ids)],
            'sale_line_ids': [(6, 0, line.invoice_line.sale_line_ids.ids)]
            })
        invoice_vals['invoice_line_ids']=line_vals
        moves = self.env['account.move'].with_context(check_move_validity=False).create(invoice_vals)
        
        if moves:
            sale_order= self.env['sale.order'].search([('invoice_ids','in', self.invoice_id.id)])
            sale_order.write({'invoice_ids':[(4,moves.id)]})


            for line in self.line_ids.filtered(lambda x: x.new_qty>0):
                #line.invoice_line.with_context(check_move_validity=False).write({'quantity':line.invoice_line.quantity-line.new_qty})
                #self.invoice_id._recompute_dynamic_lines()
                self.invoice_id.write({'final_invoice_id':moves[0].id,'invoice_line_ids':[(1,line.invoice_line.id,{'quantity':line.invoice_line.quantity-line.new_qty})]})

                self.invoice_id._compute_amount()
                






        '''
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('partner_id'), x.get('currency_id'))):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs),
                    'invoice_origin': ', '.join(origins),
                    'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Manage 'final' parameter: transform out_invoice to out_refund if negative.
        out_invoice_vals_list = []
        refund_invoice_vals_list = []
        if final:
            for invoice_vals in invoice_vals_list:
                if sum(l[2]['quantity'] * l[2]['price_unit'] for l in invoice_vals['invoice_line_ids']) < 0:
                    for l in invoice_vals['invoice_line_ids']:
                        l[2]['quantity'] = -l[2]['quantity']
                    invoice_vals['type'] = 'out_refund'
                    refund_invoice_vals_list.append(invoice_vals)
                else:
                    out_invoice_vals_list.append(invoice_vals)
        else:
            out_invoice_vals_list = invoice_vals_list
            '''




class InvoiceGeneratorDetails(models.TransientModel):
    _name = 'move.generator.line'


    generator_id = fields.Many2one('account.invoice.generator', string='Generator')
    name = fields.Char(string='Label')
    quantity = fields.Float(string='Quantity',
        default=1.0, digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.")
    new_qty = fields.Float(string='New Quantity',
        default=1.0, digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.")
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    sequence = fields.Integer(default=10)
    invoice_line= fields.Many2one('account.move.line')
