#!/usr/bin/env python3
"""Growi記事ランキング投稿
usage:
    $ python ranking.py DST [SRC] [TOP]

    # ランキングを表示するページパスを指定
    $ python ranking.py /Ranking
    # ランキングを表示するページパスとランキング集計元の親ページパスを指定
    $ python ranking.py /Ranking /From/Root
    # ランキングを表示するページパスとランキング集計元の親ページパスとトップ5の集計を指定
    $ python ranking.py /Ranking /From/Root 5
"""
import re
import argparse
from typing import Iterator, Union
from operator import attrgetter
from collections import UserList, namedtuple
from itertools import count
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

    def convert(self) -> list[str]:
        """ランキングリストをGrowiマークダウン形式のリストに変換する"""
        return [
            f"[{rank.path}]({Page.origin}/{rank.id}) :heart:{rank.liker} \
:footprints:{rank.seen} :speech_balloon:{rank.commentCount} \
:pencil2:{rank.authors}" for rank in self.data
        ]

    def order(self, top: int, ids: list[str]) -> list[str]:
        """top(数字)のリストを上位topの数でランキングづけする。
        過去のランクidsがあれば過去ランクとの比較を行う。
        """
        after_ranks: list[str] = self[:top].convert()
        # arrows初期値、idsがないとき==初めてランキングを作るとき
        arrows = ("" for _ in range(top))
        if ids:
            after_ids: list[str] = [i.id for i in self[:top]]
            arrows: Iterator[str] = Ranks.shift(ids, after_ids)
        body = [
            f"{i}. {arrow} {elem}"
            for i, arrow, elem in zip(count(1), arrows, after_ranks)
        ]
        return body

    @staticmethod
    def shift(before: list, after: list) -> Iterator[str]:
        """ afterのインデックスbeforeに比べて上がってたら上、
        下がってたら下、横ばいだったら横の記号をリストで返す。
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
        revisions = Revisions(page._id, limit=100)
        rank = Rank(page.path, page._id, len(page.liker), len(page.seenUsers),
                    page.commentCount, len(revisions.authors()))
        rank_list.append(rank)
    return rank_list


def main(dst: str, src: str = "/", top=10, dryrun=False):
    """Growiページパスsrcからランキング情報を収集し、
    Growiページパスdstへランキングを記したマークダウン形式の文字列を投稿する。
    第2引数以降省略でき、デフォルトで"/"からランキングを作成する。
    """
    ranks: Ranks = init(src)
    rank_page = Page(dst)
    if rank_page.exist:
        before_ids = Ranks.read_ids(rank_page.body)
        before_ids_chunk = chunked(before_ids, top)
    ranking_element = (
        (f"# :heart:ライクが多いランキングトップ{top}\n\n", "liker"),
        (f"\n\n# :footprints:足跡が多いランキングトップ{top}\n\n", "seen"),
        (f"\n\n# :speech_balloon:コメントが多いランキングトップ{top}\n\n", "commentCount"),
        (f"\n\n# :pencil2:編集者が多いランキングトップ{top}\n\n", "authors"),
    )
    page_body = ""
    for title, key in ranking_element:
        ranks.sort(key)
        try:
            chunk = next(before_ids_chunk)
        except (StopIteration, NameError):
            chunk = None
        ranking_md = ranks.order(top, chunk)
        page_body += title
        page_body += "\n".join(ranking_md)

    if dryrun:
        # Just print test
        print(page_body)
        return
    # Post page
    res = rank_page.post(page_body)
    print(res)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dst", help="Growiのランキング表示先ページパス")
    parser.add_argument("src",
                        nargs="?",
                        default="/",
                        help="Growiのランキング集計元ページパス")
    parser.add_argument("top",
                        nargs="?",
                        type=int,
                        default=10,
                        help="ランキング上位数")
    parser.add_argument("-n",
                        "--dryrun",
                        action="store_true",
                        help="標準出力へマークダウンをprintするのみで、記事投稿しない。")
    args = parser.parse_args()
    main(args.dst, args.src, args.top, dryrun=args.dryrun)
