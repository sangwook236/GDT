#include "generic-driver.h"

#include <vl/mser.h>
#include <vl/stringop.h>
#include <vl/pgm.h>
#include <vl/getopt_long.h>

#include <string>
#include <iostream>


namespace {
namespace local {

bool werr(const vl_bool err, const std::string &name)
{
	if (VL_ERR_OVERFLOW == err)
	{
		std::cerr << "output file name too long." << std::endl;
		return false;
	}
	else if (err)
	{
		std::cerr << "could not open '" << name << "' for writing." << std::endl;
		return false;
	}

	return true;
}

}  // namespace local
}  // unnamed namespace

namespace my_vlfeat {

void mser()
{
	const std::string input_filename = "./img_uint8/machine_vision/vlfeat/box.pgm";

	// algorithm parameters.
	double delta = -1;
	double max_area = -1;
	double min_area = -1;
	double max_variation = -1;
	double min_diversity = -1;
	int bright_on_dark = 1;
	int dark_on_bright = 1;

	vl_bool err = VL_ERR_OK;
	int exit_code = 0;
	const bool verbose = true;

	VlFileMeta frm = { 0, "%.frame", VL_PROT_ASCII, "", 0 };
	VlFileMeta piv = { 0, "%.mser",  VL_PROT_ASCII, "", 0 };
	VlFileMeta met = { 0, "%.meta",  VL_PROT_ASCII, "", 0 };

	// get basenmae from filename.
    char basename[1024];
	vl_size q = vl_string_basename(basename, sizeof(basename), input_filename.c_str(), 1) ;
	err = (q >= sizeof(basename));
	if (err)
	{
		std::cerr << "basename of '" << input_filename.c_str() << "' is too long" << std::endl;
		err = VL_ERR_OVERFLOW;
		return;
	}

	if (verbose)
	{
		std::cout << "mser: processing " << input_filename.c_str() << std::endl;
		std::cout << "mser:    basename is " << basename << std::endl;
	}

	// open output files.
	err = vl_file_meta_open(&piv, basename, "w");  if (!local::werr(err, piv.name)) return;
	err = vl_file_meta_open(&frm, basename, "w");  if (!local::werr(err, frm.name)) return;
	err = vl_file_meta_open(&met, basename, "w");  if (!local::werr(err, met.name)) return;

	if (verbose)
	{
		if (piv.active) std::cout << "mser:  writing seeds  to " << piv.name << std::endl;
		if (frm.active) std::cout << "mser:  writing frames to " << frm.name << std::endl;
		if (met.active) std::cout << "mser:  writing meta   to " << met.name << std::endl;
	}

    // read image img_uint8.
    vl_uint8 *img_uint8 = NULL;
	VlPgmImage pim;
	if (vl_pgm_read_new(input_filename.c_str(), &pim, &img_uint8))
	{
		std::cerr << "fail to load image, " << input_filename << std::endl;
		return;
	}

	// process img_uint8.
    enum { ndims = 2 };
	int dims[ndims] = { pim.width, pim.height };

	VlMserFilt *filt = vl_mser_new(ndims, dims);
	VlMserFilt *filtinv = vl_mser_new(ndims, dims);
	if (!filt || !filtinv)
	{
		std::cerr << "could not create an MSER filter." << std::endl;
		return;
	}

	if (delta >= 0) vl_mser_set_delta(filt, (vl_mser_pix)delta);
	if (max_area >= 0) vl_mser_set_max_area(filt, max_area);
	if (min_area >= 0) vl_mser_set_min_area(filt, min_area);
	if (max_variation >= 0) vl_mser_set_max_variation(filt, max_variation);
	if (min_diversity >= 0) vl_mser_set_min_diversity(filt, min_diversity);
	if (delta >= 0) vl_mser_set_delta(filtinv, (vl_mser_pix)delta);
	if (max_area >= 0) vl_mser_set_max_area(filtinv, max_area);
	if (min_area >= 0) vl_mser_set_min_area(filtinv, min_area);
	if (max_variation >= 0) vl_mser_set_max_variation(filtinv, max_variation);
	if (min_diversity >= 0) vl_mser_set_min_diversity(filtinv, min_diversity);

	if (verbose)
	{
		std::cout << "mser: parameters:" << std::endl;
		std::cout << "mser:   delta         = " << vl_mser_get_delta(filt) << std::endl;
		std::cout << "mser:   max_area      = " << vl_mser_get_max_area(filt) << std::endl;
		std::cout << "mser:   min_area      = " << vl_mser_get_min_area(filt) << std::endl;
		std::cout << "mser:   max_variation = " << vl_mser_get_max_variation(filt) << std::endl;
		std::cout << "mser:   min_diversity = " << vl_mser_get_min_diversity(filt) << std::endl;
	}

	if (dark_on_bright)
	{
		vl_mser_process(filt, (vl_mser_pix *)img_uint8);

		// save result.
		int nregions = vl_mser_get_regions_num(filt);
		vl_uint const *regions = vl_mser_get_regions(filt);

		if (piv.active)
		{
			for (int i = 0; i < nregions; ++i)
				fprintf(piv.file, "%d ", regions [i]);
		}

		if (frm.active)
		{
			vl_mser_ell_fit(filt) ;

			const int nframes = vl_mser_get_ell_num(filt);
			const int dof = vl_mser_get_ell_dof(filt);
			const float *frames = vl_mser_get_ell(filt);
			for (int i = 0; i < nframes; ++i)
			{
				for (int j = 0; j < dof; ++j)
					fprintf(frm.file, "%f ", *frames++);
				fprintf(frm.file, "\n");
			}
		}
	}

	if (bright_on_dark)
	{
		// allocate buffer.
		vl_uint8 *datainv = new vl_uint8 [vl_pgm_get_npixels(&pim) * vl_pgm_get_bpp(&pim)];
		if (!datainv)
		{
			std::cerr << "could not allocate enough memory." << std::endl;
			return;
		}

		for (signed i = 0; i < (signed)vl_pgm_get_npixels(&pim); ++i)
			datainv[i] = ~img_uint8[i]; //255 - img_uint8[i]

		vl_mser_process(filtinv, (vl_mser_pix *)datainv);

		// save result.
		int nregionsinv = vl_mser_get_regions_num(filtinv);
		vl_uint const *regionsinv = vl_mser_get_regions(filtinv);

		if (piv.active)
		{
			for (int i = 0; i < nregionsinv; ++i)
				fprintf(piv.file, "%d ", -regionsinv [i]);
		}

		if (frm.active)
		{
			vl_mser_ell_fit(filtinv);

			const int nframesinv = vl_mser_get_ell_num(filtinv);
			const int dof = vl_mser_get_ell_dof(filtinv);
			const float *framesinv = vl_mser_get_ell(filtinv);
			for (int i = 0; i < nframesinv; ++i)
			{
				for (int j = 0; j < dof; ++j)
					fprintf(frm.file, "%f ", *framesinv++);
				fprintf(frm.file, "\n");
			}
		}

		if (datainv)
		{
			delete [] datainv;
			datainv = NULL;
		}
	}

	// release filter.
    if (filt)
	{
      vl_mser_delete(filt);
      filt = NULL;
    }

    if (filtinv)
	{
      vl_mser_delete(filtinv);
      filtinv = NULL;
    }

	// release image img_uint8.
	if (img_uint8)
	{
		delete [] img_uint8;
		img_uint8 = NULL;
	}

    vl_file_meta_close(&frm);
    vl_file_meta_close(&piv);
    vl_file_meta_close(&met);
}

}  // namespace my_vlfeat
