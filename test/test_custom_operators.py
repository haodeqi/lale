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

from lale.operators import make_operator
import numpy as np

class IncreaseRowsImpl():
    def __init__(self, n_rows = 5):
        self.n_rows = n_rows

    def fit(self, X, y = None):
        result = IncreaseRowsImpl(self.n_rows)
        return result

    def transform(self, X, y = None):
        X_subset = X[0:self.n_rows-1]
        X = np.concatenate((X, X_subset), axis = 0)
        y_subset = y[0:self.n_rows-1]
        y = np.concatenate((y, y_subset), axis = 0)
        return X, y

_input_schema_fit = {
  '$schema': 'http://json-schema.org/draft-04/schema#',
  'type': 'object',
  'required': ['X', 'y'],
  'additionalProperties': False,
  'properties': {
    'X': {
      'description': 'Features; the outer array is over samples.',
      'type': 'array',
      'items': {'type': 'array', 'items': {'type': 'number'}}},
    'y': {
      'description': 'Target class labels; the array is over samples.',
      'type': 'array',
      'items': {'type': 'number'}}}}

_input_schema_predict = {
  '$schema': 'http://json-schema.org/draft-04/schema#',
  'type': 'object',
  'required': ['X' ,'y'],
  'additionalProperties': False,
  'properties': {
    'X': {
      'description': 'Features; the outer array is over samples.',
      'type': 'array',
      'items': {'type': 'array', 'items': {'type': 'number'}}},
    'y': {}}}

_output_schema = {
  '$schema': 'http://json-schema.org/draft-04/schema#'}
#,
#  'type': 'array',
#  'items': {'type': 'number'}

_hyperparam_schema = {
  '$schema': 'http://json-schema.org/draft-04/schema#',
  'allOf': [
    { 'description':
        'This first sub-object lists all constructor arguments with their '
        'types, one at a time, omitting cross-argument constraints.',
      'type': 'object',
      'additionalProperties': False,
      'relevantToOptimizer': [],
      'properties': {}
    }]}

_combined_schemas = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Combined schema for expected data and hyperparameters.',
    'type': 'object',
    'tags': {
        'pre': [],
        'op': ['estimator'],
        'post': []},
    'properties': {
        'hyperparams': _hyperparam_schema,
        'input_fit': _input_schema_fit,
        'input_predict': _input_schema_predict,
        'output': _output_schema}}

IncreaseRows = make_operator(IncreaseRowsImpl, _combined_schemas)

import sklearn.linear_model

class MyLRImpl:
    def __init__(self, penalty='l2', solver='liblinear', C=1.0):
        self.penalty = penalty
        self.solver = solver
        self.C = C
        
    def fit(self, X, y):
        result = MyLRImpl(self.penalty, self.solver, self.C)
        result._sklearn_model = sklearn.linear_model.LogisticRegression(
            penalty = self.penalty, solver=self.solver, C = self.C)
        result._sklearn_model.fit(X, y)
        return result

    def predict(self, X):
        return self._sklearn_model.predict(X)

_input_schema_fit = {
  'type': 'object',
  'required': ['X', 'y'],
  'additionalProperties': False,
  'properties': {
    'X': {
      'type': 'array',
      'items': {'type': 'array', 'items': {'type': 'number'}}},
    'y': {
      'type': 'array',
      'items': {'type': 'number', 'minimum': 0}}}}

_input_schema_predict = {
  'type': 'object',
  'required': ['X'],
  'additionalProperties': False,
  'properties': {
    'X': {
      'type': 'array',
      'items': {'type': 'array', 'items': {'type': 'number'}}}}}

_output_schema = {
  'type': 'array',
  'items': {'type': 'number', 'minimum': 0}}

_hyperparams_ranges = {
  'type': 'object',
  'additionalProperties': False,
  'required': ['solver', 'penalty', 'C'],
  'relevantToOptimizer': ['solver', 'penalty', 'C'],
  'properties': {
    'solver': {
      'description': 'Algorithm for optimization problem.',
      'enum': ['newton-cg', 'lbfgs', 'liblinear', 'sag', 'saga'],
      'default': 'liblinear'},
    'penalty': {
      'description': 'Norm used in the penalization.',
      'enum': ['l1', 'l2'],
      'default': 'l2'},
    'C': {
      'description':
        'Inverse regularization strength. Smaller values specify '
        'stronger regularization.',
      'type': 'number',
      'distribution': 'loguniform',
      'minimum': 0.0,
      'exclusiveMinimum': True,
      'default': 1.0,
      'minimumForOptimizer': 0.03125,
      'maximumForOptimizer': 32768}}}

_hyperparams_constraints = {
  'allOf': [
    { 'description':
        'The newton-cg, sag, and lbfgs solvers support only l2 penalties.',
      'anyOf': [
        { 'type': 'object',
          'properties': {
            'solver': {'not': {'enum': ['newton-cg', 'sag', 'lbfgs']}}}},
        { 'type': 'object',
          'properties': {'penalty': {'enum': ['l2']}}}]}]}

_hyperparams_schema = {
  'allOf': [_hyperparams_ranges, _hyperparams_constraints]}

_combined_schemas = {
  '$schema': 'http://json-schema.org/draft-04/schema#',
  'type': 'object',
  'properties': {
    'input_fit': _input_schema_fit,
    'input_predict': _input_schema_predict,
    'output': _output_schema,
    'hyperparams': _hyperparams_schema } }

import lale.helpers
lale.helpers.validate_is_schema(_combined_schemas)

MyLR = lale.operators.make_operator(MyLRImpl, _combined_schemas)

