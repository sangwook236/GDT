#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json

def main():
	# File.
	try:
		filepath = 'test.json'
		with open(filepath, encoding='UTF8') as fd:
			json_data = json.load(fd)
			print(json_data)
	except UnicodeDecodeError as ex:
		print('Unicode decode error in {}: {}.'.format(filepath, ex))
	except FileNotFoundError as ex:
		print('File not found, {}: {}.'.format(filepath, ex))

	try:
		filepath = 'tmp.json'
		with open(filepath, 'w+', encoding='UTF8') as fd:
			json.dump(json_data, fd, indent='\t')
	except UnicodeDecodeError as ex:
		print('Unicode decode error in {}: {}.'.format(filepath, ex))
	except FileNotFoundError as ex:
		print('File not found, {}: {}.'.format(filepath, ex))

	#--------------------
	# String.
	sz = json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
	print(type(sz), sz)

	lst = json.loads('["foo", {"bar":["baz", null, 1.0, 2]}]')
	print(type(lst), lst)

#--------------------------------------------------------------------

if '__main__' == __name__:
	main()