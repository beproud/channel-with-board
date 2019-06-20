# boardとの連絡チャンネルを作るスクリプト

## 目的

* boardと各メンバーが連絡するためのプライベートチャンネルをSlackに作る
* 全メンバー分を手作業で作るのがだるいので、自動的に作られるようにする

## 環境構築

* [slackclient](https://pypi.org/project/slackclient/) に依存(する予定)

```sh
$ python3.7 -m venv env
$ . env/bin/activate
(env) $ pip install -r requirements.txt
```

## 認証

* Slack APIでチャンネル作成するためにはuser token(`xoxp-` ではじまる)が必要
* user tokenは OAuth 2.0 で以下の手順で取得する必要がある
  * 参考: [Using OAuth 2.0](https://api.slack.com/docs/oauth)
