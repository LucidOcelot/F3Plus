MASK = (1 << 48) - 1
MULT = 0x5DEECE66D
ADD = 0xB

class JavaRandom:
    def __init__(self, seed:int):
        self.seed = (int(seed) ^ MULT) & MASK
    def next(self,bits:int):
        self.seed = (self.seed*MULT + ADD) & MASK
        return self.seed >> (48-bits)
    def next_int(self,bound=None):
        if bound is None:
            v=self.next(32); return v-(1<<32) if v>=(1<<31) else v
        if bound<=0: raise ValueError("bound must be positive")
        if (bound & (bound-1)) == 0:
            return (bound*self.next(31)) >> 31
        while True:
            bits=self.next(31); val=bits%bound
            test=(bits-val+(bound-1)) & 0xFFFFFFFF
            if test < 0x80000000: return val
    def next_long(self):
        # java.util.Random: ((long) next(32) << 32) + next(32). Both next(32)
        # results are Java signed ints before promotion to long.
        hi=self.next(32); lo=self.next(32)
        hi=hi-(1<<32) if hi>=(1<<31) else hi
        lo=lo-(1<<32) if lo>=(1<<31) else lo
        v=((hi<<32)+lo) & 0xFFFFFFFFFFFFFFFF
        return v-(1<<64) if v>=(1<<63) else v
