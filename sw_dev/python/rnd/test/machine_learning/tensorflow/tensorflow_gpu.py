#!/usr/bin/env python

# REF [site] >> https://www.tensorflow.org/tutorials/using_gpu

import tensorflow as tf

def log_device_placement():
	# To find out which devices your operations and tensors are assigned to, create the session with log_device_placement configuration option set to True.

	# Creates a graph.
	a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
	b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
	c = tf.matmul(a, b)

	# Creates a session with log_device_placement set to True.
	sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

	# Runs the op.
	print(sess.run(c))

def manual_device_placement_1():
	# Creates a graph.
	with tf.device('/device:CPU:0'):
	#with tf.device('/device:GPU:0'):
		a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
		b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
		c = tf.matmul(a, b)

	# Creates a session with log_device_placement set to True.
	sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

	# Runs the op.
	print(sess.run(c))

def manual_device_placement_2():
	graph = tf.Graph()

	# Creates a graph.
	with graph.as_default():
		with tf.device('/device:GPU:1'):
			a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
			b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
			c = tf.matmul(a, b)

	# Creates a session with log_device_placement set to True.
	sess = tf.Session(graph=graph, config=tf.ConfigProto(log_device_placement=True))

	# Runs the op.
	print(sess.run(c))

def allow_gpu_memory_growth():
	# Attempt to allocate only as much GPU memory based on runtime allocations:
	# it starts out allocating very little memory, and as Sessions get run and more GPU memory is needed, we extend the GPU memory region needed by the TensorFlow process.
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True
	#session = tf.Session(config=config, ...)

	# Bound the amount of GPU memory available to the TensorFlow process.
	config = tf.ConfigProto()
	config.gpu_options.per_process_gpu_memory_fraction = 0.4
	#session = tf.Session(config=config, ...)

def use_a_single_gpu_on_a_multi_gpu_system():
	# If the device you have specified does not exist, you will get InvalidArgumentError.

	# Creates a graph.
	with tf.device('/gpu:2'):
		a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
		b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
		c = tf.matmul(a, b)

	# Creates a session with log_device_placement set to True.
	sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

	# Runs the op.
	print(sess.run(c))

	# If you would like TensorFlow to automatically choose an existing and supported device to run the operations in case the specified one doesn't exist, 
	# set allow_soft_placement to True in the configuration option when creating the session.

	# Creates a graph.
	with tf.device('/gpu:2'):
		a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
		b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
		c = tf.matmul(a, b)

	# Creates a session with allow_soft_placement and log_device_placement set to True.
	sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True, log_device_placement=True))

	# Runs the op.
	print(sess.run(c))

def use_multiple_gpus():
	# Creates a graph.
	c = []
	for d in ['/gpu:2', '/gpu:3']:
		with tf.device(d):
			a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3])
			b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2])
			c.append(tf.matmul(a, b))
	with tf.device('/cpu:0'):
		sum = tf.add_n(c)

	# Creates a session with log_device_placement set to True.
	sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))

	# Runs the op.
	print(sess.run(sum))

def main():
	log_device_placement()
	manual_device_placement_1()
	manual_device_placement_2()

	allow_gpu_memory_growth()
	use_a_single_gpu_on_a_multi_gpu_system()
	use_multiple_gpus()

#--------------------------------------------------------------------

if '__main__' == __name__:
	main()
