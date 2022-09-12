"""
boardとの連絡チャンネルをアーカイブして作り直すスクリプト
"""

import argparse
import os
import random

from slack_sdk import WebClient


def get_userids_by_usergroup(client: WebClient, handle: str) -> list[str] | None:
    """指定されたユーザーグループのユーザー一覧を返す

    * https://api.slack.com/methods/usergroups.list
    * https://api.slack.com/methods/usergroups.users.list

    OAuth Scope: usergroups:read

    handle: ユーザーグループのメンションに使用する文字列(employees, board等)
    """

    userids = None

    # ユーザーグループの一覧を取得
    groups = client.usergroups_list()
    for group in groups["usergroups"]:
        if group["handle"] == handle:
            # ユーザーグループ内のユーザーIDのリスト
            data = client.usergroups_users_list(usergroup=group["id"])
            userids = data["users"]
            break

    return userids


def get_u_private_channels(client: WebClient) -> dict[str, str]:
    """u-NAME-board 形式のprivateチャンネル一覧を取得

    * https://api.slack.com/methods/conversations.list
    """
    # チャンネル一覧を取得
    res = client.conversations_list(limit=1000, types="private_channel")

    # u- から始まるチャンネル名のみを返す
    channels = {}
    for channel in res["channels"]:
        name = channel["name"]
        if name.startswith("u-") and name.endswith("-board"):
            channels[name] = channel["id"]
    return channels


def create_channel(client: WebClient, member: dict, board: list[str],
                   channels: dict[str, str], parrot: str, dryrun=True):
    """チャンネルを作成する

    * https://api.slack.com/methods/conversations.archive
    * https://api.slack.com/methods/conversations.create
    * https://api.slack.com/methods/conversations.invite
    * https://api.slack.com/methods/conversations.setTopic

    :param client: Slack WebClient
    :param member: チャンネル作成対象のメンバー情報
    :param board: boardのユーザーID一覧
    :param channels: 既存のu-NAME-boardチャンネル名とIDの辞書
    :param parrot: partyparrot emoji
    """

    # 名前を取得
    name = member["profile"]["display_name"]
    if not name:
        name = member["name"]

    # 休みの表記があれば削除
    if "(" in name:
        name = name.split("(")[0]

    # チャンネル名を作成
    simple_name = name.replace('-', '').replace('_', '')
    channel_name = f"u-{simple_name.lower()}-board"

    # チャンネル名、トピック
    topic = (
        f"{name}とboardの雑談ちゃんねる "
        "https://project.beproud.jp/redmine/projects/bpall/wiki/With-board"
    )

    if channel_name in channels:
        if dryrun:
            # dryrunの場合はメッセージのみを出力する
            print(f"{channel_name} をアーカイブしました(dry run)")
        else:
            # 既存のチャンネルをアーカイブする
            client.conversations_archive(channels[channel_name])
            print(f"{channel_name} をアーカイブしました")

    if dryrun:
        # dryrunの場合はメッセージのみを出力する
        print(f"{channel_name} を作成しました(dry run)")
    else:
        response = client.conversations_create(name=channel_name,
                                               is_private=True)
        channel_id = response["channel"]["id"]

        # メンバーとboardメンバーをチャンネルに追加
        users = [member["id"]]
        users += board
        # https://api.slack.com/methods/conversations.invite
        client.conversations_invite(channel=channel_id, users=users)

        # topicを設定
        # https://api.slack.com/methods/conversations.setTopic
        client.conversations_setTopic(channel=channel_id, topic=topic)

        # メッセージを送信
        msg = (
            f"このチャンネルは *{name}とboardの雑談ちゃんねる* です。"
            "役員と雑談したり、個人的なことを気軽に相談したりしてください "
            ":{parrot}:\n"
            "詳しくはトピックに設定してあるリンクをクリックしてください :bow:"
        )
        client.chat_postMessage(channel=channel_id, text=msg)
        print(f"{channel_name} を作成しました")


def main():
    # --dryrun引数に対応
    parser = argparse.ArgumentParser(
        description='Create Slack channel with board.')
    parser.add_argument('--dryrun', help='dry run', action='store_true')
    args = parser.parse_args()

    client = WebClient(token=os.environ['SLACK_API_TOKEN'])

    # parrotのemojiリストを取得
    # OAuth Scope: emoji:read
    data = client.emoji_list(limit=1000)
    parrots = [emoji for emoji in data["emoji"] if "parrot" in emoji]

    # Slack内の全ユーザー情報を取得
    # https://api.slack.com/methods/users.list
    data = client.users_list()
    # ユーザーIDをキーにした辞書に変換する
    members = {m["id"]: m for m in data["members"]}

    # employeesとboardユーザーグループのユーザーIDを取得
    employees = get_userids_by_usergroup(client, "employees")
    board = get_userids_by_usergroup(client, "board")

    # u-NAME-boardチャンネル一覧を取得
    channels = get_u_private_channels(client)

    # print(employees)
    # print(board)
    # print(channels)

    # employees から board を除外する(チャンネル作らないので)
    employees_set = set(employees) - set(board)

    # boardからtakanoryのidを除外する(チャンネル作成時に参加するので)
    for member in members.values():
        if member["profile"]["display_name"].startswith("takanory"):
            board.remove(member["id"])

    # 全メンバーのチャンネルを作成する
    for user_id in employees_set:
        # print(user_id)
        member = members[user_id]
        # 1メンバーのチャンネルを作成する
        parrot = random.choice(parrots)
        create_channel(client, member, board, channels, parrot, args.dryrun)


if __name__ == '__main__':
    main()
