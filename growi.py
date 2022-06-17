#!/usr/bin/env python3
"""post to Growi
usage:
    $ python growi.py "/user/yourname/test" "# Title\\n\\nここに本文を書きます" """
import os
import sys
import json
from types import SimpleNamespace
import requests

VERSION = "v1.0.0"


class Page:
    """GrowiへのAPIアクセス"""
    _access_token = os.environ["GROWI_ACCESS_TOKEN"]  # if unset raise KeyError
    origin = os.environ.get("GROWI_URL", "http://localhost:3000/_api")

    def __init__(self, path, **kwargs):
        """GrowiへのAPIアクセス
        # Usage
        環境変数に `_GROWI_ACCESS_TOKEN` `GROWI_URL` をセットする必要がある。
        Pythonコンソール上で行うには、

        >>> import os
        >>> os.environ["GROWI_ACCESS_TOKEN"] = "****"
        >>> os.environ["GROWI_URL"] = "http://192.168.***.***:3000/_api"

        `GROWI_ACCESS_TOKEN`を設定しない場合、KeyErrorを吐いてプログラムは終了する。
        `GROWI_URL`を設定しない場合、"http://localhost:3000/_api"が割り当てられる。

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

    def _create(self, body, **kwargs):
        """パスの内容へbodyを書き込む"""
        data = {
            "body": body,
            "path": self.path,
            "access_token": Page._access_token,
        }
        data.update(**kwargs)
        res = requests.post(Page.origin + "/v3/pages", data)
        return res.json()

    def _update(self, body, **kwargs):
        """パスの内容をbodyで更新する"""
        if body == self.body:
            return json.loads('{"error": "更新前後の内容が同じですので、更新しませんでした。"}')
        data = {
            "page_id": self.id,
            "revision_id": self.revision_id,
            "body": body,
            "access_token": Page._access_token,
        }
        data.update(**kwargs)
        res = requests.post(Page.origin + "/pages.update", data)
        return res.json()

    def post(self, body, **kwargs):
        """指定パスに
        ページが存在すれば_update(),
        ページが存在しなければ_create()
        で引数bodyの内容を上書き/書込みする。
        """
        if self.exist:
            json_resp = self._update(body, **kwargs)
        else:
            json_resp = self._create(body, **kwargs)
        return json_resp

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
        res = requests.get(Page.origin + "/v3/page", params)
        # Simplanamespaceをobject_hookしてやることで
        # json()で返ってきた辞書を再帰的にnamespace化する。
        # すなわちドットプロパティアクセスができる。
        if prop_access:
            return res.json(object_hook=lambda d: SimpleNamespace(**d))
        return res.json()

    def list(self, prop_access=False, **kwargs):
        """ パス配下の情報をJSONで取得する """
        params = {
            "path": self.path,
            "access_token": Page._access_token,
        }
        params.update(**kwargs)
        res = requests.get(Page.origin + "/pages.list", params)
        if prop_access:
            return res.json(object_hook=lambda d: SimpleNamespace(**d))
        return res.json()


class Revisions:
    """更新情報を取得"""
    url = Page.origin + "/v3/revisions/list"

    # page=0のクエリーパラメータの意味が分かっていない
    def __init__(self, id, page=0, **kwargs):
        """ページの更新情報を取得するAPI
        pageのidでインスタンス化する。
        idの取得はPage("/path").id
        """
        self.page_id: str = id
        self.page: int = page
        self._json = self.get(1, **kwargs)
        self.totalDocs: int = self._json.totalDocs
        self.docs: list = self._json.docs

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
        return {d.author._id for d in self.docs}


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        exit(0)
    if len(sys.argv) < 2:
        print(__doc__)
        exit(1)
    if "-v" in sys.argv or "--version" in sys.argv:
        print(f"growi.py version: {VERSION}")
        exit(0)
    page = Page(sys.argv[-2])
    print(page.post(sys.argv[-1]))
