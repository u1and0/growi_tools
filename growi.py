#!/usr/bin/env python3
"""post to Growi
usage:
    $ python growi.py "/user/yourname/test" "# Title\\n\\nここに本文を書きます" """
import os
import sys
import json
from types import SimpleNamespace
from typing import Optional
import requests

VERSION = "v1.0.1"


class Page:
    """GrowiへのAPIアクセス"""
    _access_token = os.environ["GROWI_ACCESS_TOKEN"]  # if unset raise KeyError
    origin = os.environ.get("GROWI_URL", "http://localhost:3000")

    def __init__(self, path, **kwargs):
        """GrowiへのAPIアクセス
        # Usage
        環境変数に `_GROWI_ACCESS_TOKEN` `GROWI_URL` をセットする必要がある。
        Pythonコンソール上で行うには、

        >>> import os
        >>> os.environ["GROWI_ACCESS_TOKEN"] = "****"
        >>> os.environ["GROWI_URL"] = "http://192.168.***.***:3000"

        `GROWI_ACCESS_TOKEN`を設定しない場合、KeyErrorを吐いてプログラムは終了する。
        `GROWI_URL`を設定しない場合、"http://localhost:3000"が割り当てられる。

        # Example
        page = Page("/user/myname")

        page.exist: ページが存在するならTrue
        page._json: page.get()で返ってくるJSONオブジェクト
                    ドットプロパティアクセスできる
        page.get(): パスのページをJSONで取得する
        page.post(body): パスの内容へbodyを書き込むか上書きする
        page.list(): パス配下の情報をJSONで取得する
        """
        self.path = path
        self._json = self.get(1, **kwargs)
        # 以降はデフォルト値
        self.body: Optional[str] = None
        self.exist: bool = False
        self.id: Optional[str] = None
        self.revision_id: Optional[str] = None
        # =>
        # {"page":
        # "id":...,
        # "revision"{...},
        # "path":...,
        # }
        try:
            self._json = self._json.page
        except AttributeError:
            self.exist = False
            self.errors = self._json.errors
        else:
            self.exist = True
            self.id = self._json.id
            self.revision_id = self._json.revision._id
            self.body = self._json.revision.body

    def create(self, body, **kwargs):
        """パスの内容へbodyを書き込む"""
        data = {
            "body": body,
            "path": self.path,
            "access_token": Page._access_token,
        }
        data.update(**kwargs)
        res = requests.post(Page.origin + "/_api/v3/page", data)
        res.raise_for_status()  # 200番台以外のステータスコードでraiseして以下は実行されない
        self.body = body
        return res.json()

    def update(self, body, **kwargs):
        """パスの内容をbodyで更新する"""
        if body == self.body:
            return json.loads('{"error": "更新前後の内容が同じなので、更新しませんでした。"}')
        data = {
            "pageId": self.id,
            "body": body,
            "revisionId": self.revision_id,
            "access_token": Page._access_token,
        }
        data.update(**kwargs)

        res = requests.put(Page.origin + "/_api/v3/page", data)
        res.raise_for_status()  # 200番台以外のステータスコードでraiseして以下は実行されない
        self.body = body
        return res.json()

    def post(self, body, **kwargs):
        """指定パスに
        ページが存在すればupdate(),
        ページが存在しなければcreate()
        で引数bodyの内容を上書き/書込みする。
        """
        if self.exist:
            return self.update(body, **kwargs)
        else:
            return self.create(body, **kwargs)

    def get(self, prop_access=False, **kwargs):
        """ パスのページをJSONで取得する
        prop_access=True でJSONオブジェクトをデフォルトの辞書ではなく
        ドットプロパティアクセスできるSimpleNamespaceの形式で取得する。
        usage:
            page = Page("...")
            page.get(0) => 普通のJSONオブジェクト
            page.get(1) => Pythonコンソールにてドットプロパティアクセス
        """
        params = {
            "path": self.path,  # 勝手にurlencodeされる
            # ので、urllib.parse.quoteなどの処理は不要
            "access_token": Page._access_token,
        }
        params.update(**kwargs)
        res = requests.get(Page.origin + "/_api/v3/page", params)
        # Simplanamespaceをobject_hookしてやることで
        # json()で返ってきた辞書を再帰的にnamespace化する。
        # すなわちドットプロパティアクセスができる。
        if prop_access:
            return res.json(object_hook=lambda d: SimpleNamespace(**d))
        return res.json()

    def list(self, prop_access=False, limit=1000, **kwargs):
        """ パス配下の情報をJSONで取得する
        prop_access=Trueにすると、ドッドプロパティアクセスができるので、
        ipython上でプロパティアクセスしやすい

        >>> page = Page("/")

        # 101までページの情報を取得
        >>> tree = page.list(prop_access=True, limit=100)

        # "/"配下の全てのページパス
        >>> page_paths = [i.path for i in tree.pages]

        # 最初のページの情報をdocに格納
        >>> doc = Page(page_paths[0])

        # /配下の全てのページのタイトルと内容の最初の50文字を辞書形式で取得
        >>> {growi.Page(p).path:growi.Page(p).body[:50] for p in pages_path}
        """
        params = {
            "pagePath": self.path,
            "access_token": Page._access_token,
            "limit": limit,
        }
        params.update(**kwargs)
        res = requests.get(Page.origin + "/_api/v3/page-listing", params)
        if prop_access:
            return res.json(object_hook=lambda d: SimpleNamespace(**d))
        return res.json()


class Revisions:
    """更新情報を取得"""
    url = Page.origin + "/_api/v3/revisions/list"

    # page=0のクエリーパラメータの意味が分かっていない
    def __init__(self, id, page=0, **kwargs):
        """ページの更新情報を取得するAPI
        pageのidでインスタンス化する。
        idの取得はPage("/path").id
        """
        self.page_id: str = id
        self.page: int = page
        self._json = self.get(1, **kwargs)
        # Growi v6.1.12 へ移行したらtotalDocsとdocsの名称が変わった？
        self.totalCount: int = self._json.totalCount
        self.revisions: list = self._json.revisions

    def get(self, prop_access=False, **kwargs):
        params = {
            "pageId": self.page_id,
            "page": self.page,
            "access_token": Page._access_token,
        }
        params.update(**kwargs)
        res = requests.get(Revisions.url, params)
        if prop_access:
            return res.json(object_hook=lambda d: SimpleNamespace(**d))
        return res.json()

    def authors(self):
        """編集者id(重複なし)を返す"""
        return {d.author._id if d.author else "" for d in self.revisions}


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if "-v" in sys.argv or "--version" in sys.argv:
        print(f"growi.py version: {VERSION}")
        sys.exit(0)
    page = Page(sys.argv[-2])
    print(page.post(sys.argv[-1]))
