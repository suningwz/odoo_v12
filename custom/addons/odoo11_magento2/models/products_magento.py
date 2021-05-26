# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

import itertools
import psycopg2
import logging

from odoo import models, api, fields, tools, exceptions, _

logger = logging.getLogger(__name__)


class ProductTemplateMagento(models.Model):
    _inherit = 'product.template'

    magento_id = fields.Char(string="Magento id of the product", readonly=True,
                             store=True)
    magento = fields.Boolean(string="Magento", readonly=True, store=True,
                             help="This product is created from magento.")
    magento_categ_ids = fields.One2many('magento.product.category',
                                        'product_tmpl_id',
                                        string="Magento Categories",
                                        readonly=True)
    magento_type = fields.Char(string="Type of Product in Magento",
                               readonly=True, store=True)
    custom_option = fields.Boolean(string="Custom Option", default=False)

    @api.multi
    def create_variant_ids(self):
        Product = self.env["product.product"]
        AttributeValues = self.env['product.attribute.value']
        for tmpl_id in self.with_context(active_test=False):
            # adding an attribute with only one value should not recreate product
            # write this attribute on every product to make sure we don't lose them
            variant_alone = tmpl_id.attribute_line_ids.filtered(
                lambda line: (line.attribute_id.create_variant
                              or line.attribute_id.magento) and len(
                    line.value_ids) == 1).mapped('value_ids')
            for value_id in variant_alone:
                updated_products = tmpl_id.product_variant_ids.filtered(lambda
                                                                            product: value_id.attribute_id not in product.mapped(
                    'attribute_value_ids.attribute_id'))
                updated_products.write(
                    {'attribute_value_ids': [(4, value_id.id)]})

            # iterator of n-uple of product.attribute.value *ids*
            variant_matrix = [
                AttributeValues.browse(value_ids)
                for value_ids in itertools.product(
                    *(line.value_ids.ids for line in tmpl_id.attribute_line_ids
                      if line.value_ids[:1].attribute_id.create_variant
                      or line.value_ids[:1].attribute_id.magento))
            ]

            # get the value (id) sets of existing variants
            existing_variants = {frozenset(
                variant.attribute_value_ids.filtered(lambda r: (
                        r.attribute_id.create_variant or r.attribute_id.magento)).ids)
                for variant in tmpl_id.product_variant_ids}
            # -> for each value set, create a recordset of values to create a
            #    variant for if the value set isn't already a variant
            to_create_variants = [
                value_ids
                for value_ids in variant_matrix
                if set(value_ids.ids) not in existing_variants
            ]

            # check product
            variants_to_activate = self.env['product.product']
            variants_to_unlink = self.env['product.product']
            for product_id in tmpl_id.product_variant_ids:
                if not product_id.active and product_id.attribute_value_ids.filtered(
                        lambda r: (
                                r.attribute_id.create_variant or r.attribute_id.magento)) in variant_matrix:
                    variants_to_activate |= product_id
                elif product_id.attribute_value_ids.filtered(lambda r: (
                        r.attribute_id.create_variant or r.attribute_id.magento)) not in variant_matrix:
                    variants_to_unlink |= product_id
            if variants_to_activate:
                variants_to_activate.write({'active': True})

            # create new product
            for variant_ids in to_create_variants:
                new_variant = Product.create({
                    'product_tmpl_id': tmpl_id.id,
                    'attribute_value_ids': [(6, 0, variant_ids.ids)]
                })

            # unlink or inactive product
            for variant in variants_to_unlink:
                try:
                    with self._cr.savepoint(), tools.mute_logger(
                            'odoo.sql_db'):
                        variant.unlink()
                # We catch all kind of exception to be sure that the operation doesn't fail.
                except (psycopg2.Error, exceptions.except_orm):
                    variant.write({'active': False})
                    pass
        return True


class ProductVariantMagento(models.Model):
    _inherit = 'product.product'

    magento_categ_ids = fields.One2many('magento.product.category',
                                        'product_id',
                                        string="Magento Categories",
                                        readonly=True)
    magento = fields.Boolean(string="Magento", readonly=True, store=True,
                             help="This product is created from magento.",
                             related='product_tmpl_id.magento')
    magento_id = fields.Char(string="Magento id of the product",
                             store=True)
    magento_type = fields.Char(string="Type of Product in Magento",
                               readonly=True, store=True)


class ProductCategMagento(models.Model):
    _inherit = 'product.category'

    magento = fields.Boolean(string="Magento", readonly=True, store=True,
                             help="This category is created from magento.")
    magento_id = fields.Integer(string="Magento id of the category",
                                readonly=True,
                                store=True)


class MagentoCategory(models.Model):
    _name = 'magento.product.category'
    _rec_name = 'categ_name'

    name = fields.Many2one('product.category', string="Category")
    categ_name = fields.Char(string="Actual Name", related='name.name')
    product_tmpl_id = fields.Many2one('product.template', string="Product")
    product_id = fields.Many2one('product.product', string="Product")


class ProductAttributeExtended(models.Model):
    _inherit = 'product.attribute'

    magento = fields.Boolean(string="Magento", store=True, readonly=True)
    attribute_set_id = fields.Integer(string="Ids")
    attribute_set = fields.Many2one('product.attribute.set')


class ProductAttributeValueExtended(models.Model):
    _inherit = 'product.attribute.value'

    magento = fields.Boolean(string="Magento", store=True, readonly=True)


class ProductAttributeSet(models.Model):
    _name = 'product.attribute.set'

    magento = fields.Boolean(string="Magento", store=True, readonly=True)
    name = fields.Char('Attribute Set')
    code = fields.Char('Code')
    attribute_rel = fields.One2many('product.attribute', 'attribute_set', string="Attributes")
