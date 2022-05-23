# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT

class sale_order(models.Model):
    _inherit = 'sale.order'

    is_remain = fields.Boolean('Remain', )
    
    