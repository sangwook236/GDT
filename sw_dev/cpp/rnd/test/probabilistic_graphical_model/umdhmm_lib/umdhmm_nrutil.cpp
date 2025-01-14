/*
**      File:   nrutil.c
**      Purpose: Memory allocation routines borrowed from the
**		book "Numerical Recipes" by Press, Flannery, Teukolsky,
**		and Vetterling.
**              state sequence and probablity of observing a sequence
**              given the model.
**      Organization: University of Maryland
**
**      $Id: nrutil.c,v 1.2 1998/02/19 16:31:35 kanungo Exp kanungo $
*/

#include <cstdio>
#include <cstdlib>
#include <malloc.h>


namespace umdhmm {

static char rcsid[] = "$Id: nrutil.c,v 1.2 1998/02/19 16:31:35 kanungo Exp kanungo $";

void nrerror(const char *error_text)
{
	fprintf(stderr, "Numerical Recipes run-time error...\n");
	fprintf(stderr, "%s\n", error_text);
	fprintf(stderr, "...now exiting to system...\n");
	exit(1);
}

float * vector(int nl, int nh)
{
	float *v = (float *)calloc(unsigned(nh - nl + 1), sizeof(float));
	if (!v) nrerror("allocation failure in vector()");
	return v - nl;
}

int * ivector(int nl, int nh)
{
	int *v = (int *)calloc(unsigned(nh - nl + 1), sizeof(int));
	if (!v) nrerror("allocation failure in ivector()");
	return v - nl;
}

double * dvector(int nl, int nh)
{
	double *v = (double *)calloc(unsigned(nh - nl + 1), sizeof(double));
	if (!v) nrerror("allocation failure in dvector()");
	return v - nl;
}

float ** matrix(int nrl, int nrh, int ncl, int nch)
{
	float **m = (float **)calloc(unsigned(nrh - nrl + 1), sizeof(float *));
	if (!m) nrerror("allocation failure 1 in matrix()");
	m -= nrl;

	for (int i = nrl; i <= nrh; ++i)
	{
		m[i] = (float *)calloc(unsigned(nch - ncl + 1), sizeof(float));
		if (!m[i]) nrerror("allocation failure 2 in matrix()");
		m[i] -= ncl;
	}
	return m;
}

double ** dmatrix(int nrl, int nrh, int ncl, int nch)
{
	double **m = (double **)calloc(unsigned(nrh - nrl + 1), sizeof(double *));
	if (!m) nrerror("allocation failure 1 in dmatrix()");
	m -= nrl;

	for (int i = nrl; i <= nrh; ++i)
	{
		m[i] = (double *)calloc(unsigned(nch - ncl + 1), sizeof(double));
		if (!m[i]) nrerror("allocation failure 2 in dmatrix()");
		m[i] -= ncl;
	}

	return m;
}

int ** imatrix(int nrl, int nrh, int ncl, int nch)
{
	int **m = (int **)calloc(unsigned(nrh - nrl + 1), sizeof(int *));
	if (!m) nrerror("allocation failure 1 in imatrix()");
	m -= nrl;

	for (int i = nrl; i <= nrh; ++i)
	{
		m[i] = (int *)calloc(unsigned(nch - ncl + 1), sizeof(int));
		if (!m[i]) nrerror("allocation failure 2 in imatrix()");
		m[i] -= ncl;
	}

	return m;
}

float ** submatrix(float **a, int oldrl, int oldrh, int oldcl, int oldch, int newrl, int newcl)
{
	float **m = (float **)calloc(unsigned(oldrh - oldrl + 1), sizeof(float *));
	if (!m) nrerror("allocation failure in submatrix()");
	m -= newrl;

	for(int i = oldrl, j = newrl; i <= oldrh; ++i, ++j)
		m[j] = a[i] + oldcl - newcl;

	return m;
}

void free_vector(float *v, int nl, int nh)
{
	free((char *)(v + nl));
}

void free_dvector(double *v, int nl, int nh)
{
	free((char *)(v + nl));
}

void free_ivector(int *v, int nl, int nh)
{
	free((char *)(v + nl));
}

void free_matrix(float **m, int nrl, int nrh, int ncl, int nch)
{
	for (int i = nrh; i >= nrl; --i)
		free((char *)(m[i] + ncl));
	free((char *)(m + nrl));
}

void free_dmatrix(double **m, int nrl, int nrh, int ncl, int nch)
{
	for (int i = nrh; i >= nrl; --i)
		free((char *)(m[i] + ncl));
	free((char *)(m + nrl));
}

void free_imatrix(int **m, int nrl, int nrh, int ncl, int nch)
{
	for (int i = nrh; i >= nrl; --i)
		free((char *)(m[i] + ncl));
	free((char *)(m + nrl));
}

void free_submatrix(float **b, int nrl, int nrh, int ncl, int nch)
{
	free((char *)(b + nrl));
}

float ** convert_matrix(float *a, int nrl, int nrh, int ncl, int nch)
{
	const int nrow = nrh - nrl + 1;
	const int ncol = nch - ncl + 1;
	float **m = (float **)calloc(unsigned(nrow), sizeof(float *));
	if (!m) nrerror("allocation failure in convert_matrix()");
	m -= nrl;
	for (int i = 0, j = nrl; i <= nrow - 1; ++i, ++j)
		m[j] = a + ncol * i - ncl;

	return m;
}

void free_convert_matrix(float **b, int nrl, int nrh, int ncl, int nch)
{
	free((char *)(b + nrl));
}

}  // namespace umdhmm
