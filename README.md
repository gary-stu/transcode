# Transcode

## Installation

- First install ffmpeg, and ensure ffmpeg is on your PATH: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- Second, install the requirements
```bash
pip3 install -r requirements.txt
```
Note: Windows users will probably use `pip` instead of `pip3`
- You're ready to roll

## Use

- Well, check `./transcode.py --help`


## Examples 
- Absolute braindead execution would be to move the files you want to transcode to this folder, and then running it
```bash
cp /path/to/my/file.mkv .
./transcode.py
```

- More advanced uses would be to check the file and pass it directly the streams to use
```bash
cp /path/to/my/file.mkv .
./transcode.py -pr file.mkv
{You see that you need to use audio stream 1 and subtitle stream 4}
./transcode.py -as 1 -ss 4
```