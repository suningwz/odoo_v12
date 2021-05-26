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

import requests
import logging
import base64
from odoo import models, fields, exceptions, _

logger = logging.getLogger(__name__)


class ProductsFetchWizard(models.Model):
    _name = 'products.fetch.wizard'

    fetch_type = fields.Selection([
        ('to_odoo', 'Fetch Products From Magento'),
        ('from_odoo', 'Update Products to Magento')
    ], string="Operation Type")

    def update_categories(self, categ_list):
        """Updating category list from magento to odoo"""
        p_id = None
        if not self.env['product.category'].search(
                [('magento_id', '=', categ_list['id'])]):
            if categ_list['children_data']:
                if categ_list['parent_id'] != 0:
                    self._cr.execute("select id from product_category "
                                     "where magento_id=%s",
                                     (categ_list['parent_id'],))
                    p_id = self._cr.fetchone()
            self.env['product.category'].create({
                'name': categ_list['name'],
                'parent_id': p_id[0] if p_id else None,
                'magento_id': categ_list['id'],
                'magento': True
            })
        for categ in categ_list['children_data']:
            self.update_categories(categ)
        return

    def fetch_query(self, vals):
        """constructing the query, from the provided column names"""
        query_str = ""
        if not vals:
            return
        for col in vals:
            query_str += " " + str(col) + ","
        return query_str[:-1]

    def _import_products_list(self,
                              config_products,
                              existing_prod_ids,
                              template,
                              attributes
                              ):
        """The aim of this function is to configure all the
         configurable products with their variants
         config_products: configurable products list from magento with their childs
         existing_prod_ids: products synced with magento
         template: required fields with their values for product template
         attributes: complete list of attributes from magento
         """
        VariantObj = self.env['product.product']
        cr = self._cr
        # fetching all the attributes and their values
        # dictionary of lists with attributes, values and id from magento
        # if this attribute is not synced with odoo, we will do it now
        cr.execute("select id, name from product_attribute where "
                   " name is not null")
        all_attrib = cr.fetchall()
        odoo_attributes = {}
        for j in all_attrib:
            if j[1] and j[0]:
                odoo_attributes[j[1]] = j[0]

        attributes_list = {}
        for att in attributes['items']:
            if att['attribute_code'] in odoo_attributes:
                # existing attribute
                attributes_list[str(att['attribute_id'])] = {
                    'id': odoo_attributes[att['attribute_code']],
                    # id of the attribute in odoo
                    'code': att['attribute_code'],  # label
                    'options': {}
                }
        # update attribute values
        cr.execute("select id, name from product_attribute_value "
                   " where name is not null")
        all_attrib_vals = cr.fetchall()
        odoo_attribute_vals = {}
        for j in all_attrib_vals:
            if j[1] and j[0]:
                odoo_attribute_vals[j[1]] = j[0]

        for att in attributes['items']:
            for option in att['options']:
                if option['label'] != ' ' and option['value'] != '' \
                        and option['label'] in odoo_attribute_vals \
                        and str(att['attribute_id']) in attributes_list:
                    value_rec = odoo_attribute_vals[option['label']]
                    # existing value
                    attributes_list[str(att['attribute_id'])]['options'][
                        option['value']] = value_rec
        product_ids = self.env['product.product'].search(
            [('custom_option', '=', True)])
        # default_code_lst = []
        cust_list = product_ids.mapped('default_code')
        # now the attributes list should be a dictionary with all the attributes
        # with their id and values both in odoo and magento+++++

        for product in config_products:
            if str(product['id']) not in existing_prod_ids:
                url = '/rest/V1/products/' + product['sku'] + '/options'
                cust_options = self.env[
                    'magento.connector'].magento_api_call(
                    headers={},
                    url=url,
                    type='GET'
                )
                if isinstance(cust_options, list):
                    for rec in cust_options:
                        if rec.get('values', False):
                            for val in rec.get('values', []):
                                if val.get('sku', False):
                                    if val.get('sku') not in cust_list:
                                        cust_val = self._update_custom_option(
                                            val,
                                            template,
                                            VariantObj,
                                            cr)
                                        cust_list.append(cust_val.default_code)

                        else:
                            if rec.get('sku', False):
                                if rec.get('sku') not in cust_list:
                                    cust_val = self._update_custom_option(rec,
                                                                          template,
                                                                          VariantObj,
                                                                          cr)
                                    cust_list.append(
                                        cust_val.default_code)

                product_categ_ids = []
                for attr in product.get('custom_attributes'):
                    if attr.get('attribute_code') == 'category_ids':
                        product_categ_ids = attr.get('value') or []

                # getting odoo's category id from the magento categ id
                # (which is already created)
                c_ids = []
                if product_categ_ids:
                    cr.execute("select id from product_category "
                               "where magento_id in %s",
                               (tuple(product_categ_ids),))
                    c_ids = cr.fetchall()

                template['name'] = product['name']
                template['magento_id'] = str(product['id'])
                template['type'] = 'product'
                template['active'] = True
                template['sale_ok'] = True
                template['purchase_ok'] = True
                template['magento'] = True
                template['default_code'] = product['sku']
                template['list_price'] = product.get('price') or 0
                template['magento_type'] = product.get('type_id') or 'simple'
                template['custom_option'] = False
                # creating products
                query_cols = self.fetch_query(template)
                query_str = "insert into product_template (" + query_cols + \
                            ") values %s RETURNING id"
                cr.execute(query_str,
                           (tuple(template.values()),))
                product_tmpl_id = cr.fetchone()
                image_file = False
                try:
                    for pic in product['media_gallery_entries']:
                        if 'thumbnail' in pic['types']:
                            image_file = product['media_gallery_entries'][0].get(
                                'file')
                            pro_tmpl = self.env['product.template'].browse(product_tmpl_id)
                            pro_tmpl.update({'image_medium': self.image_processing(image_file),
                                             'default_code': product['sku']})
                except:
                    logger.info("unable to import image url of product sku %s", product['sku'])
                    pass

                if product.get('type_id') == 'configurable':
                    # here we create template for main product and variants for
                    # the child products
                    product_tmpl_id and existing_prod_ids.append(
                        str(product['id']))

                    if product.get('childs'):
                        # since this product has childs, we need to fetch the
                        # variant options associated with this product
                        url = '/rest/V1/configurable-products/' + product[
                            'sku'] + '/options/all'
                        options = self.env[
                            'magento.connector'].magento_api_call(
                            headers={},
                            url=url,
                            type='GET'
                        )
                        # we are updating the attributes associated with this product
                        # (if it is not added to odoo already)
                        attributes_list = self._update_attributes(
                            attributes_list,
                            options,
                            attributes['items']
                        )
                        attrib_line = {}
                        child_file = False
                        for child in product['childs']:
                            variant_categ_ids = []
                            variant_att_vals = []
                            for option in options:
                                att_id = option['attribute_id']
                                current_att_id = attributes_list[att_id]['id']
                                if current_att_id not in attrib_line:
                                    attrib_line[current_att_id] = []
                                att_code = attributes_list[att_id]['code']
                                att_options = attributes_list[att_id][
                                    'options']
                                for att in child.get('custom_attributes'):
                                    if att['attribute_code'] =='image':
                                        child_file = att['value']
                                    if att['attribute_code'] == att_code:
                                        variant_att_vals.append(
                                            att_options[att['value']])
                                        attrib_line[current_att_id].append(
                                            att_options[att['value']]) \
                                            if att_options[att['value']] not in \
                                               attrib_line[current_att_id] \
                                            else None
                                    elif att[
                                        'attribute_code'] == 'category_ids':
                                        variant_categ_ids = attr.get(
                                            'value') or []
                            # creating variants
                            if str(child['id']) not in existing_prod_ids:
                                prod_id = VariantObj.create({
                                    'product_tmpl_id': product_tmpl_id[0],
                                    'attribute_value_ids': [
                                        (6, 0, variant_att_vals)],
                                    'lst_price': child.get('price') or 0,
                                    'magento': True,
                                    'active': True,
                                    'magento_id': str(child['id']),
                                    'default_code': child['sku'],
                                    'magento_type': 'simple',
                                    'image': self.image_processing(child_file)
                                })
                                logger.info("product created %s", prod_id)
                                prod_id and existing_prod_ids.append(
                                    str(child['id']))
                        for line in attrib_line:
                            cr.execute(
                                "insert into product_template_attribute_line "
                                "(attribute_id, product_tmpl_id) "
                                "values(%s, %s) returning id",
                                (line, product_tmpl_id[0]))
                            line_id = cr.fetchone()
                            line_rec = self.env[
                                'product.template.attribute.line'].search(
                                [('id', '=', line_id[0])],
                                limit=1)
                            if attrib_line[line]:
                                line_rec.write({
                                    'value_ids': [(6, 0, attrib_line[line])]
                                })

                else:
                    prod_id = VariantObj.create({
                        'product_tmpl_id': product_tmpl_id[0],
                        'magento': True,
                        'magento_id': str(product['id']),
                        'default_code': product['sku'],
                        'magento_type': product.get('type_id') or 'simple',
                        'custom_option': False,
                        'image': self.image_processing(image_file)
                    })
                    logger.info("product created %s", prod_id)
                    prod_id and existing_prod_ids.append(str(product['id']))

                for categ in c_ids:
                    cr.execute("insert into magento_product_category(name,"
                               "product_tmpl_id)"
                               " values (%s,%s)",
                               (categ[0], product_tmpl_id[0]))

        return existing_prod_ids

    def _update_custom_option(self, val, template, VariantObj, cr):
        template['name'] = val['sku']
        template['magento_id'] = str(
            val['option_type_id']) if 'option_type_id' in val else str(
            val['option_id'])
        template['type'] = 'consu'
        template['active'] = True
        template['sale_ok'] = True
        template['purchase_ok'] = True
        template['magento'] = True
        template['default_code'] = val['sku']
        template['list_price'] = val.get(
            'price') or 0
        template['magento_type'] = 'simple'
        template['custom_option'] = True

        query_cols = self.fetch_query(template)
        query_str = "insert into product_template (" + query_cols + \
                    ") values %s RETURNING id"
        cr.execute(query_str,
                   (tuple(template.values()),))
        product_custom_tmpl_id = cr.fetchone()

        custom_option_id = VariantObj.create({
            'product_tmpl_id':
                product_custom_tmpl_id[0],
            'magento': True,
            'magento_id': str(
                val['option_type_id']) if 'option_type_id' in val else str(
                val['option_id']),
            'default_code': val['sku'],
            'magento_type': 'simple',
            'custom_option': True,
        })

        return custom_option_id

    def _update_attributes(self, odoo_attributes, options, attributes):
        cr = self._cr
        options = [i['attribute_id'] for i in options]
        for att in attributes:
            if str(att['attribute_id']) not in odoo_attributes and str(
                    att['attribute_id']) in options:
                cr.execute(
                    "insert into product_attribute (name,create_variant,type,magento) "
                    " values(%s, FALSE, 'radio', TRUE) returning id",
                    (att['attribute_code'],))
                rec_id = cr.fetchone()
                odoo_attributes[str(att['attribute_id'])] = {
                    'id': rec_id[0],  # id of the attribute in odoo
                    'code': att['attribute_code'],  # label
                    'options': {}
                }
            # attribute values
            if str(att['attribute_id']) in options:
                odoo_att = odoo_attributes[str(att['attribute_id'])]
                for opt in att['options']:
                    if opt['label'] and opt['value'] \
                            and opt['value'] not in odoo_att['options']:
                        # if opt['value'][0]['value_index']
                        cr.execute(
                            "insert into product_attribute_value (name, attribute_id,magento)  "
                            "values(%s, %s, TRUE) returning id",
                            (opt['label'], odoo_att['id']))
                        rec_id = cr.fetchone()
                        odoo_att['options'][str(opt['value'])] = rec_id[
                            0]  # linking id in magento with id in odoo
        return odoo_attributes

    def fetch_products(self):
        """Fetch products"""
        if self.fetch_type == 'to_odoo':
            # fetch products to odoo
            self.fetch_products_to_odoo()

        elif self.fetch_type == 'from_odoo':
            # update products to magento
            # we will select all the products which are created locally
            self.fetch_products_from_odoo()


    def get_product_data(self):
        catalog_data = []
        products = self.env['product.product'].search([
            ('magento', '=', False),
            ('default_code', '!=', None)
        ])

        if products:
            for product in products:
                product_data = {
                    "sku": product.default_code,
                    "name": product.name,
                    "price": product.list_price,
                    "attribute_set_id": 4,
                    "type_id": "simple"
                }
                catalog_data.append({"product": product_data})
        return catalog_data and [catalog_data, products] or None

    def find_default_vals(self, model_name):
        """
        Finds the default, required, database persistant fields for the model provided.
        Useful for creating records using query.
        """
        cr = self._cr
        cr.execute("select id from ir_model "
                   "where model=%s",
                   (model_name,))
        model_res = cr.fetchone()

        if not model_res:
            return
        cr.execute("select name from ir_model_fields "
                   "where model_id=%s and required=True "
                   " and store=True",
                   (model_res[0],))
        res = cr.fetchall()
        fields_list = [i[0] for i in res if res] or []
        Obj = self.env[model_name]
        default_vals = Obj.default_get(fields_list)

        return default_vals

    def fetch_products_to_odoo(self):
        existing_ids = []
        cr = self._cr
        # fetching products already fetched from magento to skip those already created
        cr.execute("select magento_id from product_template "
                   "where magento_id is not null ")
        products = cr.fetchall()
        ids = [str(i[0]) for i in products] if products else []

        cr.execute("select magento_id from product_product "
                   "where magento_id is not null")
        products = cr.fetchall()
        for i in products:
            ids.append(i[0]) if i[0] not in ids else None

        # in magento, each product can have more than one category, so we are fetching all the categories
        # from magento
        # and creating those in odoo. For the products updated from magento,
        # we will be showing all the magento categories in a separate field
        categ_url = '/index.php/rest/V1/categories'
        type = 'GET'
        categ_list = self.env['magento.connector'].magento_api_call(
            headers={}, url=categ_url, type=type)
        try:
            # updating categories from magento to odoo
            self.update_categories(categ_list)

        except Exception as e:
            logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)

        # fetching products other than configurable products

        # fetching configurable products
        url = '/rest/V1/products?searchCriteria[filter_groups][0][filters][0]' \
              '[field]=type_id&searchCriteria[filter_groups][0][filters]' \
              '[0][value]=configurable'
        type = 'GET'
        configurable_products = self.env[
            'magento.connector'].magento_api_call(
            headers={},
            url=url,
            type=type
        )

        url = '/rest/V1/products?searchCriteria[filter_groups][0][filters][0]' \
              '[field]=type_id&searchCriteria[filter_groups][0][filters]' \
              '[0][value]=configurable&' \
              'searchCriteria[filter_groups][0][filters][0][condition_type]=' \
              'neq'
        type = 'GET'
        simple_products = self.env['magento.connector'].magento_api_call(
            headers={},
            url=url,
            type=type
        )

        url = '/rest/V1/products/attributes?searchCriteria=0'
        attributes = self.env['magento.connector'].magento_api_call(
            headers={},
            url=url,
            type='GET'
        )
        try:
            tmpl_vals = self.find_default_vals('product.template')
            simple_products_list = simple_products['items']
            if simple_products_list:
                existing_ids = self._import_products_list(
                    simple_products_list,
                    ids,
                    tmpl_vals,
                    attributes,
                )
                # end syncing simple products
            # fetching child products of configurable products
            config_prod_list = configurable_products['items']
            url = '/rest/V1/configurable-products/{sku}/children'
            for config in config_prod_list:
                config_url = url.replace('{sku}', config.get('sku'))
                childs = self.env['magento.connector'].magento_api_call(
                    headers={},
                    url=config_url,
                    type=type
                )
                config['childs'] = childs
            # we have gathered configurable products with their childs
            # and the other simple products from magento
            # next: first we will create all the configurable products with their variants
            # start creating configurable products

            # need to fetch the complete required fields list
            # and their values
            if config_prod_list:
                existing_ids = self._import_products_list(
                    config_prod_list,
                    ids,
                    tmpl_vals,
                    attributes
                )
            # end  creating configurable products


        except Exception as e:
            logger.info("Exception occured %s", e)
            raise exceptions.UserError(_("Error Occured %s") % e)

        logger.info("%d products are successfully updated.")
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def fetch_products_from_odoo(self):
        url = '/rest/V1/products'
        type = 'POST'
        headers = {
            'Content-Type': 'application/json'
        }
        product_data = self.get_product_data()

        if not product_data:
            return
        updated_list = {}
        for product in product_data[0]:
            try:
                product_list = self.env[
                    'magento.connector'].magento_api_call(
                    headers=headers,
                    url=url,
                    type=type,
                    data=product
                )
                if product_list.get('sku'):
                    updated_list[product_list['sku']] = product_list.get(
                        'id')
            except:
                pass
        if updated_list:
            for product in product_data[1]:
                if product.default_code in updated_list:
                    product.write({
                        'magento': True,
                        'magento_id': str(
                            updated_list[product.default_code])
                    })
                    product.product_tmpl_id.write({
                        'magento': True,
                        'magento_id': str(
                            updated_list[product.default_code])
                    })
        logger.info("%s product(s) updated", len(updated_list))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
    def image_processing(self ,file):
        if file:
            image = False
            magento_host = self.env['ir.config_parameter'].sudo().get_param('odoo11_magento2.magento_host')
            image_url = 'http://' + magento_host + '/pub/media/catalog/product' + file
            if requests.get(image_url).status_code == 200:
                image = base64.b64encode(
                    requests.get(image_url).content)
            return image
        else:
            return False
