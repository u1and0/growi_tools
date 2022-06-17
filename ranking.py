#!/usr/bin/env python3
"""Growi記事ランキング投稿"""
import re
from itertools import count
from operator import attrgetter
from collections import UserList, namedtuple
from typing import Union
from more_itertools import chunked
from growi import Page, Revisions

Rank = namedtuple(
    "Rank",
    [
        # 要素の最後に , を付け忘れがち
        "path",  # str
        "id",  # str
        "liker",  # int
        "seen",  # int
        "commentCount",  # int
        "authors",  # int
    ])


class Ranks(UserList):
    """Growi記事ランキング"""
    def __init__(self, *args):
        """List of Rank"""
        super().__init__(*args)

    def sort(self, key: str, reverse=True):
        """ランキングのリストに対してkeyでソートをかける"""
        return self.data.sort(key=attrgetter(key), reverse=reverse)

    def append_ranking(self) -> list[str]:
        """ランキングリストをGrowiマークダウン形式に書き換える"""
        # "/_api/" を削る処理
        length = len("http://url.ipa.ddr.ess:port")
        url = Page.origin[:Page.origin.index("/", length)]
        body = [
            f"[{rank.path}]({url}/{rank.id}) ❤ {rank.liker} \
👣{rank.seen} 🗨{rank.commentCount} ✏{rank.authors}" for rank in self.data
        ]
        return body

    def make_page(self, title: str, key: str, top: int, ids: list[str]) -> str:
        """タイトル行を追加し、keyでソートしたtop(数字)のリストを
        ランキング形式でmarkdown形式の文字列に変換する
        """
        self.sort(key)
        rankmd: list[str] = self[:top].append_ranking()
        after_ids: list[str] = [i.id for i in self[:top]]
        arrows: list[str] = Ranks.shift(ids, after_ids)
        body: str = title + "\n".join(
            f"{i}. {arrow} {elem}"
            for i, arrow, elem in zip(count(1), arrows, rankmd))
        return body

    @staticmethod
    def shift(before: list, after: list) -> list[str]:
        """
        afterのインデックスbeforeに比べて上がってたら上
        下がってたら下、横いだったら横の記号をリストで返す
        >>> be, af = "a b c".split(), "c b a".split()
        >>> ranking_shift(be, af)
        ['↗', '➡', '↘']
        >>> be, af = "a b c d".split(), "c b a e".split()
        >>> ranking_shift(be, af)
        ['↗', '➡', '↘', '↗']
        >>> be, af = "a b c d".split(), "c e a d".split()
        >>> ranking_shift(be, af)
        ['↗', '↗', '↘', '➡']
        """
        before_ranks: list[Union[int, float]] = \
            (after.index(i) if i in after else float('inf') for i in before)
        li: list[str] = []
        for after_rank, before_rank in enumerate(before_ranks):
            sub: int = before_rank - after_rank
            if sub > 0:
                li.append("↗")
            elif sub < 0:
                li.append("↘")
            else:
                li.append("➡")
        return li

    @staticmethod
    def read_ids(paragraph: str) -> list[str]:
        """paragraph からpage idのみをリストで抜き出す"""
        return re.findall(r"[a-f0-9]{24}", paragraph)


def init() -> Ranks:
    """Generate List of Rank"""
    page = Page("/")
    pages = page.list(prop_access=True, limit=1000).pages
    rank_list = Ranks()
    for page in pages:
        if page.path == "/":  # rootは編集者なしでエラーなので除外
            continue  # 最初必ず見る場所なので、足跡が必ず1位になるので除外
        revisions = Revisions(page._id, limit=100)
        rank = Rank(page.path, page._id, len(page.liker), len(page.seenUsers),
                    page.commentCount, len(revisions.authors()))
        rank_list.append(rank)
    return rank_list


if __name__ == "__main__":
    ranks: Ranks = init()
    # Make page
    top = 10
    rank_page = Page("/Sidebar")
    before_ids = Ranks.read_ids(rank_page.body)
    before_ids_chunk = chunked(before_ids, top)
    ranking_element = (
        (f"# ❤ライクが多いランキングトップ{top}\n\n", "liker"),
        (f"\n\n # 👣足跡が多いランキングトップ{top}\n\n", "seen"),
        (f"\n\n # 🗨コメントが多いランキングトップ{top}\n\n", "commentCount"),
        (f"\n\n # ✏編集者が多いランキングトップ{top}\n\n", "authors"),
    )
    page_body = ""
    for title, key in ranking_element:
        page_body += ranks.make_page(title, key, top, next(before_ids_chunk))

    # Post page
    res = rank_page.post(page_body)
    print(res)

    # Just print test
    # print(page_body)

    # import doctest
    # doctest.testmod(verbose=True)
