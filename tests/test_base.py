from modulom import WithCache, Graph


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


class GraphExample(Graph,WithCache):
    def a(self, param=None, cache_if='param is None'):
        return object(),self.x()

    def b(self):
        return self.a()

    def c(self):
        return self.a(0)

    def x(self):
        return object()
    

def test_GraphExample():
    e = GraphExample()
    t = e.a()
    assert t == e.a() == e.b() != e.c()
    a1, a2 = e.a(0), e.a(0)
    assert a1 != a2 and a1 != t
    graph = e._graph
    assert graph[('b',)] == {('a',None)}
    assert graph[('c',)] == {('a',0)}
    assert graph[('a',None)] == {('x',)}
    assert graph[('a',0)] == {('x',)}
