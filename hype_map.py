import argparse
import json

from datetime import timedelta
from statistics import mean

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate hype map.')
    parser.add_argument('file', type=str, help='File containing list of comments from a Twitch VOD.')

    args = parser.parse_args()

    with open(args.file) as comments_file:
        comments = json.load(comments_file)

    laughs_moments: list[float] = []
    for comment in comments:
        message_content = comment["message"]["body"].casefold()
        if "lul" in message_content or "kek" in message_content:
            laughs_moments.append(comment["content_offset_seconds"])

    i = 0
    while i <= len(laughs_moments) - 10:
        if abs(laughs_moments[i] - mean(laughs_moments[i:i+10])) < 4:
            print(str(timedelta(seconds=laughs_moments[i])))
            i += 20
        i += 1