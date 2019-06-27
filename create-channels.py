"""
boardとの連絡チャンネルを作るスクリプト
"""

import os

import slack


# 除外メンバーとボードメンバーの一覧
EXCLUDE_MEMBERS = (
    'slackbot', 'aodag', 'opapy', 'tokibito', 'ikasamt', 'crohaco',
    'shinichitsuchiya', 'kuwai', 'yosuke', 'tsuyoshi', 'nishio',
    'kentaro_shima', 'checkroth', 'oshima', 'xiao669', 'atsushi_suzuki',
    'hit-kumada', 'hit-hata', 'fujita', 'kw_park', 'soojin',
    'takeru.furuse',
)
BOARD_MEMBERS = ('haru', 'takanory', 'shimizukawa')


def generate_bpmember_list(members):
    """
    Slackの前メンバーから、BPメンバーとボードの一覧を抜き出す
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


def create_channel(client, member, board_members):
    """チャンネルを作成する

    * https://api.slack.com/methods/groups.create
    * https://api.slack.com/methods/groups.invite
    * https://api.slack.com/methods/groups.setTopic
    * https://api.slack.com/methods/groups.setPurpose
    """

    # 名前を取得
    name = member['profile']['display_name']
    if name:
        # 記号を削除
        name = name.replace('-', '').replace('_', '')
    else:
        name = member['name']

    # チャンネル名、トピック
    channel_name = f'u-{name}-board'
    topic = f'{name}とboardの連絡用チャンネル'

    # テスト用に3名に限定
    if name not in ('fumi23', 'masashinji', 'imaxyz'):
        return

    response = client.groups_create(name=channel_name)
    # チャンネルの作成に成功
    if response['ok']:
        channel_id = response['group']['id']

        # メンバーを追加
        client.groups_invite(channel=channel_id, user=member['id'])
   
        # boardメンバーを追加
        for board in board_members:
            if board['name'] != 'takanory':
                client.groups_invite(channel=channel_id, user=board['id'])

        # topicとpurposeを設定
        client.groups_setTopic(channel=channel_id, topic=topic)

        print(f'{channel_name} を作成しました')


def main():
    client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])

    # メンバー一覧を取得
    # https://api.slack.com/methods/users.list
    response = client.users_list()
    bp_members, board_members = generate_bpmember_list(response['members'])

    # print(len(board_members))
    # print(len(bp_members))

    # チャンネルを作成する
    for member in bp_members:
        create_channel(client, member, board_members)


if __name__ == '__main__':
    main()
