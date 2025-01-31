#!/usr/bin/env python
# coding: UTF-8

from __future__ import print_function
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D
from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.datasets import imdb

def create_ngram_set(input_list, ngram_value=2):
	"""
	Extract a set of n-grams from a list of integers.
	>>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=2)
	{(4, 9), (4, 1), (1, 4), (9, 4)}
	>>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=3)
	[(1, 4, 9), (4, 9, 4), (9, 4, 1), (4, 1, 4)]
	"""
	return set(zip(*[input_list[i:] for i in range(ngram_value)]))

def add_ngram(sequences, token_indice, ngram_range=2):
	"""
	Augment the input list of list (sequences) by appending n-grams values.
	Example: adding bi-gram
	>>> sequences = [[1, 3, 4, 5], [1, 3, 7, 9, 2]]
	>>> token_indice = {(1, 3): 1337, (9, 2): 42, (4, 5): 2017}
	>>> add_ngram(sequences, token_indice, ngram_range=2)
	[[1, 3, 4, 5, 1337, 2017], [1, 3, 7, 9, 2, 1337, 42]]
	Example: adding tri-gram
	>>> sequences = [[1, 3, 4, 5], [1, 3, 7, 9, 2]]
	>>> token_indice = {(1, 3): 1337, (9, 2): 42, (4, 5): 2017, (7, 9, 2): 2018}
	>>> add_ngram(sequences, token_indice, ngram_range=3)
	[[1, 3, 4, 5, 1337, 2017], [1, 3, 7, 9, 2, 1337, 42, 2018]]
	"""
	new_sequences = []
	for input_list in sequences:
		new_list = input_list[:]
		for ngram_value in range(2, ngram_range + 1):
			for i in range(len(new_list) - ngram_value + 1):
				ngram = tuple(new_list[i:i + ngram_value])
				if ngram in token_indice:
					new_list.append(token_indice[ngram])
		new_sequences.append(new_list)

	return new_sequences

# REF [site] >>
#	https://github.com/keras-team/keras/blob/master/examples/imdb_fasttext.py
#	https://github.com/keras-team/keras/blob/master/examples/imdb_fasttext.py
# REF [paper] >>
#	"Bag of Tricks for Efficient Text Classification", arXiv 2016.
#	"FastText.zip: Compressing text classification models", ICLR 2017.
def fasttext_imdb_example():
	# Set parameters:
	# ngram_range = 2 will add bi-grams features.
	ngram_range = 1
	max_features = 20000
	maxlen = 400
	batch_size = 32
	embedding_dims = 50
	epochs = 5

	print('Loading data...')
	(x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=max_features)
	print(len(x_train), 'train sequences')
	print(len(x_test), 'test sequences')
	print('Average train sequence length: {}'.format(np.mean(list(map(len, x_train)), dtype=int)))
	print('Average test sequence length: {}'.format(np.mean(list(map(len, x_test)), dtype=int)))

	if ngram_range > 1:
		print('Adding {}-gram features'.format(ngram_range))
		# Create set of unique n-gram from the training set.
		ngram_set = set()
		for input_list in x_train:
			for i in range(2, ngram_range + 1):
				set_of_ngram = create_ngram_set(input_list, ngram_value=i)
				ngram_set.update(set_of_ngram)

		# Dictionary mapping n-gram token to a unique integer.
		# Integer values are greater than max_features in order to avoid collision with existing features.
		start_index = max_features + 1
		token_indice = {v: k + start_index for k, v in enumerate(ngram_set)}
		indice_token = {token_indice[k]: k for k in token_indice}

		# max_features is the highest integer that could be found in the dataset.
		max_features = np.max(list(indice_token.keys())) + 1

		# Augmenting x_train and x_test with n-grams features.
		x_train = add_ngram(x_train, token_indice, ngram_range)
		x_test = add_ngram(x_test, token_indice, ngram_range)
		print('Average train sequence length: {}'.format(np.mean(list(map(len, x_train)), dtype=int)))
		print('Average test sequence length: {}'.format(np.mean(list(map(len, x_test)), dtype=int)))

	print('Pad sequences (samples x time)')
	x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
	x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
	print('x_train shape:', x_train.shape)
	print('x_test shape:', x_test.shape)

	print('Build model...')
	model = Sequential()
	# We start off with an efficient embedding layer which maps our vocab indices into embedding_dims dimensions.
	model.add(Embedding(max_features, embedding_dims, input_length=maxlen))
	# We add a GlobalAveragePooling1D, which will average the embeddings of all words in the document.
	model.add(GlobalAveragePooling1D())
	# We project onto a single unit output layer, and squash it with a sigmoid:
	model.add(Dense(1, activation='sigmoid'))

	model.compile(loss='binary_crossentropy',
				  optimizer='adam',
				  metrics=['accuracy'])

	print('Train model...')
	model.fit(x_train, y_train,
			  batch_size=batch_size,
			  epochs=epochs,
			  validation_data=(x_test, y_test))

def main():
	fasttext_imdb_example()

#--------------------------------------------------------------------

if '__main__' == __name__:
	main()
