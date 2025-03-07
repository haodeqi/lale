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

import ast
import contextlib
import json
import jsonschema
import jsonsubschema
import numpy as np
import pandas as pd
import os
import re
import sys
import time
import traceback
import urllib
import warnings
import yaml
import scipy.sparse
import importlib
import graphviz
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, log_loss
from sklearn.utils.metaestimators import _safe_split
import copy
import logging
import importlib
import inspect
import pkgutil
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class assert_raises:
    def __init__(self, expected_exc_type):
        self.__expected_exc_type = expected_exc_type

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        assert exc_type is self.__expected_exc_type
        print_yaml('error', str(exc_value), file=sys.stderr)
        return True

class assert_warns:
    def __init__(self, expected_exc_type):
        self.__expected_exc_type = expected_exc_type

    def __enter__(self):
        warnings.filterwarnings("error", category=self.__expected_exc_type)

    def __exit__(self, exc_type, exc_value, traceback):
        warnings.resetwarnings()
        assert exc_type is self.__expected_exc_type
        print_yaml('error', str(exc_value), file=sys.stderr)
        return True

def assignee_name(level=1):
    tb = traceback.extract_stack()
    file_name, line_number, function_name, text = tb[-(level+2)]
    tree = ast.parse(text, file_name)
    assert isinstance(tree, ast.Module)
    if len(tree.body) == 1 and isinstance(tree.body[0], ast.Assign):
        lhs = tree.body[0].targets
        if len(lhs) == 1 and isinstance(lhs[0], ast.Name):
            return lhs[0].id
    return None

def data_to_json(data, subsample_array = True):
    if type(data) is tuple:
        # convert to list
        return [data_to_json(elem, subsample_array) for elem in data]
    if type(data) is list:
        return [data_to_json(elem, subsample_array) for elem in data]
    elif type(data) is dict:
        return {key: data_to_json(data[key], subsample_array) for key in data}
    elif isinstance(data, np.ndarray):
        return ndarray_to_json(data, subsample_array)
    elif type(data) is scipy.sparse.csr_matrix:
        return ndarray_to_json(data.toarray(), subsample_array)
    elif isinstance(data, pd.DataFrame) or isinstance(data, pd.Series):
        np_array = data.values
        return ndarray_to_json(np_array, subsample_array)
    else:
        return data

def dict_without(orig_dict, key):
    return {k: orig_dict[k] for k in orig_dict if k != key}

def load_yaml(dir_name, file_name, meta_dir=True):
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    if meta_dir:
        op_dir = os.path.join(parent_dir, 'meta_data', dir_name)
    else:
        op_dir = os.path.join(parent_dir, dir_name)
    schema_file = os.path.join(op_dir, file_name)
    with open(schema_file, 'r') as f:
        result = yaml.load(f)
    return result

def ndarray_to_json(arr, subsample_array=True):
    #sample 10 rows and no limit on columns
    if subsample_array:
        num_subsamples = [10, np.iinfo(np.int).max, np.iinfo(np.int).max]
    else:
        num_subsamples = [np.iinfo(np.int).max, np.iinfo(np.int).max, np.iinfo(np.int).max]
    def subarray_to_json(indices):
        if len(indices) == len(arr.shape):
            if isinstance(arr[indices], float) or isinstance(arr[indices], int)\
                or isinstance(arr[indices], str):
                return arr[indices]
            elif arr.dtype == np.float64 or arr.dtype == np.float32:
                return float(arr[indices])
            elif arr.dtype == np.int64:
                return int(arr[indices])
            elif arr.dtype.kind == 'U':
                return str(arr[indices])
            elif arr.dtype.kind == 'O':
                return str(arr[indices])
            else:
                raise ValueError(f'Unexpected dtype {arr.dtype}, '
                                 f'kind {arr.dtype.kind}, '
                                 f'type {type(arr[indices])}.')
        else:
            assert len(indices) < len(arr.shape)
            return [subarray_to_json(indices + (i,))
                    for i in range(min(num_subsamples[len(indices)], arr.shape[len(indices)]))]
    return subarray_to_json(())

def print_yaml(what, doc, file=sys.stdout):
    print(yaml.dump({what: doc}).strip(), file=file)

def validate_schema(value, schema, subsample_array=True):
    json_value = data_to_json(value, subsample_array)
    jsonschema.validate(json_value, schema)

JSON_META_SCHEMA_URL = 'http://json-schema.org/draft-04/schema#'
JSON_META_SCHEMA = None

def validate_is_schema(value):
    if '$schema' in value:
        assert value['$schema'] == JSON_META_SCHEMA_URL
    global JSON_META_SCHEMA
    if JSON_META_SCHEMA is None:
        url = JSON_META_SCHEMA_URL
        with contextlib.closing(urllib.request.urlopen(url)) as f:
            JSON_META_SCHEMA = json.load(f)
    jsonschema.validate(value, JSON_META_SCHEMA)

def is_schema(value):
    if isinstance(value, dict):
        try:
            jsonschema.validate(value, JSON_META_SCHEMA)
        except:
            return False
        return True
    return False

class SubschemaError(Exception):
    def __init__(self, sub, sup, sub_name='sub', sup_name='super'):
        self.sub = sub
        self.sup = sup
        self.sub_name = sub_name
        self.sup_name = sup_name

    def __str__(self):
        summary = f'expected {self.sub_name} <: {self.sup_name}'
        import pprint
        sub = pprint.pformat(self.sub, width=70, compact=True)
        sup = pprint.pformat(self.sup, width=70, compact=True)
        details = f'\n{self.sub_name} = \\\n{sub}\n{self.sup_name} = \\\n{sup}'
        return summary + details

def validate_subschema(sub, sup, sub_name='sub', sup_name='super'):
    if not jsonsubschema.isSubschema(sub, sup):
        raise SubschemaError(sub, sup, sub_name, sup_name)

def cross_val_score_track_trials(estimator, X, y=None, scoring=accuracy_score, cv=5):
    """
    Use the given estimator to perform fit and predict for splits defined by 'cv' and compute the given score on 
    each of the splits.

    :param estimator: A valid sklearn_wrapper estimator
    :param X, y: Valid data and target values that work with the estimator
    :param scoring: a scorer object from sklearn.metrics (https://scikit-learn.org/stable/modules/classes.html#module-sklearn.metrics)
             Default value is accuracy_score.
    :param cv: an integer or an object that has a split function as a generator yielding (train, test) splits as arrays of indices.
        Integer value is used as number of folds in sklearn.model_selection.StratifiedKFold, default is 5.
        Note that any of the iterators from https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators can be used here.

    :return: cv_results: a list of scores corresponding to each cross validation fold
    """
    if isinstance(cv, int):
        cv = StratifiedKFold(cv)
    
    cv_results = []
    log_loss_results = []
    time_results = []
    for train, test in cv.split(X, y):
        X_train, y_train = _safe_split(estimator, X, y, train)
        X_test, y_test = _safe_split(estimator, X, y, test, train)
        start = time.time()
        trained_estimator = estimator.fit(X_train, y_train)
        predicted_values = trained_estimator.predict(X_test)
        execution_time = time.time() - start
        # not all estimators have predict probability
        try:
            y_pred_proba = trained_estimator.predict_proba(X_test)
            logloss = log_loss(y_true=y_test, y_pred=y_pred_proba)
            log_loss_results.append(logloss)
        except BaseException:
            logger.debug("Warning, log loss cannot be computed")
        cv_results.append(scoring(y_test, predicted_values))
        time_results.append(execution_time)

    return np.array(cv_results).mean(), np.array(log_loss_results).mean(), np.array(execution_time).mean()


def cross_val_score(estimator, X, y=None, scoring=accuracy_score, cv=5):
    """
    Use the given estimator to perform fit and predict for splits defined by 'cv' and compute the given score on
    each of the splits.
    :param estimator: A valid sklearn_wrapper estimator
    :param X, y: Valid data and target values that work with the estimator
    :param scoring: a scorer object from sklearn.metrics (https://scikit-learn.org/stable/modules/classes.html#module-sklearn.metrics)
             Default value is accuracy_score.
    :param cv: an integer or an object that has a split function as a generator yielding (train, test) splits as arrays of indices.
        Integer value is used as number of folds in sklearn.model_selection.StratifiedKFold, default is 5.
        Note that any of the iterators from https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators can be used here.
    :return: cv_results: a list of scores corresponding to each cross validation fold
    """
    if isinstance(cv, int):
        cv = StratifiedKFold(cv)

    cv_results = []
    for train, test in cv.split(X, y):
        X_train, y_train = _safe_split(estimator, X, y, train)
        X_test, y_test = _safe_split(estimator, X, y, test, train)
        trained_estimator = estimator.fit(X_train, y_train)
        predicted_values = trained_estimator.predict(X_test)
        cv_results.append(scoring(y_test, predicted_values))

    return cv_results

def create_operator_using_reflection(class_name, operator_name, param_dict):
    instance = None
    if class_name is not None:
        class_name_parts = class_name.split(".")
        assert(len(class_name_parts)) >1, "The class name needs to be fully qualified, i.e. module name + class name"
        module_name = ".".join(class_name_parts[0:-1])
        class_name = class_name_parts[-1]

        module = importlib.import_module(module_name)

        class_ = getattr(module, class_name)
        
        if param_dict is None:
            instance = class_.create(name=operator_name)
        else:
            instance = class_.create(name=operator_name, kwargs = param_dict)
    return instance

def create_individual_op_using_reflection(class_name, operator_name, param_dict):
    instance = None
    if class_name is not None:
        class_name_parts = class_name.split(".")
        assert(len(class_name_parts)) >1, "The class name needs to be fully qualified, i.e. module name + class name"
        module_name = ".".join(class_name_parts[0:-1])
        class_name = class_name_parts[-1]

        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        
        if param_dict is None:
            instance = class_()
        else:
            instance = class_(**param_dict)
    return instance

def to_graphviz(lale_operator):
    from lale.operators import Operator, Pipeline
    from lale.pretty_print import hyperparams_to_string
    if not isinstance(lale_operator, Operator):
        raise ValueError("The input to to_graphviz needs to be a valid LALE operator.")
    jsn = lale_operator.to_json()
    dot = graphviz.Digraph()
    dot.attr('graph', rankdir='LR')
    if isinstance(lale_operator, Pipeline):
        nodes = jsn['steps']
    else:
        nodes = [jsn]
    #figure out what things were called in the caller
    cls2sym, name2cls = {}, {}
    import inspect
    symtab = inspect.stack()[1][0].f_globals
    for sym, val in symtab.items():
        if isinstance(val, Operator):
            cls = val.class_name()
            cls2sym[cls] = '?' if (cls in cls2sym) else sym
    cls2sym = {cls: cls2sym[cls] for cls in cls2sym if cls2sym[cls] != '?'}
    for node in nodes:
        name, cls = node['operator'], node['class']
        if '|' in name:
            for step in node['steps']:
                name2cls[step['operator']] = step['class']
        else:
            name2cls[name] = cls
    def name2sym(name):
        if '|' in name:
            step_syms = [name2sym(n.strip()) for n in name.split(sep='|')]
            return ' | '.join(step_syms)
        if name in name2cls:
            cls = name2cls[name]
            if cls in cls2sym:
                return cls2sym[cls]
        return name
    #do the actual visualizations
    try:
        edges = jsn['edges']
    except KeyError:
        edges = []
    def make_tooltip(node):
        sym = name2sym(node['operator'])
        if 'hyperparams' in node:
            hps = node['hyperparams']
            if hps:
                return f'{sym}({hyperparams_to_string(hps)})'
        return sym
    for i, node in enumerate(nodes):
        state2color = {
            'trained': 'white',
            'trainable': 'lightskyblue1',
            'planned': 'skyblue2'}
        attrs = {
            'style' :'filled',
            'fillcolor': state2color[node['state']],
            'tooltip': make_tooltip(node)}
        if 'documentation_url' in node:
            attrs = {**attrs, 'URL': node['documentation_url']}
        dot.node(str(i), name2sym(node['operator']), **attrs)
    for edge in edges:
        dot.edge(str(edge[0]), str(edge[1]))
    return dot

def println_pos(message, out_file=sys.stdout):
    tb = traceback.extract_stack()[-2]
    match = re.search(r'<ipython-input-([0-9]+)-', tb[0])
    if match:
        pos = 'notebook cell [{}] line {}'.format(match[1], tb[1])
    else:
        pos = '{}:{}'.format(tb[0], tb[1])
    strtime = time.strftime('%Y-%m-%d_%H-%M-%S')
    to_log = '{}: {} {}'.format(pos, strtime, message)
    print(to_log, file=out_file)
    if match:
        os.system('echo {}'.format(to_log))

def create_instance_from_hyperopt_search_space(lale_object, hyperparams):
    '''
    Hyperparams is a n-tuple of dictionaries of hyper-parameters, each
    dictionary corresponds to an operator in the pipeline
    '''
    #lale_object can either be an individual operator, a pipeline or an operatorchoice
    #Validate that the number of elements in the n-tuple is the same
    #as the number of steps in the current pipeline

    from lale.operators import IndividualOp
    from lale.operators import Pipeline
    from lale.operators import TrainablePipeline
    from lale.operators import OperatorChoice
    if isinstance(lale_object, IndividualOp):
        if hyperparams:
            hyperparams.pop('name', None)
        return lale_object(**hyperparams)
    elif isinstance(lale_object, Pipeline):
        if len(hyperparams) != len(lale_object.steps()):
            raise ValueError('The number of steps in the hyper-parameter space does not match the number of steps in the pipeline.')
        op_instances = []
        edges = lale_object.edges()
        #op_map:Dict[PlannedOpType, TrainableOperator] = {}
        op_map = {}
        for op_index in range(len(hyperparams)):
            state_params = hyperparams[op_index]
            #TODO: Should ideally check if the class_name is the same as the class name of the op from self.operators() at op_index
            op_instance = create_instance_from_hyperopt_search_space(lale_object.steps()[op_index], state_params)
            op_instances.append(op_instance)
            orig_op = lale_object._steps[op_index]
            op_map[orig_op] = op_instance

        #trainable_edges:List[Tuple[TrainableOperator, TrainableOperator]]
        try:
            trainable_edges = [(op_map[x], op_map[y]) for (x, y) in edges]
        except KeyError as e:
            raise ValueError("An edge was found with an endpoint that is not a step (" + str(e) + ")")

        return TrainablePipeline(op_instances, trainable_edges, ordered=True)
    elif isinstance(lale_object, OperatorChoice):
        #Hyperopt search space for an OperatorChoice is generated as a dictionary with a single element
        #corresponding to the choice made, the only key is the index of the step and the value is 
        #the params corresponding to that step.
        step_index, hyperparams = hyperparams.popitem()
        step_object = lale_object.steps()[step_index]
        return create_instance_from_hyperopt_search_space(step_object, hyperparams)
        
def import_from_sklearn_pipeline(sklearn_pipeline):
    #For all pipeline steps, identify equivalent lale wrappers if present,
    #if not, call make operator on sklearn classes and create a lale pipeline.

    def get_equivalent_lale_op(sklearn_obj):
        module_name = "lale.lib.sklearn"
        from sklearn.base import clone
        from lale.operators import make_operator

        class_name = sklearn_obj.__class__.__name__
        module = importlib.import_module(module_name)
        try:
            class_ = getattr(module, class_name)
        except AttributeError:
            class_ = make_operator(sklearn_obj, name=class_name)
        class_ = class_(**sklearn_obj.get_params())
        class_._impl._sklearn_model =  copy.deepcopy(sklearn_obj)
        return class_         

    from sklearn.pipeline import FeatureUnion, Pipeline
    from sklearn.base import BaseEstimator
    from lale.operators import make_pipeline, make_union
    
    if isinstance(sklearn_pipeline, Pipeline):
        nested_pipeline_steps = sklearn_pipeline.named_steps.values()
        nested_pipeline_lale_objects = [import_from_sklearn_pipeline(nested_pipeline_step) for nested_pipeline_step in nested_pipeline_steps]
        lale_op_obj = make_pipeline(*nested_pipeline_lale_objects)
    elif isinstance(sklearn_pipeline, FeatureUnion):
        transformer_list = sklearn_pipeline.transformer_list
        concat_predecessors = [import_from_sklearn_pipeline(transformer[1]) for transformer in transformer_list]
        lale_op_obj = make_union(*concat_predecessors)
    else:
        lale_op_obj = get_equivalent_lale_op(sklearn_pipeline)
    return lale_op_obj
        
def get_hyperparam_names(op):
    import inspect
    if op._impl.__module__.startswith('lale'):
        hp_schema = op.hyperparam_schema()
        params = next(iter(hp_schema.get('allOf', []))).get('properties', {})
        return list(params.keys())
    else:
        return inspect.getargspec(op._impl.__class__.__init__).args
                
def validate_method(op, m):
    if op._impl.__module__.startswith('lale'):
        assert (m in op._schemas['properties'].keys())
    else:
        a = ''
        if m.startswith('input_'):
            a = m[len('input_'):]
        elif m.startswith('output_'):
            a = m[len('output_'):]
        if a:
            assert (hasattr(op._impl, a))

def caml_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def get_lib_schema(impl):
    try:
        module_name = impl.__module__.split('.')[0]
        class_name = caml_to_snake(impl.__class__.__name__)
        lib_name = '.'.join(['lale.lib', module_name, class_name])
        m = importlib.import_module(lib_name)
        return m._combined_schemas
    except (ModuleNotFoundError, AttributeError):
        return None
    
logger = logging.getLogger(__name__)

def wrap_imported_operators():
    import lale.lib
    from .operators import  make_operator
    calling_frame = inspect.stack()[1][0]
    g = calling_frame.f_globals
    for name in (n for n in g if inspect.isclass(g[n])):
        m = g[name].__module__.split('.')[0]
        if m in [p.name for p in pkgutil.iter_modules(lale.lib.__path__)]:
            logger.info(f'Lale:Wrapped operator:{name}')
            g[name] = make_operator(impl=g[name], name=name)

class val_wrapper():
    """This is used to wrap values that cause problems for hyper-optimizer backends
    lale will unwrap these when given them as the value of a hyper-parameter"""

    def __init__(self, base):
        self._base = base

    def unwrap_self(self):
        return self._base

    @classmethod
    def unwrap(cls, obj):
        if isinstance(obj, cls):
            return cls.unwrap(obj.unwrap_self())
        else:
            return obj
