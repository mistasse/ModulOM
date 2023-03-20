import textwrap
import inspect
from types import FunctionType
from functools import partial
import collections


def flatten_code(lines):
    ret = []
    for line in lines:
        if isinstance(line, str):
            ret.append(line)
        elif isinstance(line, list):
            ret.append(textwrap.indent(flatten_code(line), '  '))
    return "\n".join(ret)


NoneType = type(None)
EmptyType = type(inspect._empty)
class RegParameter(inspect.Parameter):
    def __init__(self, name, kind, *, default, annotation, register=None):
        super().__init__(name, kind, default=default, annotation=annotation)
        if register is not None and self.default is not inspect._empty and not isinstance(self.default, (NoneType, bool, int, float, str)):
            self.identifier = register(self.name, self.default)
        
    def __str__(self):
        if hasattr(self, 'identifier'):
            return f"{self.name}={self.identifier}"
        return super().__str__()

    
IN_CACHE = 1
CONDITION_SATISFIED = 2


def cache_method(name, f, env=None, debug=False):
    signature = inspect.signature(f)
    cache_if = signature.parameters.get('_cache_if', None)
    cache_condition = cache_if.default if cache_if is not None and cache_if.default is not inspect._empty else True
    def register(function, name, value):
        if env is not None:
            identifier = f"{function}_{name}"
            assert identifier not in env
            env[identifier] = value
            return identifier
    signature = inspect.Signature([
        RegParameter(p.name, p.kind, default=p.default, annotation=p.annotation,
                     register=partial(register, name))
        for p in signature.parameters.values() if p.name != '_cache_if'
    ])
    params = list(signature.parameters.values())[1:]
    decl = str(signature)
    pos = ', '.join(param.name for param in params)
    call = ', '.join(f"{p.name}={p.name}" if p.kind == p.KEYWORD_ONLY else p.name for p in params)
    
    ret = [f'def {name}{decl}:', []]
    body = ret[-1]
    if debug:
        code = f'''
        key = ({name!r}, {pos})
        condition = bool({cache_condition})
        cached = self.__cache__.get(key, _NOVALUE)
        flags = {IN_CACHE}*(cached is not _NOVALUE) + {CONDITION_SATISFIED}*condition
        self._on_cache('get', key, flags)
        if cached is _NOVALUE:
            try:
                self._on_cache('enter', key, flags)
                cached = super().{name}({call})
                if condition:
                    self.__cache__[key] = cached
            finally:
                self._on_cache('exit', key, flags)
        return cached
        '''
    elif cache_condition is True or cache_condition == 'True':
        code = f'''
        key = ({name!r}, {pos})
        cached = self.__cache__.get(key, _NOVALUE)
        if cached is _NOVALUE:
            self.__cache__[key] = cached = super().{name}({call})
        return cached
        '''
    elif cache_condition is False or cache_condition == 'False':
        code = f'''
        return super().{name}({call})
        '''
        return None  # Can actually just skip the creation of the function
    else:  # not debug and cache condition is not trivial
        code = f'''
        if not ({cache_condition}): return super().{name}({call})
        key = ({name!r}, {pos})
        cached = self.__cache__.get(key, _NOVALUE)
        if cached is _NOVALUE:
            self.__cache__[key] = cached = super().{name}({call})
        return cached
        '''
        
    body.append(textwrap.dedent(code)[1:])
    return ret, env


_NOVALUE = object()

class WithCache:
    def __new__(cls, *args, **kwargs):
        extension = cls.__dict__.get("__caching__", None)
        if extension is None:
            dct = {}
            for name in dir(cls):
                if name.startswith('_'):
                    continue
                f = _NOVALUE
                for c in cls.mro():
                    if c is WithCache: break  # don't add cache to methods behind WithCache
                    f = c.__dict__.get(name, _NOVALUE)
                    if f is not _NOVALUE: break
                if f is _NOVALUE or not isinstance(f, FunctionType):
                    continue
                dct[name] = f
            
            basename = cls.__name__
            clsname = basename+'WithCache'
            code = [f"class {clsname}({basename}):", '', []]
            env = {}
            for name, f in dct.items():
                cached_code = cache_method(name, f, env=env, debug=hasattr(cls, '_on_cache'))
                if cached_code is None:
                    continue
                code[-1].extend(cached_code)
            env = {**env, basename: cls, '_NOVALUE':_NOVALUE}
            code = flatten_code(code)
            exec(code, env)
            extension = env[clsname]
            cls.__caching__ = extension
        ret = super().__new__(extension) # *args, **kwargs
        ret.__cache__ = {}
        return ret

    @property
    def _cache(self):
        """Disentangles the cache per function. This makes cache visualization easier,
        not meant to be used in the code
        """
        ret = collections.defaultdict(dict)
        for k, v in self.__cache__.items():
            name = k[0]
            ret[name][k[1:]] = v
        return dict(ret)

class Graph:
    def __init__(self):
        self.__current = ['']
        self._calls = []
        
    def _on_cache(self, event, key, flags):
        if event == 'get':
            self._calls.append((self.__current[-1], key))
            print(flags)
        elif event == 'enter':
            self.__current.append(key)
        elif event == 'exit':
            self.__current.pop()
        else:
            raise NotImplementedError(event)
