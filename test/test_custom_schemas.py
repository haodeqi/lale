# Copyright 2019 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import lale
import sklearn
import lale.helpers as helpers
import lale.schemas as schemas
from sklearn.decomposition import PCA as foo
from xgboost import XGBClassifier as bar
from lightgbm import LGBMClassifier as baz


class TestCustomSchema(unittest.TestCase):
    def setUp(self):
        import sklearn.decomposition
        import lale.lib.sklearn
        from lale.operators import make_operator
        self.sk_pca = make_operator(sklearn.decomposition.PCA, schemas={})
        self.ll_pca = lale.lib.sklearn.PCA

    def test_override_schemas(self):
        init_schemas = self.sk_pca._schemas
        pca_schemas = self.ll_pca._schemas
        foo = self.sk_pca.customize_schema(schemas=schemas.JSON(pca_schemas))
        self.assertEqual(foo._schemas, pca_schemas)
        self.assertEqual(self.sk_pca._schemas, init_schemas)
        self.assertRaises(Exception, self.sk_pca.customize_schema, schemas={})

    def test_override_input(self):
        init_input_schema = self.sk_pca.get_schema('input_fit')
        pca_input = self.ll_pca.get_schema('input_fit')
        foo = self.sk_pca.customize_schema(input_fit=schemas.JSON(pca_input))
        self.assertEqual(foo.get_schema('input_fit'), pca_input)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.sk_pca.get_schema(
            'input_fit'), init_input_schema)
        self.assertRaises(
            Exception, self.sk_pca.customize_schema, input_fit={})
        self.assertRaises(
            Exception, self.sk_pca.customize_schema, input_foo=pca_input)

    def test_override_output(self):
        init_output_schema = self.sk_pca.get_schema('output')
        pca_output = self.ll_pca.get_schema('output')
        foo = self.sk_pca.customize_schema(output=schemas.JSON(pca_output))
        self.assertEqual(foo.get_schema('output'), pca_output)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.sk_pca.get_schema('output'), init_output_schema)
        self.assertRaises(Exception, self.sk_pca.customize_schema, output={})
        self.assertRaises(
            Exception, self.sk_pca.customize_schema, output_foo=pca_output)

    def test_override_output2(self):
        init_output_schema = self.sk_pca.get_schema('output')
        pca_output = schemas.AnyOf([
            schemas.Array(
                schemas.Array(
                    schemas.Float())),
            schemas.Array(
                schemas.Float())])
        expected = {'$schema': 'http://json-schema.org/draft-04/schema#',
                    'anyOf': [
                        {'type': 'array',
                         'items': {
                             'type': 'array',
                             'items': {'type': 'number'}}},
                        {'type': 'array',
                         'items': {
                             'type': 'number'}}]}
        foo = self.sk_pca.customize_schema(output=pca_output)
        self.assertEqual(foo.get_schema('output'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.sk_pca.get_schema('output'), init_output_schema)

    def test_override_bool_param_sk(self):
        init = self.sk_pca.hyperparam_schema('whiten')
        expected = {'default': True,
                    'type': 'boolean',
                    'description': 'override'}
        foo = self.sk_pca.customize_schema(
            whiten=schemas.Bool(default=True, desc='override'))
        self.assertEqual(foo.hyperparam_schema('whiten'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.sk_pca.hyperparam_schema('whiten'), init)
        self.assertRaises(Exception, self.sk_pca.customize_schema, whitenX={})

    def test_override_bool_param_ll(self):
        init = self.ll_pca.hyperparam_schema('whiten')
        expected = {'default': True, 'type': 'boolean'}
        foo = self.ll_pca.customize_schema(whiten=schemas.Bool(default=True))
        self.assertEqual(foo.hyperparam_schema('whiten'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema('whiten'), init)
        self.assertRaises(Exception, self.ll_pca.customize_schema, whitenX={})

    def test_override_enum_param(self):
        init = self.ll_pca.hyperparam_schema('svd_solver')
        expected = {'default': 'full', 'enum': ['auto', 'full']}
        foo = self.ll_pca.customize_schema(
            svd_solver=schemas.Enum(default='full', values=['auto', 'full']))
        self.assertEqual(foo.hyperparam_schema('svd_solver'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema('svd_solver'), init)

    def test_override_float_param(self):
        init = self.ll_pca.hyperparam_schema('tol')
        expected = {'default': 0.1,
                    'type': 'number',
                    'minimum': -10,
                    'maximum': 10,
                    'exclusiveMaximum': True,
                    'exclusiveMinimum': False}
        foo = self.ll_pca.customize_schema(
            tol=schemas.Float(default=0.1,
                              min=-10,
                              max=10,
                              exclusiveMax=True,
                              exclusiveMin=False))
        self.assertEqual(foo.hyperparam_schema('tol'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema('tol'), init)

    def test_override_int_param(self):
        init = self.ll_pca.hyperparam_schema('iterated_power')
        expected = {'default': 1,
                    'type': 'integer',
                    'minimum': -10,
                    'maximum': 10,
                    'exclusiveMaximum': True,
                    'exclusiveMinimum': False}
        foo = self.ll_pca.customize_schema(
            iterated_power=schemas.Int(default=1,
                                       min=-10,
                                       max=10,
                                       exclusiveMax=True,
                                       exclusiveMin=False))
        self.assertEqual(foo.hyperparam_schema('iterated_power'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema('iterated_power'), init)

    def test_override_null_param(self):
        init = self.ll_pca.hyperparam_schema('n_components')
        expected = {'enum': [None]}
        foo = self.ll_pca.customize_schema(n_components=schemas.Null())
        self.assertEqual(foo.hyperparam_schema('n_components'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema('n_components'), init)

    def test_override_json_param(self):
        init = self.ll_pca.hyperparam_schema('tol')
        expected = {'description': 'Tol',
                    'type': 'number',
                    'minimum': 0.2,
                    'default': 1.0}
        foo = self.ll_pca.customize_schema(tol=schemas.JSON(expected))
        self.assertEqual(foo.hyperparam_schema('tol'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema('tol'), init)

    def test_override_any_param(self):
        init = self.ll_pca.hyperparam_schema('iterated_power')
        expected = {'anyOf': [
            {'type': 'integer'},
            {'enum': ['auto', 'full']}],
            'default': 'auto'}
        foo = self.ll_pca.customize_schema(
            iterated_power=schemas.AnyOf([schemas.Int(),
                                          schemas.Enum(['auto', 'full'])], default='auto'))
        self.assertEqual(foo.hyperparam_schema('iterated_power'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema('iterated_power'), init)

    def test_override_array_param(self):
        init = self.sk_pca.hyperparam_schema('copy')
        expected = {'type': 'array',
                    'minItemsForOptimizer': 1,
                    'maxItemsForOptimizer': 20,
                    'items': {'type': 'integer'}}
        foo = self.sk_pca.customize_schema(
            copy=schemas.Array(minItems=1, maxItems=20, items=schemas.Int()))
        self.assertEqual(foo.hyperparam_schema('copy'), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.sk_pca.hyperparam_schema('copy'), init)

    def test_override_object_param(self):
        init = self.sk_pca.get_schema('input_fit')
        expected = {'$schema': 'http://json-schema.org/draft-04/schema#',
                    'type': 'object',
                    'required': ['X'],
                    'additionalProperties': False,
                    'properties': {
                        'X': {'type': 'array',
                              'items': {
                                  'type': 'number'}}}}
        foo = self.sk_pca.customize_schema(
            input_fit=schemas.Object(required=['X'],
                                     additionalProperties=False,
                                     properties={'X': schemas.Array(schemas.Float())}))
        self.assertEqual(foo.get_schema('input_fit'), expected)
        helpers.validate_is_schema(foo.get_schema('input_fit'))
        self.assertEqual(self.sk_pca.get_schema('input_fit'), init)
        
    def test_add_constraint(self):
        init = self.sk_pca.hyperparam_schema()
        expected = {'allOf': [
            {'type': 'object', 'properties': {}},
            {'anyOf': [
                {'type': 'object',
                 'properties': {
                     'n_components': {
                         'not': {
                             'enum': ['mle']},
                     }},
                 },
                {'type': 'object',
                 'properties': {
                     'svd_solver': {
                         'enum': ['full', 'auto']},
                 }}]}]}
        foo = self.sk_pca.customize_schema(
            constraint=schemas.AnyOf([
                schemas.Object({
                    'n_components': schemas.Not(schemas.Enum(['mle']))
                }),
                schemas.Object({
                    'svd_solver': schemas.Enum(['full', 'auto'])
                })
            ]))
        self.assertEqual(foo.hyperparam_schema(), expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.sk_pca.hyperparam_schema(), init)
        
    def test_override_relevant(self):
        init = self.ll_pca.hyperparam_schema()['allOf'][0]['relevantToOptimizer']
        expected = ['svd_solver']
        foo = self.ll_pca.customize_schema(relevantToOptimizer=['svd_solver'])
        self.assertEqual(foo.hyperparam_schema()['allOf'][0]['relevantToOptimizer'], expected)
        helpers.validate_is_schema(foo._schemas)
        self.assertEqual(self.ll_pca.hyperparam_schema()['allOf'][0]['relevantToOptimizer'], init)
        self.assertRaises(Exception, self.sk_pca.customize_schema, relevantToOptimizer={})
        
    def test_load_schema(self):
        from lale.operators import make_operator
        new_pca = make_operator(sklearn.decomposition.PCA)
        self.assertEqual(self.ll_pca._schemas, new_pca._schemas)
        self.assertNotEqual(self.ll_pca._schemas, self.sk_pca._schemas)
        
    def test_wrap_imported_operators(self):
        from lale.lib.sklearn import PCA
        from lale.lib.xgboost import XGBClassifier
        from lale.lib.lightgbm import LGBMClassifier
        lale.wrap_imported_operators()
        self.assertEqual(foo._schemas, PCA._schemas)
        self.assertEqual(bar._schemas, XGBClassifier._schemas)
        self.assertEqual(baz._schemas, LGBMClassifier._schemas)
        
        
        
