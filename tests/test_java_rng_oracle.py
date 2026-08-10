from __future__ import annotations

import unittest

from minescript.rng_compat import JavaRandom as CompatJavaRandom
from minescript.seed.java_rng import JavaRandom


class JavaRandomOracleTests(unittest.TestCase):
    """Vectors generated with OpenJDK java.util.Random, not F3+ itself."""

    def test_unbounded_next_int_matches_openjdk(self):
        rng = JavaRandom(12345)
        expected = [
            1553932502,
            -2090749135,
            -287790814,
            -355989640,
            -716867186,
            161804169,
            1402202751,
            535445604,
        ]
        self.assertEqual([rng.next_int() for _ in expected], expected)

    def test_non_power_of_two_bound_matches_openjdk(self):
        rng = JavaRandom(0)
        expected = [360, 948, 29, 447, 515, 53, 491, 761]
        self.assertEqual([rng.next_int(1000) for _ in expected], expected)

    def test_signed_overflow_rejection_path_matches_openjdk(self):
        # 2^30 + 1 makes java.util.Random reject roughly half of raw 31-bit draws.
        # A Python port that forgets Java's signed-int overflow diverges immediately.
        rng = JavaRandom(12345)
        expected = [
            776966251,
            80902084,
            701101375,
            267722802,
            505783501,
            75883389,
            749719517,
            962239390,
        ]
        self.assertEqual([rng.next_int(1073741825) for _ in expected], expected)

    def test_compatibility_rng_uses_the_canonical_class(self):
        self.assertIs(CompatJavaRandom, JavaRandom)


if __name__ == "__main__":
    unittest.main()
