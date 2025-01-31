//#include "stdafx.h"
#if defined(_WIN64) || defined(WIN64) || defined(_WIN32) || defined(WIN32)
#include <vld/vld.h>
#endif
#include <iostream>
#include <ctime>
#include <cstdlib>


int main(int argc, char *argv[])
{
	int fann_main(int argc, char *argv[]);
	int opennn_main(int argc, char *argv[]);

	int elm_main(int argc, char *argv[]);

	int retval = EXIT_SUCCESS;
	try
	{
		std::srand((unsigned int)std::time(NULL));

		std::cout << "Fast Artificial Neural Network (FANN) library -----------------------" << std::endl;
		//retval = fann_main(argc, argv);

		std::cout << "\nOpen Neural Networks (OpenNN) library -------------------------------" << std::endl;
		//retval = opennn_main(argc, argv);

		std::cout << "\nExtreme Learning Machines (ELM) algorithm ---------------------------" << std::endl;
		retval = elm_main(argc, argv);
	}
	catch (const std::bad_alloc &ex)
	{
		std::cerr << "std::bad_alloc caught: " << ex.what() << std::endl;
		retval = EXIT_FAILURE;
	}
	catch (const std::exception &ex)
	{
		std::cerr << "std::exception caught: " << ex.what() << std::endl;
		retval = EXIT_FAILURE;
	}
	catch (...)
	{
		std::cerr << "Unknown exception caught." << std::endl;
		retval = EXIT_FAILURE;
	}

	std::cout << "Press any key to exit ..." << std::endl;
	std::cin.get();

	return retval;
}
