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


def main():
    bp_members = []
    board_members = []
    client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])
    response = client.users_list()
    for member in response['members']:
        # breakpoint()

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

    print(len(board_members))
    print(len(bp_members))


if __name__ == '__main__':
    main()
