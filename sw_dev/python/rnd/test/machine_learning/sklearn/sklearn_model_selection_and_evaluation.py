#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
import numpy as np
import pandas as pd
import scipy.stats
from sklearn import model_selection
from sklearn import metrics, pipeline, preprocessing, utils
from sklearn import datasets
from sklearn import linear_model, svm, naive_bayes, ensemble
import matplotlib.pyplot as plt

# REF [site] >>
#	http://scikit-learn.org/stable/model_selection.html
#	http://scikit-learn.org/stable/auto_examples/classification/plot_classifier_comparison.html

def plot_learning_curve(estimator, title, X, y, ylim=None, cv=None, n_jobs=1, train_sizes=np.linspace(.1, 1.0, 5)):
	"""
	Generate a simple plot of the test and training learning curve.

	Parameters
	----------
	estimator : object type that implements the "fit" and "predict" methods.
		An object of that type which is cloned for each validation.

	title : string
		Title for the chart.

	X : array-like, shape (n_samples, n_features)
		Training vector, where n_samples is the number of samples and
		n_features is the number of features.

	y : array-like, shape (n_samples) or (n_samples, n_features), optional
		Target relative to X for classification or regression;
		None for unsupervised learning.

	ylim : tuple, shape (ymin, ymax), optional
		Defines minimum and maximum yvalues plotted.

	cv : int, cross-validation generator or an iterable, optional
		Determines the cross-validation splitting strategy.
		Possible inputs for cv are:
			- None, to use the default 3-fold cross-validation,
			- integer, to specify the number of folds.
			- An object to be used as a cross-validation generator.
			- An iterable yielding train/test splits.

		For integer/None inputs, if ``y`` is binary or multiclass,
		:class:`StratifiedKFold` used. If the estimator is not a classifier
		or if ``y`` is neither binary nor multiclass, :class:`KFold` is used.

		Refer :ref:`User Guide <cross_validation>` for the various
		cross-validators that can be used here.

	n_jobs : integer, optional
		Number of jobs to run in parallel (default 1).
	"""
	plt.figure()
	plt.title(title)
	if ylim is not None:
		plt.ylim(*ylim)
	plt.xlabel('Training examples')
	plt.ylabel('Score')
	train_sizes, train_scores, test_scores = model_selection.learning_curve(estimator, X, y, cv=cv, n_jobs=n_jobs, train_sizes=train_sizes)
	train_scores_mean = np.mean(train_scores, axis=1)
	train_scores_std = np.std(train_scores, axis=1)
	test_scores_mean = np.mean(test_scores, axis=1)
	test_scores_std = np.std(test_scores, axis=1)
	plt.grid()

	plt.fill_between(train_sizes, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std, alpha=0.1, color='r')
	plt.fill_between(train_sizes, test_scores_mean - test_scores_std, test_scores_mean + test_scores_std, alpha=0.1, color='g')
	plt.plot(train_sizes, train_scores_mean, 'o-', color='r', label='Training score')
	plt.plot(train_sizes, test_scores_mean, 'o-', color='g', label='Cross-validation score')

	plt.legend(loc='best')
	return plt

def learning_curve_example_1():
	# REF [site] >> http://scikit-learn.org/stable/auto_examples/model_selection/plot_learning_curve.html
	digits = datasets.load_digits()
	X, y = digits.data, digits.target

	title = 'Learning Curves (Naive Bayes)'
	# Cross validation with 100 iterations to get smoother mean test and train score curves, each time with 20% data randomly selected as a validation set.
	cv = model_selection.ShuffleSplit(n_splits=100, test_size=0.2, random_state=0)

	estimator = naive_bayes.GaussianNB()
	plot_learning_curve(estimator, title, X, y, ylim=(0.7, 1.01), cv=cv, n_jobs=4)

	title = 'Learning Curves (SVM, RBF kernel, $\gamma=0.001$)'
	# SVC is more expensive so we do a lower number of CV iterations:
	cv = model_selection.ShuffleSplit(n_splits=10, test_size=0.2, random_state=0)
	estimator = svm.SVC(gamma=0.001)
	plot_learning_curve(estimator, title, X, y, (0.7, 1.01), cv=cv, n_jobs=4)

	plt.show()

	# REF [site] >> http://scikit-learn.org/stable/auto_examples/model_selection/plot_validation_curve.html
	digits = datasets.load_digits()
	X, y = digits.data, digits.target

	param_range = np.logspace(-6, -1, 5)
	train_scores, test_scores = model_selection.validation_curve(svm.SVC(), X, y, param_name='gamma', param_range=param_range, cv=10, scoring='accuracy', n_jobs=1)
	train_scores_mean = np.mean(train_scores, axis=1)
	train_scores_std = np.std(train_scores, axis=1)
	test_scores_mean = np.mean(test_scores, axis=1)
	test_scores_std = np.std(test_scores, axis=1)

	plt.title('Validation Curve with SVM')
	plt.xlabel('$\gamma$')
	plt.ylabel('Score')
	plt.ylim(0.0, 1.1)
	lw = 2
	plt.semilogx(param_range, train_scores_mean, label='Training score', color='darkorange', lw=lw)
	plt.fill_between(param_range, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std, alpha=0.2, color='darkorange', lw=lw)
	plt.semilogx(param_range, test_scores_mean, label='Cross-validation score', color='navy', lw=lw)
	plt.fill_between(param_range, test_scores_mean - test_scores_std, test_scores_mean + test_scores_std, alpha=0.2, color='navy', lw=lw)
	plt.legend(loc='best')
	plt.show()

# REF [site] >> https://scikit-learn.org/stable/modules/learning_curve.html
def learning_curve_example_2():
	np.random.seed(0)

	X, y = datasets.load_iris(return_X_y=True)
	indices = np.arange(y.shape[0])
	np.random.shuffle(indices)
	X, y = X[indices], y[indices]

	#--------------------
	param_name = 'alpha'
	param_range = np.logspace(-7, 3, 3)  # [1e-5, 1e3].
	train_scores, valid_scores = model_selection.validation_curve(linear_model.Ridge(), X, y, param_name=param_name, param_range=param_range, cv=5)
	#train_scores, valid_scores = model_selection.validation_curve(estimator, X, y, param_name=param_name, param_range=param_range, groups=None, cv=None, scoring=None, n_jobs=None, pre_dispatch='all', verbose=0, error_score=np.nan, fit_params=None)

	print('Train scores:\n{}'.format(train_scores))
	print('Validation scores:\n{}'.format(valid_scores))

	train_scores_mean = train_scores.mean(axis=1)
	train_scores_std = train_scores.std(axis=1)
	valid_scores_mean = valid_scores.mean(axis=1)
	valid_scores_std = valid_scores.std(axis=1)

	plt.figure()
	#plt.plot(param_range, train_scores_mean, label='train', color='darkorange')
	plt.semilogx(param_range, train_scores_mean, label='train', color='darkorange')
	plt.fill_between(param_range, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std, alpha=0.2, color='darkorange')
	#plt.plot(param_range, valid_scores_mean, label='valid', color='navy')
	plt.semilogx(param_range, valid_scores_mean, label='valid', color='navy')
	plt.fill_between(param_range, valid_scores_mean - valid_scores_std, valid_scores_mean + valid_scores_std, alpha=0.2, color='navy')
	plt.xlabel(param_name)
	plt.ylabel('Score')
	plt.title('Validation curves')
	plt.legend(loc='best')

	#--------------------
	train_sizes_abs, train_scores, valid_scores = model_selection.learning_curve(svm.SVC(kernel='linear'), X, y, train_sizes=[50, 80, 110], cv=5)
	#train_sizes_abs, train_scores, valid_scores = model_selection.learning_curve(estimator, X, y, groups=None, train_sizes=np.linspace(0.1, 1.0, 5), cv=None, scoring=None, exploit_incremental_learning=False, n_jobs=None, pre_dispatch='all', verbose=0, shuffle=False, random_state=None, error_score=nan, return_times=False, fit_params=None)
	
	print('Train sizes = {}.'.format(train_sizes_abs))
	print('Train scores:\n{}'.format(train_scores))
	print('Validation scores:\n{}'.format(valid_scores))

	plt.figure()
	plt.plot(train_sizes_abs, train_scores.mean(axis=1), label='train')
	plt.plot(train_sizes_abs, valid_scores.mean(axis=1), label='valid')
	plt.xlabel('Train size')
	plt.ylabel('Score')
	plt.title('Learning curves')
	plt.legend(loc='best')

	plt.show()

def train_test_split_example():
	iris = datasets.load_iris()
	X_train, X_test, y_train, y_test = model_selection.train_test_split(iris.data, iris.target, test_size=0.4, shuffle=True, stratify=None, random_state=0)
	# If variable y is a binary categorical variable with values 0 and  1 and there are 25% of zeros and 75% of ones, stratify=y will make sure that your random split has 25% of 0's and 75% of 1's.
	#X_train, X_test, y_train, y_test = model_selection.train_test_split(iris.data, iris.target, test_size=0.4, shuffle=True, stratify=iris.target, random_state=0)

	print(X_train.shape, y_train.shape)
	print(X_test.shape, y_test.shape)

	clf = svm.SVC(kernel='linear', C=1).fit(X_train, y_train)
	scores = clf.score(X_test, y_test)   
	print('Scores =', scores)

def split_example():
	X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
	y = np.array([1, 2, 1, 2])
	groups = np.array([0, 0, 2, 2])

	if False:
		# The entry test_fold[i] represents the index of the test set that sample i belongs to.
		# It is possible to exclude sample i from any test set (i.e. include sample i in every training set) by setting test_fold[i] equal to -1.
		test_fold = [0, 1, -1, 1]
		split = PredefinedSplit(test_fold)
		print('#splits =', split.get_n_splits(X, y))
	elif False:
		# The stratified folds are made by preserving the percentage of samples for each class.
		split = model_selection.StratifiedShuffleSplit(n_splits=3, test_size=0.25, random_state=None)
		print('#splits =', split.get_n_splits(X, y))
	elif False:
		# The same group will not appear in two different folds.
		# The number of distinct groups has to be at least equal to the number of folds.
		split = model_selection.GroupShuffleSplit(n_splits=3, test_size=0.25, random_state=None)
		#print('#splits =', split.get_n_splits(X, y, groups))
		print('#splits =', split.get_n_splits(groups=groups))
	elif False:
		split = model_selection.TimeSeriesSplit(n_splits=3, max_train_size=None)
		print('#splits =', split.get_n_splits())
	else:
		split = model_selection.ShuffleSplit(n_splits=3, test_size=0.25, random_state=None)
		print('#splits =', split.get_n_splits(X))
	print('Split:', split)

	#for train_indices, test_indices in split.split():
	#for train_indices, test_indices in split.split(X, y):
	#for train_indices, test_indices in split.split(X, y, groups):
	for train_indices, test_indices in split.split(X):
		#print('TRAIN:', train_indices.shape, 'TEST:', test_indices.shape)
		print('TRAIN:', train_indices, 'TEST:', test_indices)

		X_train, X_test = X[train_indices], X[test_indices]
		y_train, y_test = y[train_indices], y[test_indices]
		#print('TRAIN:\n', X_train, y_train)
		#print('TEST:\n', X_test, y_test)

def k_fold_example():
	X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
	y = np.array([1, 2, 1, 2])
	groups = np.array([0, 0, 2, 2])

	if False:
		# The stratified folds are made by preserving the percentage of samples for each class.
		kf = model_selection.StratifiedKFold(n_splits=4, shuffle=True, random_state=None)
		#kf = model_selection.RepeatedStratifiedKFold(n_splits=4, n_repeats=10, random_state=None)
		print('#splits =', kf.get_n_splits(X, y))
	elif False:
		# The same group will not appear in two different folds.
		# The number of distinct groups has to be at least equal to the number of folds.
		kf = model_selection.GroupKFold(n_splits=4)
		print('#splits =', kf.get_n_splits(X, y, groups))
	else:
		kf = model_selection.KFold(n_splits=4, shuffle=True, random_state=None)
		#kf = model_selection.RepeatedKFold(n_splits=5, n_repeats=10, random_state=None)
		print('#splits =', kf.get_n_splits(X))
	print('K-fold:', kf)

	#for train_indices, test_indices in kf.split(X, y):
	#for train_indices, test_indices in kf.split(X, y, groups):
	for train_indices, test_indices in kf.split(X):
		#print('TRAIN:', train_indices.shape, 'TEST:', test_indices.shape)
		print('TRAIN:', train_indices, 'TEST:', test_indices)

		X_train, X_test = X[train_indices], X[test_indices]
		y_train, y_test = y[train_indices], y[test_indices]
		#print('TRAIN:\n', X_train, y_train)
		#print('TEST:\n', X_test, y_test)

def leave_out_example():
	X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
	y = np.array([1, 2, 1, 2])
	groups = np.array([0, 0, 2, 2])

	if False:
		lo = model_selection.LeavePOut(p=2)
		print('#splits =', lo.get_n_splits(X))
	elif False:
		# The same group will not appear in two different folds.
		# The number of distinct groups has to be at least equal to the number of folds.
		lo = model_selection.LeaveOneGroupOut()
		#print('#splits =', lo.get_n_splits(X, y, groups))
		print('#splits =', lo.get_n_splits(groups=groups))
	elif False:
		# The same group will not appear in two different folds.
		# The number of distinct groups has to be at least equal to the number of folds.
		lo = model_selection.LeaveOneGroupOut(n_groups=2)
		#print('#splits =', lo.get_n_splits(X, y, groups))
		print('#splits =', lo.get_n_splits(groups=groups))
	else:
		lo = model_selection.LeaveOneOut()
		print('#splits =', lo.get_n_splits(X))
	print('Leave-out:', lo)

	#for train_indices, test_indices in lo.split(X, y, groups):
	for train_indices, test_indices in lo.split(X):
		#print('TRAIN:', train_indices.shape, 'TEST:', test_indices.shape)
		print('TRAIN:', train_indices, 'TEST:', test_indices)

		X_train, X_test = X[train_indices], X[test_indices]
		y_train, y_test = y[train_indices], y[test_indices]
		#print('TRAIN:\n', X_train, y_train)
		#print('TEST:\n', X_test, y_test)

# REF [site] >>
#	http://scikit-learn.org/stable/modules/cross_validation.html
#	http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.cross_validate.html
def cross_validation_example_1():
	#diabetes = datasets.load_diabetes()
	##X, y = diabetes.data[:150], diabetes.target[:150]
	#X, y = diabetes.data, diabetes.target
	iris = datasets.load_iris()
	X, y = iris.data, iris.target

	lasso = linear_model.Lasso()

	cv_results = model_selection.cross_validate(lasso, X, y, cv=4, return_train_score=False, n_jobs=-1)
	print('Keys =', sorted(cv_results.keys()))
	print('Test score =', cv_results['test_score'])

	scores = model_selection.cross_validate(lasso, X, y, cv=5, scoring=('r2', 'neg_mean_squared_error'), return_train_score=True, n_jobs=-1)
	print('Keys =', sorted(scores.keys()))
	print('Test score (negative mean squared error) =', scores['test_neg_mean_squared_error'])
	print('Test score (R2) =', scores['train_r2'])

	#-------------------
	#clf = svm.SVC(kernel='linear', C=1, probability=True)
	clf = ensemble.RandomForestClassifier(n_estimators=20)

	y_pred = model_selection.cross_val_predict(clf, X, y, cv=5, n_jobs=-1, method='predict')
	#y_pred = model_selection.cross_val_predict(clf, X, y, cv=5, n_jobs=-1, method='predict_proba')
	print('Prediction =', y_pred)
	scores = model_selection.cross_val_score(clf, X, y, cv=5, n_jobs=-1)
	print('Scores =', scores)
	print('Accuracy: %0.2f (+/- %0.2f)' % (scores.mean(), scores.std() * 2))

	y_pred = model_selection.cross_val_predict(clf, X, y, cv=4, n_jobs=-1, method='predict')
	print('Prediction =', y_pred)
	scores = model_selection.cross_val_score(clf, X, y, cv=4, n_jobs=-1, scoring='f1_macro')
	#scores = model_selection.cross_val_score(clf, X, y, cv=4, n_jobs=-1, scoring=('f1_macro', 'precision_micro'))  # Error.
	print('Scores =', scores)
	print('Accuracy: %0.2f (+/- %0.2f)' % (scores.mean(), scores.std() * 2))

	#-------------------
	cv = model_selection.ShuffleSplit(n_splits=3, test_size=0.3, random_state=0)
	scores = model_selection.cross_val_score(clf, X, y, cv=cv, n_jobs=-1)
	print('Scores =', scores)
	print('Accuracy: %0.2f (+/- %0.2f)' % (scores.mean(), scores.std() * 2))

# REF [site] >> https://scikit-learn.org/stable/modules/cross_validation.html
def cross_validation_example_2():
	X, y = datasets.load_iris(return_X_y=True)

	if True:
		clf = svm.SVC(kernel='linear', C=1, random_state=42)

		# When the cv argument is an integer, cross_val_score uses the KFold or StratifiedKFold strategies by default, the latter being used if the estimator derives from ClassifierMixin.
		# The score computed at each CV iteration is the score method of the estimator.
		scores = model_selection.cross_val_score(clf, X, y, cv=5)
		print('[1] CV scores = {} (mean = {}, stddev = {}).'.format(scores, scores.mean(), scores.std()))

		scores = model_selection.cross_val_score(clf, X, y, cv=5, scoring='f1_macro')
		print('[2] CV scores = {} (mean = {}, stddev = {}).'.format(scores, scores.mean(), scores.std()))

		# A cross validation iterator.
		cv = model_selection.ShuffleSplit(n_splits=5, test_size=0.3, random_state=0)
		scores = model_selection.cross_val_score(clf, X, y, cv=cv)
		print('[3] CV scores = {} (mean = {}, stddev = {}).'.format(scores, scores.mean(), scores.std()))

		# An iterable yielding (train, test) splits as arrays of indices.
		def custom_cv_2folds(X):
			n = X.shape[0]
			i = 1
			while i <= 2:
				idx = np.arange(n * (i - 1) / 2, n * i / 2, dtype=int)
				yield idx, idx
				i += 1

		custom_cv = custom_cv_2folds(X)
		scores = model_selection.cross_val_score(clf, X, y, cv=custom_cv)
		print('[4] CV scores = {} (mean = {}, stddev = {}).'.format(scores, scores.mean(), scores.std()))

		# A Pipeline makes it easier to compose estimators, providing this behavior under cross-validation.
		clf = pipeline.make_pipeline(preprocessing.StandardScaler(), svm.SVC(C=1))
		scores = model_selection.cross_val_score(clf, X, y, cv=cv)
		print('[5] CV scores = {} (mean = {}, stddev = {}).'.format(scores, scores.mean(), scores.std()))

	#--------------------
	if True:
		clf = svm.SVC(kernel='linear', C=1, random_state=0)

		scoring = ['precision_macro', 'recall_macro']
		#scoring = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro']
		scores = model_selection.cross_validate(clf, X, y, scoring=scoring)
		#scores = model_selection.cross_validate(clf, X, y, scoring=scoring, cv=None, n_jobs=None, return_train_score=True, return_estimator=True)

		print('CV keys = {}.'.format(sorted(scores.keys())))
		print(pd.DataFrame(scores))
		print('Recall macro (test) = {} (mean = {}, stddev = {}).'.format(scores['test_recall_macro'], scores['test_recall_macro'].mean(), scores['test_recall_macro'].std()))

		# Predefined or custom scoring function.
		scoring = {
			'prec_macro': 'precision_macro',
			'rec_macro': metrics.make_scorer(metrics.recall_score, average='macro')
		}
		scores = model_selection.cross_validate(clf, X, y, scoring=scoring, cv=5, return_train_score=True)

		print('CV keys = {}.'.format(sorted(scores.keys())))
		print(pd.DataFrame(scores))
		print('rec_macro (test) = {} (mean = {}, stddev = {}).'.format(scores['train_rec_macro'], scores['train_rec_macro'].mean(), scores['train_rec_macro'].std()))

		# A single metric.
		scores = model_selection.cross_validate(clf, X, y, scoring='precision_macro', cv=5, return_estimator=True)

		print('CV keys = {}.'.format(sorted(scores.keys())))
		print(pd.DataFrame(scores))
		print('Score (test) = {} (mean = {}, stddev = {}).'.format(scores['test_score'], scores['test_score'].mean(), scores['test_score'].std()))

# Hyper-parameter optimization.
#	REF [paper] >> "Random Search for Hyper-Parameter Optimization", JMLR 2012.
#	REF [site] >> http://scikit-learn.org/stable/modules/grid_search.html
#	REF [site] >> http://scikit-learn.org/stable/auto_examples/model_selection/randomized_search.html
def hyper_parameter_optimization_example():
	from time import time
	from scipy.stats import randint as sp_randint

	# Get some data.
	digits = datasets.load_digits()
	X, y = digits.data, digits.target

	# Build a classifier.
	clf = ensemble.RandomForestClassifier(n_estimators=20)

	# Utility function to report best scores.
	def report(results, n_top=3):
		for i in range(1, n_top + 1):
			candidates = np.flatnonzero(results['rank_test_score'] == i)
			for candidate in candidates:
				print('Model with rank: {0}'.format(i))
				print('Mean validation score: {0:.3f} (std: {1:.3f})'.format(
					results['mean_test_score'][candidate],
					results['std_test_score'][candidate])
				)
				print('Parameters: {0}'.format(results['params'][candidate]))
				print('')

	# Specify parameters and distributions to sample from.
	param_dist = {
		'max_depth': [3, None],
		'max_features': sp_randint(1, 11),
		'min_samples_split': sp_randint(2, 11),
		'min_samples_leaf': sp_randint(1, 11),
		'bootstrap': [True, False],
		'criterion': ['gini', 'entropy'],
	}

	# Run randomized search.
	n_iter_search = 20
	random_search = model_selection.RandomizedSearchCV(clf, param_distributions=param_dist, n_iter=n_iter_search)

	start = time()
	random_search.fit(X, y)
	print('RandomizedSearchCV took %.2f seconds for %d candidates parameter settings.' % ((time() - start), n_iter_search))
	report(random_search.cv_results_)

	# Use a full grid over all parameters.
	param_grid = {
		'max_depth': [3, None],
		'max_features': [1, 3, 10],
		'min_samples_split': [2, 3, 10],
		'min_samples_leaf': [1, 3, 10],
		'bootstrap': [True, False],
		'criterion': ['gini', 'entropy'],
	}

	# Run grid search.
	#os.environ["OMP_NUM_THREADS"] = "2"
	grid_search = model_selection.GridSearchCV(clf, param_grid=param_grid, verbose=1, n_jobs=2)
	start = time()
	grid_search.fit(X, y)
	print('GridSearchCV took %.2f seconds for %d candidate parameter settings.' % (time() - start, len(grid_search.cv_results_['params'])))
	report(grid_search.cv_results_)

# REF [site] >> https://scikit-learn.org/stable/modules/grid_search.html
def hyper_parameter_tuning_example():
	# Hyper-parameters are parameters that are not directly learnt within estimators.
	# In scikit-learn they are passed as arguments to the constructor of the estimator classes.
	# Typical examples include C, kernel and gamma for Support Vector Classifier, alpha for Lasso, etc.
	# It is possible and recommended to search the hyper-parameter space for the best cross validation score.
	# Any parameter provided when constructing an estimator may be optimized in this manner.
	# Specifically, to find the names and current values for all parameters for a given estimator:
	#	estimator.get_params()

	"""
	parameters = {
		'C': scipy.stats.expon(scale=100),
		'gamma': scipy.stats.expon(scale=0.1),
		'kernel': ['rbf'],
		'class_weight':['balanced', None],
	}
	parameters = {
		'C': utils.fixes.loguniform(1e0, 1e3),
		'gamma': utils.fixes.loguniform(1e-4, 1e-3),
		'kernel': ['rbf'],
		'class_weight':['balanced', None]
	}
	"""

	#--------------------
	# Exhaustive grid search.
	# REF [site] >> https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html

	if True:
		iris = datasets.load_iris()

		#param_grid = {'kernel':('linear', 'rbf'), 'C':[1, 10]}
		param_grid = [
			{'C': [1, 10, 100, 1000], 'kernel': ['linear']},
			{'C': [1, 10, 100, 1000], 'gamma': [0.001, 0.0001], 'kernel': ['rbf']},
		]
		clf = svm.SVC()
		search = model_selection.GridSearchCV(clf, param_grid)
		search.fit(iris.data, iris.target)

		print('CV keys = {}.'.format(sorted(search.cv_results_.keys())))
		print(pd.DataFrame(search.cv_results_))
		print('Best params: {}.'.format(search.best_params_))
		print('Best estimator: {}.'.format(search.best_estimator_))
		print('Best score = {}.'.format(search.best_score_))

	#--------------------
	# Randomized search.
	# REF [site] >> https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RandomizedSearchCV.html

	if True:
		iris = datasets.load_iris()

		clf = linear_model.LogisticRegression(solver='saga', tol=1e-2, max_iter=200, random_state=0)
		param_distributions = {
			'C': scipy.stats.uniform(loc=0, scale=4),
			'penalty': ['l2', 'l1']
		}
		search = model_selection.RandomizedSearchCV(clf, param_distributions, random_state=0)
		search = search.fit(iris.data, iris.target)

		print('CV keys = {}.'.format(sorted(search.cv_results_.keys())))
		print(pd.DataFrame(search.cv_results_))
		print('Best params: {}.'.format(search.best_params_))
		print('Best estimator: {}.'.format(search.best_estimator_))
		print('Best score = {}.'.format(search.best_score_))

	#--------------------
	# Randomized parameter optimization.
	# REF [site] >> https://scikit-learn.org/stable/auto_examples/model_selection/plot_randomized_search.html

	if True:
		X, y = datasets.load_digits(return_X_y=True, n_class=3)

		# Build a classifier.
		clf = linear_model.SGDClassifier(loss="hinge", penalty="elasticnet", fit_intercept=True)

		# Utility function to report best scores.
		def report(results, n_top=3):
			for i in range(1, n_top + 1):
				candidates = np.flatnonzero(results["rank_test_score"] == i)
				for candidate in candidates:
					print("Model with rank: {0}".format(i))
					print("Mean validation score: {0:.3f} (std: {1:.3f})".format(results["mean_test_score"][candidate], results["std_test_score"][candidate]))
					print("Parameters: {0}".format(results["params"][candidate]))
					print("")

		# Specify parameters and distributions to sample from.
		param_dist = {
			"average": [True, False],
			"l1_ratio": scipy.stats.uniform(0, 1),
			"alpha": utils.fixes.loguniform(1e-2, 1e0),
		}

		# Run randomized search.
		n_iter_search = 15
		random_search = model_selection.RandomizedSearchCV(clf, param_distributions=param_dist, n_iter=n_iter_search)

		start = time.time()
		random_search.fit(X, y)
		print("RandomizedSearchCV took %.2f seconds for %d candidates parameter settings." % ((time.time() - start), n_iter_search) )
		report(random_search.cv_results_)
		#print('CV keys = {}.'.format(sorted(random_search.cv_results_.keys())))
		#print(pd.DataFrame(random_search.cv_results_))

		# Use a full grid over all parameters.
		param_grid = {
			"average": [True, False],
			"l1_ratio": np.linspace(0, 1, num=10),
			"alpha": np.power(10, np.arange(-2, 1, dtype=float)),
		}

		# Run grid search.
		grid_search = model_selection.GridSearchCV(clf, param_grid=param_grid)
		start = time.time()
		grid_search.fit(X, y)

		print("GridSearchCV took %.2f seconds for %d candidate parameter settings." % (time.time() - start, len(grid_search.cv_results_["params"])))
		report(grid_search.cv_results_)
		#print('CV keys = {}.'.format(sorted(grid_search.cv_results_.keys())))
		#print(pd.DataFrame(grid_search.cv_results_))

	#--------------------
	# Searching for optimal parameters with successive halving.
	# REF [site] >> https://scikit-learn.org/stable/modules/grid_search.html

def main():
	#learning_curve_example_1()
	learning_curve_example_2()

	#train_test_split_example()
	#split_example()
	#k_fold_example()
	#leave_out_example()

	#cross_validation_example_1()
	#cross_validation_example_2()

	#hyper_parameter_optimization_example()
	#hyper_parameter_tuning_example()

#--------------------------------------------------------------------

if '__main__' == __name__:
	main()
