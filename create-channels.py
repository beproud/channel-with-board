"""
boardとの連絡チャンネルをアーカイブして作り直すスクリプト
"""

import argparse
import os

from slack_sdk import WebClient


def get_userids_by_usergroup(client: WebClient, handle: str) -> list[str] | None:
    """指定されたユーザーグループのユーザー一覧を返す

    * https://api.slack.com/methods/usergroups.list
    * https://api.slack.com/methods/usergroups.users.list

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
                   channels: dict[str, str], dryrun=True):
    """チャンネルを作成する

    * https://api.slack.com/methods/conversations.archive
    * https://api.slack.com/methods/conversations.create
    * https://api.slack.com/methods/conversations.invite
    * https://api.slack.com/methods/conversations.setTopic

    :param client: Slack WebClient
    :param member: チャンネル作成対象のメンバー情報
    :param board: boardのユーザーID一覧
    :param channels: 既存のu-NAME-boardチャンネル名とIDの辞書
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

    print(channel_name)
    print(topic)
    print(channels[channel_name])
    
    return

    if channel_name in channels:
        print(f'チャンネル {channel_name} はすでに存在します')
    else:
        if dryrun:
            # dryrunの場合はメッセージのみを出力する
            print(f'{channel_name} を作成しました(dry run)')
        else:
            response = client.conversations_create(name=channel_name,
                                                   is_private=True)
            channel_id = response['channel']['id']

            # メンバーとboardメンバーのIDリストを作成して追加
            users = [member['id']]
            for board in board_members:
                if board['name'] != 'takanory':
                    users.append(board['id'])
            client.conversations_invite(channel=channel_id, users=users)

            # topicを設定
            client.conversations_setTopic(channel=channel_id, topic=topic)

            # メッセージを送信
            msg = f'このチャンネルは *{name}とboardの雑談ちゃんねる* です。役員と雑談したり、個人的なことを気軽に相談したりしてください :party_parrot:\n詳しくはトピックに設定してあるリンクをクリックしてください :bow:'
            client.chat_postMessage(channel=channel_id, text=msg)
            print(f'{channel_name} を作成しました')


def main():
    # --dryrun引数に対応
    parser = argparse.ArgumentParser(
        description='Create Slack channel with board.')
    parser.add_argument('--dryrun', help='dry run', action='store_true')
    args = parser.parse_args()

    client = WebClient(token=os.environ['SLACK_API_TOKEN'])

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

    # 全メンバーのチャンネルを作成する
    for user_id in employees:
        if user_id in board:
            # boardメンバーは対象外
            continue
        # print(user_id)
        member = members[user_id]
        # 1メンバーのチャンネルを作成する
        create_channel(client, member, board, channels, args.dryrun)


if __name__ == '__main__':
    main()
