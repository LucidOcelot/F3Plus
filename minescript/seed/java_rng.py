MASK = (1 << 48) - 1
MULT = 0x5DEECE66D
ADD = 0xB


class JavaRandom:
    """java.util.Random compatible 48-bit LCG.

    The rejection branch in ``next_int(bound)`` deliberately emulates Java's signed
    32-bit overflow. Python integers do not overflow, so comparing the unbounded Python
    expression directly would accept values that Java rejects and desynchronize every
    subsequent RNG state.
    """

    def __init__(self, seed: int):
        self.seed = (int(seed) ^ MULT) & MASK

    def next(self, bits: int):
        self.seed = (self.seed * MULT + ADD) & MASK
        return self.seed >> (48 - bits)

    def next_int(self, bound=None):
        if bound is None:
            value = self.next(32)
            return value - (1 << 32) if value >= (1 << 31) else value
        bound = int(bound)
        if bound <= 0:
            raise ValueError("bound must be positive")
        if (bound & (bound - 1)) == 0:
            return (bound * self.next(31)) >> 31
        while True:
            bits = self.next(31)
            value = bits % bound
            # java.util.Random tests ``bits - value + (bound - 1) >= 0`` using a
            # signed 32-bit int. Reproduce that overflow before deciding to accept.
            test = (bits - value + (bound - 1)) & 0xFFFFFFFF
            if test < 0x80000000:
                return value

    def next_long(self):
        # java.util.Random: ((long) next(32) << 32) + next(32). Both next(32)
        # results are Java signed ints before promotion to long.
        hi = self.next(32)
        lo = self.next(32)
        hi = hi - (1 << 32) if hi >= (1 << 31) else hi
        lo = lo - (1 << 32) if lo >= (1 << 31) else lo
        value = ((hi << 32) + lo) & 0xFFFFFFFFFFFFFFFF
        return value - (1 << 64) if value >= (1 << 63) else value

    def next_float(self) -> float:
        return self.next(24) / float(1 << 24)

    def next_double(self) -> float:
        return ((self.next(26) << 27) + self.next(27)) / float(1 << 53)
