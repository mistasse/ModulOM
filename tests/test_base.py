from modulom import WithCache, Dependencies


class Example(WithCache):
    def a(self, param=None, cache_if='param is None'):
        return object()

    def b(self):
        return self.a()

    def c(self):
        return self.a()
    

def test_Example():
    e = Example()
    t = e.a()
    assert t == e.a() == e.b() == e.c()
    a1, a2 = e.a(0), e.a(0)
    assert a1 != a2 and a1 != t


class DepsExample(Dependencies,WithCache):
    def a(self, param=None, cache_if='param is None'):
        return object(),self.x()

    def b(self):
        return self.a()

    def c(self):
        return self.a(0)

    def x(self):
        return object()
    

def test_DepsExample():
    e = DepsExample()
    t = e.a()
    assert t == e.a() == e.b() != e.c()
    a1, a2 = e.a(0), e.a(0)
    assert a1 != a2 and a1 != t
    deps = e._dependencies
    assert deps[('b',)] == {('a',None)}
    assert deps[('c',)] == {('a',0)}
    assert deps[('a',None)] == {('x',)}
    assert deps[('a',0)] == {('x',)}
