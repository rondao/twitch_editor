import argparse
import json
import requests
import time
import socket
import sys
from collections.abc import Callable, Iterator


def collect_chat_from_channel(channel: str, oauth_token: str, nickname: str) -> Callable[[], Iterator[str]]:
    sock = socket.socket()
    sock.connect(('irc.chat.twitch.tv', 6667))
    sock.send(f"PASS oauth:{oauth_token}\n".encode('utf-8'))
    sock.send(f"NICK {nickname}\n".encode('utf-8'))
    sock.send(f"JOIN #{channel}\n".encode('utf-8'))

    def read_message() -> Iterator[str]:
        while True:
            resp = sock.recv(2048).decode('utf-8')

            if resp.startswith('PING'):
                sock.send("PONG\n".encode('utf-8'))

            yield resp

    return read_message


def collect_chat_from_vod(video_id: int) -> list[dict[str, object]]:
    url = f"https://api.twitch.tv/v5/videos/{video_id}/comments?cursor="
    response_json = requests.get(url, headers={"Client-ID": "hdaoisxhhrc9h3lz3k24iao13crkkq8",
                                               "Accept": "application/vnd.twitchtv.v5+json"}).json()

    comments = response_json["comments"]
    while "_next" in response_json:
        print(comments[-1]["content_offset_seconds"], file=sys.stderr)
        time.sleep(0.5)
        response_json = requests.get(url + response_json["_next"],
                                     headers={"Client-ID": "hdaoisxhhrc9h3lz3k24iao13crkkq8",
                                              "Accept": "application/vnd.twitchtv.v5+json"}).json()
        comments += response_json["comments"]

    return comments


def _collect_chat_from_vod(args: argparse.Namespace) -> None:
    print(json.dumps(collect_chat_from_vod(args.video_id)))


def _collect_chat_from_channel(args: argparse.Namespace) -> None:
    channel = collect_chat_from_channel(
        args.channel, args.oauth_token, args.nickname)
    for msg in channel():
        print(msg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Download chat from Twitch.')
    subcommands = parser.add_subparsers()

    vod_command = subcommands.add_parser(
        'vod', help='Collect chat from a vod.')
    vod_command.add_argument('video_id', type=int,
                             help='Twitch video ID to download chat from.')
    vod_command.set_defaults(func=_collect_chat_from_vod)

    channel_command = subcommands.add_parser(
        'channel', help='Collect chat from a live channel.')
    channel_command.add_argument('channel', type=str,
                                 help='Twitch channel ID to download chat from.')
    channel_command.add_argument('oauth_token', type=str,
                                 help='Twitch OAUTH token with "chat:read" and "chat:edit" scope permissions.')
    channel_command.add_argument('nickname', type=str,
                                 help='Twitch nickname associated with the OAUTH token.')
    channel_command.set_defaults(func=_collect_chat_from_channel)

    args = parser.parse_args()
    args.func(args)
