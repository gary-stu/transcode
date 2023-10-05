from argparse import ArgumentParser, Namespace
from os import listdir, rename
from pathlib import Path


def main(args: Namespace):
	"""
	TODO
	:param args:
	:return:
	"""
	if args.ext.startswith('.'):
		args.ext = args.ext[1:]

	for f in listdir(args.dir):
		if f.endswith(args.ext):
			# Search for 2 numbers in a row
			pos = 0
			i = 0
			while i < len(f) - 2:
				# Ignore the "S01" from a "S01E01" format
				if f[i] == 'S' and f[i+1].isdigit() and f[i+2].isdigit():
					i+= 2

				if f[i].isdigit() and f[i+1].isdigit():
					pos = i
					break
				i += 1

			number = f[pos: pos+2]
			new_name = f'{args.name} - {number}.{args.ext}'

			if args.rename:
				old_file = Path(args.dir, f)
				new_file = Path(args.dir, new_name)
				print(f'"{f}" -> "{new_name}"')
				rename(old_file, new_file)

			else:
				print(f'old: {f}')
				print(f'new: {new_name}')
				print('')


if __name__ == '__main__':
	parser = ArgumentParser()

	parser.add_argument(
		'-n', '--name',
		help='The name of the series',
		dest='name',
		action='store',
		required=True
	)

	parser.add_argument(
		'-r', '--rename',
		help='Rename the files. If not included in command, will only print expected result',
		dest='rename',
		action='store_true'
	)

	parser.add_argument(
		'-e', '--extension',
		help='Script will run on all the files with given extension on the folder. Defaults to mkv',
		dest='ext',
		action='store',
		default='mkv'
	)

	parser.add_argument(
		'-d', '--dir',
		help='dir on which to run the script. Defaults to "."',
		dest='dir',
		action='store',
		default='.'
	)

	args = parser.parse_args()
	main(args)
