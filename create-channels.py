"""
boardとの連絡チャンネルをアーカイブして作り直すスクリプト
"""

import argparse
import os

from slack_sdk import WebClient


# BPメンバーの一覧
BP_MEMBERS = (
    "shimizukawa tommy ae35 altnight tell-k cafistar ray monjudoh natsu"
    "cactusman kk6 nakagami kyoka hydden aoki marippe wan kameko xiao"
    "furi susumuis kashew mtb_beta nao_y fumi23 tsutomu furuta kai"
    "konie hirayama hajimo masashinji imaxyz komo_fr ssh22 kemu yukie"
    "nutty hayaosuzuki delhi09 chieko arty saito"
)
BOARD_MEMBERS = ('haru', 'takanory', '923', 'nana')


def generate_bpmember_list(members):
    """
    Slackの全メンバーから、BPメンバーとボードの一覧を抜き出す
    """
    bp_members = []
    board_members = []

    for member in members:
        # Bot、削除されたメンバー、Guestは対象外
        if member['is_bot'] or member['deleted'] or member['is_restricted'] or member['is_ultra_restricted']:
            continue

        # 名前を取得
        name = member['name']
        profile = member['profile']
        dname = profile['display_name'] or profile['real_name']

        # 除外メンバーは対象外
        if name in EXCLUDE_MEMBERS or dname in EXCLUDE_MEMBERS:
            continue

        # ボードメンバーを取り出す
        if name in BOARD_MEMBERS or dname in BOARD_MEMBERS:
            board_members.append(member)
        else:
            # それ以外はBPメンバー
            bp_members.append(member)
    return bp_members, board_members


def get_private_channels(client):
    """チャンネル一覧を取得

    * https://api.slack.com/methods/conversations.list
    """
    res = client.conversations_list(limit=1000, types='private_channel')
    # チャンネル一覧を取得
    chs = res['channels']

    # u- から始まるチャンネル名のみを返す
    return {ch['name'] for ch in chs if ch['name'].startswith('u-')}


def create_channel(client, member, board_members, channels, dryrun=False):
    """チャンネルを作成する

    * https://api.slack.com/methods/conversations.create
    * https://api.slack.com/methods/conversations.invite
    * https://api.slack.com/methods/conversations.setTopic

    :param client: Slack client
    :param member: チャンネル作成対象のメンバー
    :param board_members: boardのメンバー情報一覧
    :param channels: u- から始まるチャンネル名のセット
    """

    # 名前を取得
    name = member['profile']['display_name']
    if name:
        # 記号を削除
        name = name.replace('-', '').replace('_', '')
    else:
        name = member['name']

    # チャンネル名、トピック
    channel_name = f'u-{name.lower()}-board'
    topic = f'{name}とboardの雑談ちゃんねる https://project.beproud.jp/redmine/projects/bpall/wiki/With-board'

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

    # メンバー一覧を取得
    # https://api.slack.com/methods/users.list
    response = client.users_list()
    bp_members, board_members = generate_bpmember_list(response['members'])
    for member in bp_members:
        print(member["name"])
    #print(board_members)

    # チャンネル一覧を取得
    #channels = get_private_channels(client)

    # チャンネルを作成する
    #for member in bp_members:
    #    create_channel(client, member, board_members, channels, args.dryrun)


if __name__ == '__main__':
    main()
