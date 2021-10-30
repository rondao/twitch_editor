import argparse
import subprocess


def clipping_commands_from_file(edit_filename: str) -> list[str]:
    clipping_commands: list[str] = []
    with open(edit_filename) as edit_file:
        video_file: str
        while (line := edit_file.readline().rstrip()):
            command, arg = line.split(" ", 1)
            match command:
                case "f":
                    video_file = arg
                case "c":
                    start_time, duration = arg.split(" ", 1)
                    clipping_commands.append(
                        f"ffmpeg -y -ss {start_time} -i {video_file} -t {duration} -f rawvideo -vcodec rawvideo clip{len(clipping_commands)}.raw")
    return clipping_commands


def collect_clips_duration(clips_filename: list[str]) -> list[tuple[str, float]]:
    ffprobe = ['ffprobe', '-show_entries', 'format=duration',
               '-v', 'quiet', '-of', 'default=noprint_wrappers=1:nokey=1']
    return [(filename, float(subprocess.run(ffprobe + [filename], stdout=subprocess.PIPE).stdout)) for filename in clips_filename]


def create_composition(edit_filename: str, transition_duration: int = 1) -> str:
    inputs: list[list[str]] = []
    filter_complex: str = ""
    with open(edit_filename) as edit_file:
        video_file: str
        while (line := edit_file.readline().rstrip()):
            command, arg = line.split(" ", 1)
            match command:
                case "f":
                    video_file = arg
                case "c":
                    if not video_file:
                        raise Exception(
                            "Clip command [c " + arg + "] don't have a reference video file.")
                    start_time, end_time = arg.split(" ", 1)

                    inputs.append(["-ss", start_time, "-to",
                                  end_time, "-i", video_file])

                    start_seconds = _time_to_sec(start_time)
                    end_seconds = _time_to_sec(end_time)

                    input = len(inputs) - 1
                    filter_complex += f"[{input}:v] trim=end={end_seconds - start_seconds - transition_duration},setpts=PTS-STARTPTS [begin_v{input}];"
                    filter_complex += f"[{input}:v] trim=start={end_seconds - start_seconds - transition_duration},setpts=PTS-STARTPTS [end_v{input}];"
                    filter_complex += f"[{input}:a] atrim=end={end_seconds - start_seconds - transition_duration},asetpts=PTS-STARTPTS [begin_a{input}];"
                    filter_complex += f"[{input}:a] atrim=start={end_seconds - start_seconds - transition_duration},asetpts=PTS-STARTPTS [end_a{input}];"

    for i in range(0, len(inputs) - 1):
        filter_complex += f"[end_v{i}] [begin_v{i + 1}] xfade=transition=fadewhite:duration={transition_duration} [t{i}_v{i+1}];"
        filter_complex += f"[end_a{i}] [begin_a{i + 1}] acrossfade=duration={transition_duration} [t{i}_a{i+1}];"

    filter_complex += "[begin_v0][begin_a0]" + "".join(
        [f"[t{i}_v{i+1}][t{i}_a{i+1}]" for i in range(0, len(inputs) - 1)]) + f"[end_v{len(inputs) - 1}][end_a{len(inputs) - 1}]"
    filter_complex += f"concat=n={len(inputs) + 1}:v=1:a=1 [outv][outa]"

    ffmpeg = ["ffmpeg"]
    for input in inputs:
        ffmpeg.extend(input)

    ffmpeg.extend(["-filter_complex", filter_complex])

    output = "output.mp4"
    ffmpeg.extend(["-map", "[outv]", "-map", "[outa]", "-y", output])

    # print(ffmpeg)
    subprocess.run(ffmpeg)
    return output


def _time_to_sec(time_str: str) -> int:
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compose clips extracted from videos.')
    parser.add_argument('edit_filename', type=str,
                        help='File with instructions to clip and compose.')

    args = parser.parse_args()
    print(create_composition(args.edit_filename))

    # clipping_commands = clipping_commands_from_file(args.edit_filename)
    # for cmd in clipping_commands:
    #     subprocess.run(cmd.split())

    # print(compose_clips([f"clip{i}.raw"
    #       for i in range(len(clipping_commands))]))