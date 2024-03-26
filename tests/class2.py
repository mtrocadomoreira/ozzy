class Base:
    __slots__ = ("a", "b", "c")


class Child(Base):
    __slots__ = tuple()
    pass


obj = Base()
obj.__class__ = Child
# -> TypeError: __class__ assignment: 'Child' object layout differs from 'Base'
