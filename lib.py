#
# variable creation:
#  count uses of expressions,
#  when used more than once, create a variable for them
#

# for strconcat implement __radd__ which handles str + custom_type


# todos:
# -> put variable name on _jsexpr, not as a dict value that's kinda weird
# -> probably rename the _exprstack to _stmtstack or something, since we also want to deal with ifs and stuff
# -> research:  decorator that modifies the scope of the function called or something like that, so we don't have to use global variables?

# ! note that this system does not deal with operator precendence in any way other than how python handles it by default
# ! if in any case python's operator precendence would produce a result different from what it would in javascript, we kinda have a problem
# (i doubt this is the case but it might be in some weird cases with special operators idk)


from string import ascii_letters
import json
import inspect
from isvalidjsid import isvalidjsid

_exprstack = {}
_scopestack = []
_lastexitedscope = None


def _newvar(lastvar):
    if lastvar == '':
        return 'a'
    else:
        v = lastvar
        l = len(v)
        for i in range(l):
            c = v[l-i-1]
            if c != 'Z':
                # string are immutable :(
                return v[:l-i-1] + ascii_letters[ascii_letters.index(c)+1] + v[l-i+1:]

        return 'a' + v


def _getexprstack():
    global _exprstack, _scopestack
    return _scopestack[-1].subexprstack if len(_scopestack) > 1 else _exprstack


def _tojs(any, exprstack=_getexprstack()):
    if isinstance(any, _jsexpr):
        return exprstack[any] if any._usecount > 1 else any.tojs()

    return json.dumps(any)


def _incusecount(*any):
    for x in any:
        if isinstance(x, _jsexpr):
            x._usecount += 1


class _jsexpr:
    _usecount = 0

    def __init__(self):
        global _exprstack, _scopestack

        if len(_scopestack) > 0:
            _scopestack[-1].subexprstack[self] = None
        else:
            _exprstack[self] = None

    # required because __eq__ has been redefined
    def __hash__(self):
        # not sure if this is a good way of doing it but it seems to work i guess?
        return id(self)

    # +
    def __add__(self, other): return _jsbinop('+', self, other)
    def __radd__(self, other): return _jsbinop('+', other, self)
    # -
    def __sub__(self, other): return _jsbinop('-', self, other)
    def __rsub__(self, other): return _jsbinop('-', other, self)
    # *
    def __mul__(self, other): return _jsbinop('*', self, other)
    def __rmul__(self, other): return _jsbinop('*', other, self)

    # /, //
    def __truediv__(self, other): return _jsbinop('/', self, other)
    def __floordiv__(self, other): return _jsfncall(
        'Math.floor', [_jsbinop('/', self, other)])

    # **
    def __pow__(self, other): return _jsfncall('Math.pow', [self, other])

    # eq, ne, le, ge, gt, lt are their own reflected (__r...__) versions already
    # ==, !=
    def __eq__(self, other): return _jsbinop('===', self, other)
    def __ne__(self, other): return _jsbinop('!==', self, other)
    # >=, <=
    def __ge__(self, other): return _jsbinop('>=', self, other)
    def __le__(self, other): return _jsbinop('<=', self, other)
    # >, <
    def __gt__(self, other): return _jsbinop('>', self, other)
    def __lt__(self, other): return _jsbinop('<', self, other)

    # maybe these two shouldn't really be on the _jsexpr base class but whatever it's convenient this way
    # (used for statements like if/else, for, while, etc.)
    def __enter__(self):
        global _scopestack
        _scopestack.append(self)

    def __exit__(self, exc_type, exc_value, traceback):
        global _scopestack, _lastexitedscope
        _lastexitedscope = _scopestack.pop()

    # uhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh   this is a really bad way of doing this   uhhhhhhhhhhhhhhhhhhhhhhhhh
    def __getattribute__(self, name):
        # simple hierarchy would be: __getattribute__ <-- (user defined js generating function) <-- codegen
        # , note that codegen() calls _internalcodegen() (which accesses _usecount on something) so we need to account for that.
        if inspect.stack()[2][3] == 'codegen' and inspect.stack()[1][3] != '_internalcodegen':
            return _jsaccess(self, name)

        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        # simple hierarchy would be: __getattribute__ <-- (user defined js generating function) <-- codegen
        # , note that codegen() calls _internalcodegen() (which accesses _usecount on something) so we need to account for that.
        if inspect.stack()[2][3] == 'codegen' and inspect.stack()[1][3] != '_internalcodegen':
            return _jssetprop(self, name, value)

        return super().__setattr__(name, value)

    def __call__(self, *args):
        return _jsfncall(self, args, fnisjsobj=True)


class _jsfncall(_jsexpr):
    def __init__(self, fnname, fnargs, fnisjsobj=False):
        super().__init__()

        self.fnname = fnname
        self.fnargs = fnargs
        self.fnisjsobj = fnisjsobj

        _incusecount(fnname, *fnargs)

    def tojs(self, terminal=False):
        return f'{self.fnname if not self.fnisjsobj else _tojs(self.fnname)}({",".join(_tojs(arg) for arg in self.fnargs)})' + (';' if terminal else '')


class _jsbinop(_jsexpr):
    def __init__(self, op, a, b):
        super().__init__()

        self.op = op
        self.a = a
        self.b = b

        _incusecount(a, b)

    def tojs(self, terminal=False):
        ajs = (f'({_tojs(self.a)})' if isinstance(
            self.a, _jsbinop) and not self.a._usecount >= 2 and self.a.op != self.op else _tojs(self.a))
        bjs = (f'({_tojs(self.b)})' if isinstance(
            self.b, _jsbinop) and not self.b._usecount >= 2 else _tojs(self.b))
        return ajs + self.op + bjs + (';' if terminal else '')


class PyJSSyntaxError(Exception):
    pass


class if_(_jsexpr):
    def __init__(self, cond):
        super().__init__()

        self.cond = cond

        # don't try to be "efficient" and put this outside of the __init__ function
        # that won't actually reinitialize the dict everytime a new instance is constructed
        self.subexprstack = {}

        _incusecount(cond)

    def tojs(self, terminal=True):
        return f'if({_tojs(self.cond)}){{{_internalcodegen(self.subexprstack)}}}'


class elseif(_jsexpr):
    def __init__(self, cond):
        global _lastexitedscope
        # as for how _jsexpr and the global stacks are implemented right now, this has to be checked in the constructor
        # , not in __enter__
        if not isinstance(_lastexitedscope, if_) and not isinstance(_lastexitedscope, elseif):
            raise PyJSSyntaxError(
                "elseif can only follow if_ or another elseif")

        super().__init__()

        self.cond = cond
        self.subexprstack = {}

        _incusecount(cond)

    def tojs(self, terminal=True):
        return f'else if({_tojs(self.cond)}){{{_internalcodegen(self.subexprstack)}}}'


class else_(_jsexpr):
    def __init__(self):
        global _lastexitedscope
        # as for how _jsexpr and the global stacks are implemented right now, this has to be checked in the constructor
        # , not in __enter__
        if not isinstance(_lastexitedscope, if_) and not isinstance(_lastexitedscope, elseif):
            raise PyJSSyntaxError("else can only follow if_ or elseif")

        super().__init__()

        self.subexprstack = {}

    def tojs(self, terminal=True):
        return f'else{{{_internalcodegen(self.subexprstack)}}}'


class _jsaccess(_jsexpr):
    def __init__(self, obj, name):
        super().__init__()

        self.obj = obj
        self.name = name

        _incusecount(obj, name)

    def tojs(self, terminal=False):
        return _tojs(self.obj) + (f'.{self.name}' if isvalidjsid(self.name) else f'[{_tojs(self.name)}]') + (';' if terminal else '')


class _jssetprop(_jsexpr):
    def __init__(self, obj, name, value):
        super().__init__()

        self.obj = obj
        self.name = name
        self.value = value

        _incusecount(obj, name, value)

    def tojs(self, terminal=False):
        return _tojs(self.obj) + (f'.{self.name}' if isvalidjsid(self.name) else f'[{_tojs(self.name)}]') + f'={_tojs(self.value)}' + (';' if terminal else '')


def jsfunc(name):
    '''shortcut for creating a jsexpr for a function name'''
    def call(*args):
        return _jsfncall(name, args)

    return call


def _internalcodegen(exprstack):
    js = ''
    lastvar = ''

    for expr in exprstack.keys():
        if expr._usecount == 1:
            continue

        if expr._usecount >= 2:
            lastvar = var = exprstack[expr] = _newvar(lastvar)

        js += (f'let {var}=' if expr._usecount >
               1 else '') + expr.tojs(terminal=True)

    return js


def codegen(func):
    '''for now takes a function and will generate the js code for it'''
    func()

    global _exprstack
    js = _internalcodegen(_exprstack)
    _exprstack = {}

    return js
