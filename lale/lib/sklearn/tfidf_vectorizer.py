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

import lale.helpers
import lale.operators
import numpy as np
import pandas as pd
import sklearn.feature_extraction.text

class TfidfVectorizerImpl():
    def __init__(self, **hyperparams):
        if 'dtype' in hyperparams and hyperparams['dtype'] == 'float64':
            hyperparams = {**hyperparams, 'dtype': np.float64}
        self._hyperparams = hyperparams

    def fit(self, X, y=None):
        self._sklearn_model = sklearn.feature_extraction.text.TfidfVectorizer(**self._hyperparams)
        if isinstance(X, np.ndarray) or isinstance(X, pd.DataFrame):
            X = X.squeeze()
        self._sklearn_model.fit(X, y)
        return self

    def transform(self, X):
        if isinstance(X, np.ndarray) or isinstance(X, pd.DataFrame):
            X = X.squeeze()
        return self._sklearn_model.transform(X)

_hyperparams_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Convert a collection of raw documents to a matrix of TF-IDF features.',
    'allOf': [
    {   'type': 'object',
        'required': ['input', 'encoding', 'decode_error', 'strip_accents', 'lowercase', 'preprocessor', 'tokenizer', 'analyzer', 'stop_words', 'ngram_range', 'max_df', 'min_df', 'max_features', 'vocabulary', 'binary', 'dtype', 'norm', 'use_idf', 'smooth_idf', 'sublinear_tf'],
        'relevantToOptimizer': ['analyzer',  'ngram_range', 'max_df', 'min_df', 'binary', 'norm', 'use_idf', 'smooth_idf', 'sublinear_tf'],
        'additionalProperties': False,
        'properties': {
            'input': {
                'enum': ['filename', 'file', 'content'],
                'default': 'content'},
            'encoding': {
                'type': 'string',
                'default': 'utf-8'},
            'decode_error': {
                'enum': ['strict', 'ignore', 'replace'],
                'default': 'strict'},
            'strip_accents': {
                'enum': ['ascii', 'unicode', None],
                'default': None},
            'lowercase': {
                'type': 'boolean',
                'default': True},
            'preprocessor': {
                'anyOf': [
                {},
                {   'enum': [None]}],
                'default': None},
            'tokenizer': {
                'anyOf': [
                {},
                {   'enum': [None]}],
                'default': None},
            'analyzer': {
                'enum': ['word', 'char', 'char_wb'], #Need to support callable
                'default': 'word'},
            'stop_words': {
                'anyOf': [{
                    'enum': [None]}, {
                    'type': 'array'}, {
                    'type': 'string'}],
                'default': None},
            'token_pattern': {
                'type': 'string',
                'default': '(?u)\\b\\w\\w+\\b'},
            'ngram_range': {
                'default': [1, 1],
                'anyOf': [{
                    'type': 'array',
                    'typeForOptimizer': 'tuple',
                    'minItemsForOptimizer': 2,
                    'maxItemsForOptimizer': 2,
                    'items': {
                        'type': 'integer',
                        'minimumForOptimizer': 1,
                        'maximumForOptimizer': 3},
                    'forOptimizer':False
                    },
                    {
                        'enum': [(1,1), (1,2), (1,3), (2,2), (2,3), (3,3)]
                    }
                ]},
            'max_df': {
                'anyOf': [{
                    'description': 'float in range [0.0, 1.0]',
                    'type': 'number',
                    'minimum': 0.0,
                    'maximum': 1.0,
                    'minimumForOptimizer': 0.8,
                    'maximumForOptimizer': 0.9,
                    'distribution': 'uniform'}, {
                    'type': 'integer', 'forOptimizer': False}],
                'default': 1.0},
            'min_df': {
                'anyOf': [{
                    'description': 'float in range [0.0, 1.0]',
                    'type': 'number',
                    'minimum': 0.0,
                    'maximum': 1.0,
                    'minimumForOptimizer': 0.0,
                    'maximumForOptimizer': 0.1,
                    'distribution': 'uniform'}, {
                    'type': 'integer', 'forOptimizer': False}],
                'default': 1},
            'max_features': {
                'anyOf': [{
                    'anyOf': [{
                        'type': 'number'}, {
                        'enum': [None]}]}],
                'default': None},
            'vocabulary': {
                'description': 'XXX TODO XXX, Mapping or iterable, optional',
                'anyOf': [{
                    'type': 'object'}, {
                    'enum': [None]}],
                'default': None},
            'binary': {
                'type': 'boolean',
                'default': False},
            'dtype': {
                'description': 'XXX TODO XXX, type, optional',
                'type': 'string',
                'default': 'float64'},
            'norm': {
                'enum': ['l1', 'l2', None],
                'default': 'l2'},
            'use_idf': {
                'type': 'boolean',
                'default': True},
            'smooth_idf': {
                'type': 'boolean',
                'default': True},
            'sublinear_tf': {
                'type': 'boolean',
                'default': False}}},
    {   'description': "tokenizer, only applies if analyzer == 'word'",
        'anyOf': [
        {   'type': 'object',
            'properties': {
                'analyzer': {
                    'enum': ['word']}}},
        {   'type': 'object',
            'properties': {
                'tokenizer': {
                    'enum': [None]}}}]},
    {   'description': "stop_words can be a list only if analyzer == 'word'",
        'anyOf': [
        {   'type': 'object',
            'properties': {
                'stop_words': {
                    'not': {
                        'type': 'array'}}}},
        {   'type': 'object',
            'properties': {
                'analyzer': {
                    'enum': ['word']}}}]}]}

_input_fit_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Input data schema for training the TfidfVectorizer from scikit-learn.',
    'type': 'object',
    'required': ['X'],
    'additionalProperties': False,
    'properties': {
        'X': {
            'description': 'Features; the outer array is over samples.',
            'anyOf': [
                {   'type': 'array',
                    'items': {'type': 'string'}},
                {   'type': 'array',
                    'items': {
                        'type': 'array', 'minItems': 1, 'maxItems': 1,
                        'items': {'type': 'string'}}}]},
        'y': {
            'description': 'Target class labels; the array is over samples.'}}}

_input_predict_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Input data schema for predictions using the TfidfVectorizer model from scikit-learn.',
    'type': 'object',
    'required': ['X'],
    'additionalProperties': False,
    'properties': {
        'X': {
            'description': 'Features; the outer array is over samples.',
            'anyOf': [
                {   'type': 'array',
                    'items': {'type': 'string'}},
                {   'type': 'array',
                    'items': {
                        'type': 'array', 'minItems': 1, 'maxItems': 1,
                        'items': {'type': 'string'}}}]}}}

_output_schema = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Output data schema for predictions (projected data) using the TfidfVectorizer model from scikit-learn.',
    'type': 'array',
    'items': {
        'type': 'array',
        'items': {
            'type': 'number'}}}

_combined_schemas = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'description': 'Combined schema for expected data and hyperparameters.',
    'documentation_url': 'https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html',
    'type': 'object',
    'tags': {
        'pre': ['text'],
        'op': ['transformer'],
        'post': []},
    'properties': {
        'hyperparams': _hyperparams_schema,
        'input_fit': _input_fit_schema,
        'input_predict': _input_predict_schema,
        'output': _output_schema }}

if (__name__ == '__main__'):
    lale.helpers.validate_is_schema(_combined_schemas)

TfidfVectorizer = lale.operators.make_operator(TfidfVectorizerImpl, _combined_schemas)
