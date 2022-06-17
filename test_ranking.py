"""ranking.py test"""
import unittest
import ranking


class TestRanks_shift(unittest.TestCase):
    """Ranks.shift() test"""
    def test_rank_updown(self):
        """ランク内で順位が変わるケース"""
        be, af = "a b c".split(), "c b a".split()
        self.assertEqual(
            list(ranking.Ranks.shift(be, af)),
            [':arrow_upper_right:', ':arrow_right:', ':arrow_lower_right:'])

    def test_rank_new(self):
        """ランク外から上がってきたケース"""
        be, af = "a b c d".split(), "c b a e".split()
        self.assertEqual(list(ranking.Ranks.shift(be, af)), [
            ':arrow_upper_right:', ':arrow_right:', ':arrow_lower_right:',
            ':new:'
        ])

    def test_rank_new2(self):
        """ランク外から２位に上がってきたケース"""
        be, af = "a b c d".split(), "c e a d".split()
        self.assertEqual(list(ranking.Ranks.shift(be, af)), [
            ':arrow_upper_right:', ':new:', ':arrow_lower_right:',
            ':arrow_right:'
        ])


if __name__ == "__main__":
    unittest.main()
