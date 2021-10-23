import argparse
import requests
import time

from collect_chat import collect_chat_from_channel
from collections import deque


def clip_live_channel(broadcaster_id: int, oauth_token: str, client_id: int) -> str:
    url = f"https://api.twitch.tv/helix/clips?broadcaster_id={broadcaster_id}"
    response_json = requests.post(url, headers={"Authorization": f"Bearer {oauth_token}",
                                                "Client-Id": client_id}).json()

    return response_json["data"][0]["id"] if "data" in response_json else ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Clip hype moments from a live channel.')
    parser.add_argument('channel', type=str,
                        help='Twitch channel ID to collect chat from.')
    parser.add_argument('broadcaster_id', type=int,
                        help='Broadcaster Id from the desired channel.')
    parser.add_argument('client_id', type=str,
                        help='Twitch client_id associated with the OAUTH token.')
    parser.add_argument('oauth_token', type=str,
                        help='Twitch OAUTH token with "chat:read", "chat:edit" and "clips:edit" scope permissions.')
    parser.add_argument('nickname', type=str,
                        help='Twitch nickname associated with the OAUTH token.')

    args = parser.parse_args()

    time_to_ignore_messages = 15  # seconds
    number_of_messages_for_a_hype = 5
    latest_laugh_moments: deque[float] = deque()

    channel = collect_chat_from_channel(
        args.channel, args.oauth_token, args.nickname)
    for msg in channel():
        while latest_laugh_moments and latest_laugh_moments[0] + time_to_ignore_messages < time.time():
            latest_laugh_moments.popleft()

        if "lul" in msg.casefold() or "kek" in msg.casefold():
            latest_laugh_moments.append(time.time())

        if len(latest_laugh_moments) >= number_of_messages_for_a_hype:
            latest_laugh_moments.clear()
            clip_id = clip_live_channel(
                args.broadcaster_id, args.oauth_token, args.client_id)
            print("CLIPPED AND SHIPPED! " + clip_id)
