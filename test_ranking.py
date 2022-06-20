"""ranking.py test"""
import os
import unittest


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


class TestRanks_order(unittest.TestCase):
    """Ranks.order() test"""
    def test_rank(self):
        rank1 = ranking.Rank(path="/rank1", id="1111", liker=0)
        rank2 = ranking.Rank(path="/rank2", id="2222", liker=1)
        rank3 = ranking.Rank(path="/rank3", id="3333", liker=2)
        ranks = ranking.Ranks([rank1, rank2, rank3])
        ids = ["1111", "2222", "3333"]
        top = 3
        ranks.sort("liker")
        actual = ranks.order(top, ids)
        expected = [
            "1. :arrow_upper_right: [/rank3](https://demo.growi.org/3333) \
:heart:2 :footprints:0 :speech_balloon:0 :pencil2:0",
            "2. :arrow_right: [/rank2](https://demo.growi.org/2222) \
:heart:1 :footprints:0 :speech_balloon:0 :pencil2:0",
            "3. :arrow_lower_right: [/rank1](https://demo.growi.org/1111) \
:heart:0 :footprints:0 :speech_balloon:0 :pencil2:0",
        ]
        self.assertEqual(actual, expected)


class TestRanks_order_newcase(unittest.TestCase):
    """Ranks.order() test"""
    def test_rank(self):
        rank1 = ranking.Rank(path="/rank1", id="1111", liker=0)
        rank2 = ranking.Rank(path="/rank2", id="2222", liker=1)
        rank3 = ranking.Rank(path="/rank3", id="3333", liker=2)
        rank4 = ranking.Rank(path="/rank4", id="4444", liker=10)
        ranks = ranking.Ranks([rank1, rank2, rank3, rank4])
        ids = ["1111", "2222", "3333"]
        top = 3
        ranks.sort("liker")
        actual = ranks.order(top, ids)
        expected = [
            "1. :new: [/rank4](https://demo.growi.org/4444) \
:heart:10 :footprints:0 :speech_balloon:0 :pencil2:0",
            "2. :arrow_upper_right: [/rank3](https://demo.growi.org/3333) \
:heart:2 :footprints:0 :speech_balloon:0 :pencil2:0",
            "3. :arrow_lower_right: [/rank2](https://demo.growi.org/2222) \
:heart:1 :footprints:0 :speech_balloon:0 :pencil2:0",
        ]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    # Set env for test
    os.environ["GROWI_ACCESS_TOKEN"] = ""
    os.environ["GROWI_URL"] = "https://demo.growi.org"
    import ranking
    unittest.main()
