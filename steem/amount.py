class Amount(object):
    def __init__(self, amountString="0 SBD"):
        self.amount, self.asset = amountString.split(" ")
        self.amount = float(self.amount)

    def __str__(self):
        if self.asset == "SBD":
            prec = 3
        elif self.asset == "STEEM":
            prec = 3
        elif self.asset == "VESTS":
            prec = 6
        else:
            prec = 6
        return "{:.{prec}f} {}".format(self.amount, self.asset, prec=prec)

    def __float__(self):
         return self.amount

    def __int__(self):
         return int(self.amount)

    def __add__(self, other):
        assert self.asset == other.asset
        a = Amount(str(self))
        a.amount += other.amount
        return a

    def __sub__(self, other):
        assert self.asset == other.asset
        a = Amount(str(self))
        a.amount -= other.amount
        return a

    def __mul__(self, other):
        assert self.asset == other.asset
        a = Amount(str(self))
        a.amount *= other.amount
        return a

    def __floordiv__(self, other):
        assert self.asset == other.asset
        a = Amount(str(self))
        a.amount //= other.amount
        return a

    def __div__(self, other):
        assert self.asset == other.asset
        a = Amount(str(self))
        a.amount /= other.amount
        return a

    def __mod__(self, other):
        assert self.asset == other.asset
        a = Amount(str(self))
        a.amount %= other.amount
        return a

    def __pow__(self, other):
        assert self.asset == other.asset
        a = Amount(str(self))
        a.amount **= other.amount
        return a

    __repr__ = __str__
    __iadd__ = __add__
    __isub__ = __sub__
    __imul__ = __mul__
    __idiv__ = __div__
    __ifloordiv__ = __floordiv__
    __imod__ = __mod__
    __ipow__ = __pow__


if __name__ == "__main__":
    a = Amount("2 SBD")
    b = Amount("9 SBD")
    print(a + b)
    print(b)
    b **= a
    print(b)
