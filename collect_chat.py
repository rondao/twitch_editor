import argparse
import json
import requests
import time
import sys


def collect_chat(video_id: int) -> list[dict[str, object]]:
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download chat from a Twitch video.')
    parser.add_argument('video_id', type=int, help='Twitch video ID to download chat from.')

    args = parser.parse_args()
    print(json.dumps(collect_chat(args.video_id)))