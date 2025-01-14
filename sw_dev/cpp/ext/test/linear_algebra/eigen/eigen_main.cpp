//#include "stdafx.h"
#include <iostream>


namespace {
namespace local {

}  // namespace local
}  // unnamed namespace

namespace my_eigen {

void basic_operation();
void lu();
void evd();
void svd();
void qr();
void cholesky();

void linear_system();
void linear_least_squares();
void nonlinear_least_squares();

void transformation_test();

void spline();

}  // namespace my_eigen

//-----------------------------------------------------------------------
// Porting from Eigen2 to Eigen3.
//	REF [site] >> http://eigen.tuxfamily.org/dox/Eigen2ToEigen3.html

int eigen_main(int argc, char *argv[])
{
	//my_eigen::basic_operation();

	// Decomposition -----------------------------------------
	//my_eigen::lu();
	//my_eigen::evd();
	//my_eigen::svd();
	//my_eigen::qr();
	//my_eigen::cholesky();

	// Linear system -----------------------------------------
	//my_eigen::linear_system();

	// Least squares -----------------------------------------
	//my_eigen::linear_least_squares();
	//my_eigen::nonlinear_least_squares();  // Not yet implemented.

	// Geometry ----------------------------------------------
	//	- Transformation.
	my_eigen::geometry();

	// Unsupported -------------------------------------------
	//my_eigen::tensor();
	//my_eigen::spline();

	return 0;
}
