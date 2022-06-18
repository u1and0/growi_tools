#!/usr/bin/env python3
"""Growi記事ランキング投稿"""
import re
from typing import Iterator
from operator import attrgetter
from collections import UserList, namedtuple
from typing import Union
from more_itertools import chunked
from growi import Page, Revisions

fields = {
    "path": "",
    "id": "",
    "liker": 0,
    "seen": 0,
    "commentCount": 0,
    "authors": 0
}
Rank = namedtuple("Rank", fields.keys(), defaults=fields.values())


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
        return [
            f"[{rank.path}]({Page.origin}/{rank.id}) :heart:{rank.liker} \
:footprints:{rank.seen} :left_speech_bubble:{rank.commentCount} \
:pencil2:{rank.authors}" for rank in self.data
        ]

    def make_page(self, top: int, ids: list[str]) -> str:
        """top(数字)のリストを
        ランキング形式でmarkdown形式の文字列に変換する
        """
        after_ranks: list[str] = self[:top].append_ranking()
        # arrows初期値、idsがないとき==初めてランキングを作るとき
        arrows = ("" for _ in range(top))
        if ids:
            after_ids: list[str] = [i.id for i in self[:top]]
            arrows: Iterator[str] = Ranks.shift(ids, after_ids)
        body = [
            f"{i}. {arrow} {elem}"
            for i, arrow, elem in zip(range(1, 1 + top), arrows, after_ranks)
        ]
        return body

    @staticmethod
    def shift(before: list, after: list) -> Iterator[str]:
        """ afterのインデックスbeforeに比べて上がってたら上
        下がってたら下、横いだったら横の記号をリストで返す
        """
        before_ranks: list[Union[int, float]] = \
            (after.index(i) if i in after else float("inf") for i in before)
        for after_rank, before_rank in enumerate(before_ranks):
            sub: int = before_rank - after_rank
            if sub == float("inf"):
                yield ":new:"
            elif sub > 0:
                yield ":arrow_upper_right:"
            elif sub < 0:
                yield ":arrow_lower_right:"
            else:
                yield ":arrow_right:"

    @staticmethod
    def read_ids(paragraph: str) -> list[str]:
        """paragraph からpage idのみをリストで抜き出す"""
        return re.findall(r"[a-f0-9]{24}", paragraph)


def init(path: str = "/") -> Ranks:
    """Generate List of Rank"""
    page = Page(path)
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
    ranks: Ranks = init("/お試し")
    # Make page
    top = 10
    rank_page = Page("/お試し/Ranking")
    if rank_page.exist:
        before_ids = Ranks.read_ids(rank_page.body)
        before_ids_chunk = chunked(before_ids, top)
    ranking_element = (
        (f"# :heart:ライクが多いランキングトップ{top}\n\n", "liker"),
        (f"\n\n# :footprints:足跡が多いランキングトップ{top}\n\n", "seen"),
        (f"\n\n# :left_speech_bubble:コメントが多いランキングトップ{top}\n\n",
         "commentCount"),
        (f"\n\n# :pencil2:編集者が多いランキングトップ{top}\n\n", "authors"),
    )
    page_body = ""
    for title, key in ranking_element:
        ranks.sort(key)
        try:
            chunk = next(before_ids_chunk)
        except (StopIteration, NameError):
            chunk = None
        ranking_md = ranks.make_page(top, chunk)
        page_body += title
        page_body += "\n".join(ranking_md)

    # Post page
    # res = rank_page.post(page_body)
    # print(res)

    # Just print test
    print(page_body)

    # import doctest
    # doctest.testmod(verbose=True)
