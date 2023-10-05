#!/usr/bin/python3
"""
Encode videos for my PS4/DLNA server
"""

from argparse import ArgumentParser, Namespace
from os import listdir, mkdir, remove
from pathlib import Path
from pprint import pprint
from subprocess import run

from ffmpeg import probe


video_filetypes = ['mkv', 'mp4', 'avi']


def ffprobe(args: Namespace):
    """
    TODO
    :param args:
    :return:
    """
    filepath = Path(args.probe)
    file = probe(filepath)

    video_streams = []
    audio_streams = []
    subtitle_streams = []

    for stream in file['streams']:
        if stream['codec_type'] == 'video':
            video_streams.append(stream)
        if stream['codec_type'] == 'audio':
            audio_streams.append(stream)
        if stream['codec_type'] == 'subtitle':
            subtitle_streams.append(stream)

    i = 0
    for stream in video_streams:
        print(f'video stream {i}')
        pprint(stream)
        print('')
        i += 1
    print('-------------')

    i = 0
    for stream in audio_streams:
        print(f'audio stream {i}')
        pprint(stream)
        print('')
        i += 1
    print('-------------')

    i = 0
    for stream in subtitle_streams:
        print(f'subtitle stream {i}')
        pprint(stream)
        print('')
        i += 1


def cmd(command: list):
    """
    TODO
    :param command:
    """
    command_text = ' '.join(f for f in command)
    print(command_text)
    run(command_text)


def main(args: Namespace):
    """
    TODO
    :param args:
    :return:
    """
    # Probe the files if requested
    if args.probe != '':
        ffprobe(args)
        exit(0)

    # Loop on all the video files in folder to encode them in H264 yuv420p format
    for file in listdir(args.folder):

        # only work on videos, and not text files, audio files or pictures
        file_split = file.split('.')
        if file_split[-1] in video_filetypes:
            filepath = Path(args.folder, file)

            # Probe the video to get the correct data to work with
            audio_stream_number = 0
            subtitle_stream_number = 0
            audio_index = None
            subtitle_index = None
            probed_file = probe(filepath)

            for stream in probed_file['streams']:
                if stream['codec_type'] == 'audio':
                    # try to autodetect the audio stream using the args.audio_language language
                    try:
                        if stream['tags']['language'] == args.audio_language:
                            print('audio stream detected')
                            audio_index = audio_stream_number
                    except KeyError:
                        pass

                    audio_stream_number += 1

                if stream['codec_type'] == 'subtitle':
                    # try to autodetect the subtitle stream using the args.subtitle_language language
                    try:
                        if stream['tags']['language'] == args.subtitle_language:
                            print('subtitle stream detected')
                            subtitle_index = subtitle_stream_number
                    except KeyError:
                        pass

                    subtitle_stream_number += 1

            # If there is a single subtitle stream, use it
            if subtitle_stream_number == 1:
                subtitle_index = 0

            # If there is a single audio stream, use it
            if audio_stream_number == 1:
                audio_index = 0

            # Force use streams (both audio and subtitle) if they were forced with command arguments
            if args.subtitle_stream != '':
                subtitle_index = int(args.subtitle_stream)

            if args.audio_stream != '':
                audio_index = int(args.audio_stream)

            # Check that an audio stream has been selected by previous code
            assert audio_index is not None

            # Check that a sub stream has been selected by previous code
            # (unless specified through command argument that none were required)
            if not args.no_subs:
                assert subtitle_index is not None

            # Set encoding speed preset
            # If dry run, set it to ultrafast
            preset = args.preset
            if args.dry_run:
                preset = 'ultrafast'

            # create a folder for the newly encoded videos
            new_folder = Path(args.folder, 'transcoded')
            try:
                mkdir(new_folder)
            except FileExistsError:
                pass

            # Create the ffmpeg command to encode the video
            ffmpeg_command = [
                'ffmpeg',
                '-i', f'"{filepath}"',
                '-map', '0:v:0',
                '-map', f'0:a:{audio_index}',
                '-map', '0:t',
                '-vcodec', 'libx264', '-profile:v', 'high', '-preset', preset,
                '-pix_fmt', 'yuv420p',
                '-acodec', 'libmp3lame',
            ]

            # hardcode subtitles onto the video if needed
            if not args.no_subs:
                # # normal subtitles

                if not args.subtitle_video:
                    if not args.extract:
                        # Source the subs directly from the video
                        special_windows_path = str(Path(args.folder))
                        special_windows_path += '/' + file
                        # creating a special string, else would not be understood in windows
                        ffmpeg_command += [
                            '-vf', f'"subtitles=\'{special_windows_path}\':stream_index={subtitle_index}"'
                        ]

                    else:
                        # First extract the subs in a "out.ass" file, then get the subs from this ass file
                        ffmpeg_command += [
                            '-vf', '"ass=./out.ass"'
                        ]
                        extract_command = [
                            'ffmpeg',
                            '-i', f'"{filepath}"',
                            '-map', f'0:s:{subtitle_index}',
                            'out.ass', '-y'
                        ]
                        cmd(extract_command)

                # picture based subtitles
                else:
                    if args.non_video_subtitle:
                        pass
                    ffmpeg_command += [
                        '-filter_complex', f'"[0:v][0:s:{subtitle_index}]overlay=shortest=1[v]"',
                    ]
                    ffmpeg_command[4] = '"[v]"'

            new_filename = '.'.join(part for part in file_split[:-1]) + '.mkv'
            new_filepath = Path(new_folder, new_filename)

            ffmpeg_command += [f'"{new_filepath}"', '-y']
            cmd(ffmpeg_command)

            # Delete the generated subs if some were generated
            try:
                remove('out.ass')
            except FileNotFoundError:
                pass

            # exit if it was a dry run, no need to encode the rest
            if args.dry_run:
                exit(0)


if __name__ == '__main__':
    argparser = ArgumentParser(
        description='Transcoder for PS4. '
                    'Will transcode every file in a folder to files with a single H264 video stream, '
                    'single libmp3lame audio stream and hardcoded subs (if applicable)'
    )

    argparser.add_argument(
        '-pr', '--probe',
        help='Probe a single file with ffprobe.',
        dest='probe',
        action='store',
        default='',
    )

    argparser.add_argument(
        '-a', '--audio-language',
        help='Define which audio language to transcode if multiple audio are present. Defaults to jpn',
        dest='audio_language',
        action='store',
        default='jpn'
    )

    argparser.add_argument(
        '-s', '--subtitle-language',
        help='Define which subtitle language to transcode if multiple audio are present. Defaults to fre',
        dest='subtitle_language',
        action='store',
        default='fre'
    )

    argparser.add_argument(
        '-as', '--audio-stream',
        help='Force a specific audio stream',
        dest='audio_stream',
        action='store',
        default=''
    )

    argparser.add_argument(
        '-ss', '--subtitle-stream',
        help='Force a specific subtitle stream',
        dest='subtitle_stream',
        action='store',
        default=''
    )

    argparser.add_argument(
        '-ns', '--no-subtitles',
        help='Do not hardcode any subtitles in the video (no subtitles will be present in output)',
        dest='no_subs',
        action='store_true'
    )

    argparser.add_argument(
        '-f', '--folder',
        help='The folder on which to run the script. Defaults to current folder "."',
        dest='folder',
        action='store',
        default='.'
    )

    argparser.add_argument(
        '-p', '--preset',
        help='The ffmpeg preset to use for h264. Defaults to medium',
        dest='preset',
        action='store',
        choices=[
            'ultrafast',
            'superfast',
            'veryfast',
            'faster',
            'fast',
            'medium',
            'slow',
            'slower',
            'veryslow',
            'placebo'
        ],
        default='medium'
    )

    argparser.add_argument(
        '-sv', '--subtitle-videotype',
        help='Enter this option if the subtitle type is video type (like dvd subs)',
        dest='subtitle_video',
        action='store_true',
    )

    argparser.add_argument(
        '-e', '--extract-subs',
        help='Add an additional step that extract text based subs to ass format before adding them again',
        dest='extract',
        action='store_true'
    )

    argparser.add_argument(
        '-d', '--dry-run',
        help='Test the output by creating a single output with an ultrafast preset, so you can see what it does',
        dest='dry_run',
        action='store_true'
    )

    args = argparser.parse_args()
    main(args)
