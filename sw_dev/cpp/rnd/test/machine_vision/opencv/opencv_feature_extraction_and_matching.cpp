//#include "stdafx.h"
#define CV_NO_BACKWARD_COMPATIBILITY
#include <opencv2/xfeatures2d.hpp>
#include <opencv2/opencv.hpp>
#include <iostream>
#include <list>

#if 0
#define DRAW_RICH_KEYPOINTS_MODE     0
#define DRAW_OUTLIERS_MODE           0
#endif


namespace {
namespace local {

void crossCheckMatching(const cv::Ptr<cv::DescriptorMatcher> &matcher, const cv::Mat &descriptors1, const cv::Mat &descriptors2, std::vector<cv::DMatch> &filteredMatches12, int knn = 1)
{
	filteredMatches12.clear();
	std::vector<std::vector<cv::DMatch> > matches12, matches21;
	matcher->knnMatch(descriptors1, descriptors2, matches12, knn);
	matcher->knnMatch(descriptors2, descriptors1, matches21, knn);
	for (size_t m = 0; m < matches12.size(); ++m)
	{
		bool findCrossCheck = false;
		for (size_t fk = 0; fk < matches12[m].size(); ++fk)
		{
			const cv::DMatch &forward = matches12[m][fk];

			for (size_t bk = 0; bk < matches21[forward.trainIdx].size(); ++bk)
			{
				const cv::DMatch &backward = matches21[forward.trainIdx][bk];
				if (backward.trainIdx == forward.queryIdx)
				{
					filteredMatches12.push_back(forward);
					findCrossCheck = true;
					break;
				}
			}

			if (findCrossCheck) break;
		}
	}
}


#if 0
void feature_extraction_and_matching()
{
	// "FAST", "STAR", "SIFT", "SURF", "ORB", "MSER", "GFTT", "HARRIS", "DENSE", "SimpleBlob".
	// also combined format is supported: feature detector adapter name ("Grid", "Pyramid") + feature detector name (see above), e.g. "GridFAST", "PyramidSTAR", etc.
	const std::string featureDetectorName("MSER");

	// "SIFT", "SURF", "ORB", "BRIEF", "Calonder". (?)
	// also combined format is supported: descriptor extractor adapter name ("Opponent") + descriptor extractor name (see above), e.g. "OpponentSIFT", etc.
	const std::string decriptorExtractorName("SIFT");

	// "BruteForce"(it uses L2), "BruteForce-L1", "BruteForce-Hamming", "BruteForce-HammingLUT", "FlannBased".
	const std::string decriptorMatcherName("FlannBased");

	cv::Ptr<cv::FeatureDetector> detector = cv::FeatureDetector::create(featureDetectorName);
	cv::Ptr<cv::DescriptorExtractor> descriptorExtractor = cv::DescriptorExtractor::create(decriptorExtractorName);
	cv::Ptr<cv::DescriptorMatcher> matcher = cv::DescriptorMatcher::create(decriptorMatcherName);
	//const int mactherFilterType = 0;  // None filter.
	const int mactherFilterType = 1;  // Cross checker filter.

	const double ransacReprojThreshold = 1.0;
	const bool evaluationMode = false;

	if (detector.empty())
	{
		std::cout << "Can not create detector of given types." << std::endl;
		return;
	}
	if (descriptorExtractor.empty())
	{
		std::cout << "Can not create descriptor extractor of given types." << std::endl;
		return;
	}
	if (matcher.empty())
	{
		std::cout << "Can not create descriptor matcher of given types." << std::endl;
		return;
	}

	//
	const std::string filename1("../data/machine_vision/opencv/melon_target.png");
	const std::string filename2("../data/machine_vision/opencv/melon_1.png");
	//const std::string filename2("../data/machine_vision/opencv/melon_2.png");
	//const std::string filename2("../data/machine_vision/opencv/melon_3.png");

	const std::string windowName("Feature extraction 2");
	cv::namedWindow(windowName, cv::WINDOW_AUTOSIZE);

	//
	const cv::Mat rgb1(cv::imread(filename1, cv::IMREAD_COLOR));
	if (rgb1.empty())
	{
		std::cout << "Failed to load image file: " << filename1 << std::endl;
		return;
	}

	// Extract keypoints.
	std::cout << "Extracting keypoints from first image ..." << std::endl;
	std::vector<cv::KeyPoint> keypoints1;
	detector->detect(rgb1, keypoints1);
	std::cout << '\t' << keypoints1.size() << " points" << std::endl;

	// compute descriptors.
	std::cout << "Computing descriptors for keypoints from first image..." << std::endl;
	cv::Mat descriptors1;
	descriptorExtractor->compute(rgb1, keypoints1, descriptors1);

	cv::RNG rng = cv::theRNG();
	cv::Mat H1to2;
	cv::Mat rgb2;
	if (evaluationMode)
	{
		warpPerspectiveRand(rgb1, rgb2, H1to2, rng);
		if (rgb2.empty())
		{
			std::cout << "Failed to create image" << std::endl;
			return;
		}
	}
	else
	{
		rgb2 = cv::imread(filename2, cv::IMREAD_COLOR);
		if (rgb2.empty())
		{
			std::cout << "Fail to load image file: " << filename2 << std::endl;
			return;
		}
	}

	// Extract keypoints.
	std::cout << "Extracting keypoints from second image ..." << std::endl;
	std::vector<cv::KeyPoint> keypoints2;
	detector->detect(rgb2, keypoints2);
	std::cout << '\t' << keypoints2.size() << " points" << std::endl;

	if (evaluationMode && !H1to2.empty())
	{
		std::cout << "Evaluate feature detector ..." << std::endl;
		float repeatability;
		int correspCount;
		cv::evaluateFeatureDetector(rgb1, rgb2, H1to2, &keypoints1, &keypoints2, repeatability, correspCount);
		std::cout << "\tRepeatability = " << repeatability << std::endl;
		std::cout << "\tCorrespCount = " << correspCount << std::endl;
	}

	// Compute descriptors.
	std::cout << "Computing descriptors for keypoints from second image ..." << std::endl;
	cv::Mat descriptors2;
	descriptorExtractor->compute(rgb2, keypoints2, descriptors2);

	// Match descriptors.
	std::cout << "Matching descriptors ..." << std::endl;
	std::vector<cv::DMatch> filteredMatches;
	//std::vector<std::vector<DMatch> > filteredMatches;
	switch (mactherFilterType)
	{
	case 0:
		{
			matcher->match(descriptors1, descriptors2, filteredMatches);
			//const int k = 5;
			//matcher->knnMatch(descriptors1, descriptors2, filteredMatches, k);
			//const float maxDistance = 5.0f;
			//matcher->radiusMatch(descriptors1, descriptors2, filteredMatches, maxDistance);
		}
		break;
	case 1:
		crossCheckMatching(matcher, descriptors1, descriptors2, filteredMatches, 1);
		break;
	}

	if (evaluationMode && !H1to2.empty())
	{
		std::cout << "Evaluate descriptor match ..." << std::endl;
		std::vector<cv::Point2f> curve;
		cv::Ptr<cv::GenericDescriptorMatcher> gdm = new cv::VectorDescriptorMatcher(descriptorExtractor, matcher);
		cv::evaluateGenericDescriptorMatcher(rgb1, rgb2, H1to2, keypoints1, keypoints2, 0, 0, curve, gdm);
		for (float l_p = 0; l_p < 1 - FLT_EPSILON; l_p += 0.1f)
			std::cout << "\t1-precision = " << l_p << "; recall = " << cv::getRecall(curve, l_p) << std::endl;
	}

	std::vector<int> queryIdxs(filteredMatches.size()), trainIdxs(filteredMatches.size());
	for (size_t i = 0; i < filteredMatches.size(); ++i)
	{
		queryIdxs[i] = filteredMatches[i].queryIdx;
		trainIdxs[i] = filteredMatches[i].trainIdx;
	}

	if (!evaluationMode && ransacReprojThreshold >= 0.0)
	{
		std::cout << "Computing homography (RANSAC) ..." << std::endl;
		std::vector<cv::Point2f> points1, points2;
		cv::KeyPoint::convert(keypoints1, points1, queryIdxs);
		cv::KeyPoint::convert(keypoints2, points2, trainIdxs);

		//H1to2 = cv::findHomography(cv::Mat(points1), cv::Mat(points2), cv::LMEDS, ransacReprojThreshold);
		H1to2 = cv::findHomography(cv::Mat(points1), cv::Mat(points2), cv::RANSAC, ransacReprojThreshold);
	}

	cv::Mat drawImg;
	if (!H1to2.empty())  // Filter outliers.
	{
		std::vector<char> matchesMask(filteredMatches.size(), 0);
		std::vector<cv::Point2f> points1, points2;
		cv::KeyPoint::convert(keypoints1, points1, queryIdxs);
		cv::KeyPoint::convert(keypoints2, points2, trainIdxs);
		cv::Mat points1_transformed;
		cv::perspectiveTransform(cv::Mat(points1), points1_transformed, H1to2);

		for (size_t i1 = 0; i1 < points1.size(); ++i1)
		{
			if (cv::norm(points2[i1] - points1_transformed.at<cv::Point2f>((int)i1, 0)) < 4)  // inlier
				matchesMask[i1] = 1;
		}

		// Draw inliers.
		cv::drawMatches(rgb1, keypoints1, rgb2, keypoints2, filteredMatches, drawImg, CV_RGB(0, 255, 0), CV_RGB(0, 0, 255), matchesMask
#if DRAW_RICH_KEYPOINTS_MODE
			, cv::DrawMatchesFlags::DRAW_RICH_KEYPOINTS
#endif
		);

#if DRAW_OUTLIERS_MODE
		// Draw outliers.
		for (size_t i1 = 0; i1 < matchesMask.size(); ++i1)
			matchesMask[i1] = !matchesMask[i1];
		cv::drawMatches(rgb1, keypoints1, rgb2, keypoints2, filteredMatches, drawImg, CV_RGB(0, 0, 255), CV_RGB(255, 0, 0), matchesMask,
			cv::DrawMatchesFlags::DRAW_OVER_OUTIMG | cv::DrawMatchesFlags::NOT_DRAW_SINGLE_POINTS);
#endif
	}
	else
		cv::drawMatches(rgb1, keypoints1, rgb2, keypoints2, filteredMatches, drawImg);

	cv::imshow(windowName, drawImg);

	cv::waitKey(0);

	cv::destroyWindow(windowName);
}
#else
void feature_extraction_and_matching()
{
	std::list<std::pair<std::string, std::string> > filename_pairs;
#if 0
	filename_pairs.push_back(std::make_pair("../data/machine_vision/opencv/melon_target.png", "./data/machine_vision/opencv/melon_1.png"));
	//filename_pairs.push_back(std::make_pair("../data/machine_vision/opencv/melon_2.png", "./data/machine_vision/opencv/melon_3.png"));
#elif 1
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_1.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_2.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_3.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_4.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_5.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_6.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_7.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_0.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_8.jpg"));

	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_1.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_2.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_2.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_3.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_3.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_4.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_4.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_5.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_5.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_6.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_6.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_7.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_7.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_8.jpg"));
	filename_pairs.push_back(std::make_pair("D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_8.jpg", "D:/dataset/failure_analysis/defect/visible_ray/auto_9_view/Image_20171110/C12/resized/Review_1.jpg"));
#endif

	//
	cv::Ptr<cv::Feature2D> defaultDetector(cv::xfeatures2d::SIFT::create()), defaultDescriptor(cv::xfeatures2d::SIFT::create());

	cv::Ptr<cv::Feature2D> detector(cv::xfeatures2d::SIFT::create()), descriptor(detector);
	//cv::Ptr<cv::Feature2D> detector(cv::xfeatures2d::SURF::create()), descriptor(detector);
	//cv::Ptr<cv::Feature2D> detector(cv::BRISK::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> detector(cv::ORB::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> detector(cv::MSER::create());  // Use cv::MSER::detectRegions().
	//cv::Ptr<cv::Feature2D> detector(cv::FastFeatureDetector::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> detector(cv::AgastFeatureDetector::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> detector(cv::GFTTDetector::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> detector(cv::SimpleBlobDetector::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> detector(cv::KAZE::create()), descriptor(detector);
	//cv::Ptr<cv::Feature2D> detector(cv::AKAZE::create()), descriptor(detector);
	//cv::Ptr<cv::Feature2D> descriptor(cv::xfeatures2d::FREAK::create()), detector(defaultDetector);  // Use a gray image as an input.
	//cv::Ptr<cv::Feature2D> detector(cv::xfeatures2d::StarDetector::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> descriptor(cv::xfeatures2d::BriefDescriptorExtractor::create()), detector(defaultDetector);
	//cv::Ptr<cv::Feature2D> descriptor(cv::xfeatures2d::LUCID::create()), detector(defaultDetector);
	//cv::Ptr<cv::Feature2D> descriptor(cv::xfeatures2d::LATCH::create()), detector(defaultDetector);
	//cv::Ptr<cv::Feature2D> descriptor(cv::xfeatures2d::DAISY::create()), detector(defaultDetector);
	//cv::Ptr<cv::Feature2D> detector(cv::xfeatures2d::MSDDetector::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> descriptor(cv::xfeatures2d::VGG::create()), detector(defaultDetector);
	//cv::Ptr<cv::Feature2D> descriptor(cv::xfeatures2d::BoostDesc::create()), detector(defaultDetector);
	//cv::Ptr<cv::Feature2D> signature(cv::xfeatures2d::PCTSignatures::create());
	//cv::Ptr<cv::Feature2D> signature(cv::xfeatures2d::PCTSignaturesSQFD::create());
	//cv::Ptr<cv::Feature2D> detector(cv::xfeatures2d::HarrisLaplaceFeatureDetector::create()), descriptor(defaultDescriptor);
	//cv::Ptr<cv::Feature2D> detector(cv::xfeatures2d::AffineFeature2D::create(detector, descriptor)), descriptor(detector);  // Affine adaptation for key points.

	//cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create(cv::DescriptorMatcher::FLANNBASED));
	cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create(cv::DescriptorMatcher::BRUTEFORCE));
	//cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create(cv::DescriptorMatcher::BRUTEFORCE_SL2));
	//cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create(cv::DescriptorMatcher::BRUTEFORCE_L1));
	//cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create(cv::DescriptorMatcher::BRUTEFORCE_HAMMING));
	//cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create(cv::DescriptorMatcher::BRUTEFORCE_HAMMINGLUT));

	const int mactherFilterType = 0;  // None filter.
	//const int mactherFilterType = 1;  // Cross checker filter.

	const size_t MAX_KEYPOINT_COUNT = 200;
	const double ransacReprojThreshold = 3.0;

	const int kernelSize = 7;
	const double sigma = 0.0;

	const double inlier_threshold = 4.0;

	cv::Mat gray1, gray2;
	std::vector<cv::KeyPoint> keypoints1, keypoints2;
	cv::Mat descriptors1, descriptors2;
	std::vector<cv::DMatch> matches;
	//std::vector<std::vector<cv::DMatch> > matches;
	cv::Mat img_matches, img_warped;
	std::vector<cv::Point2f> points1, points2;
	cv::Mat H1to2;
	cv::Mat points1_transformed;
	for (std::list<std::pair<std::string, std::string> >::const_iterator cit = filename_pairs.begin(); cit != filename_pairs.end(); ++cit)
	{
		const std::string filename1(cit->first);
		const std::string filename2(cit->second);

		const cv::Mat rgb1(cv::imread(filename1, cv::IMREAD_COLOR));
		if (rgb1.empty())
		{
			std::cout << "Failed to load an image file: " << filename1 << std::endl;
			continue;
		}
		const cv::Mat rgb2(cv::imread(filename2, cv::IMREAD_COLOR));
		if (rgb2.empty())
		{
			std::cout << "Failed to load an image file: " << filename2 << std::endl;
			continue;
		}

#if 1
		// Blur image.
		cv::GaussianBlur(rgb1, rgb1, cv::Size(kernelSize, kernelSize), sigma, sigma, cv::BORDER_DEFAULT);
		cv::GaussianBlur(rgb2, rgb2, cv::Size(kernelSize, kernelSize), sigma, sigma, cv::BORDER_DEFAULT);
#endif

		cv::cvtColor(rgb1, gray1, cv::COLOR_BGR2GRAY);
		cv::cvtColor(rgb2, gray2, cv::COLOR_BGR2GRAY);

		// Detect keypoints.
		std::cout << "Detecting keypoints ..." << std::endl;
		detector->detect(rgb1, keypoints1);
		std::cout << '\t' << keypoints1.size() << " points detected." << std::endl;
		cv::KeyPointsFilter::retainBest(keypoints1, MAX_KEYPOINT_COUNT);
		std::cout << '\t' << keypoints1.size() << " points filtered." << std::endl;

		detector->detect(rgb2, keypoints2);
		std::cout << '\t' << keypoints2.size() << " points detected." << std::endl;
		cv::KeyPointsFilter::retainBest(keypoints2, MAX_KEYPOINT_COUNT);
		std::cout << '\t' << keypoints2.size() << " points filtered." << std::endl;

		// Compute feature descriptors.
		std::cout << "Computing feature descriptors ..." << std::endl;
		descriptor->compute(rgb1, keypoints1, descriptors1);
		descriptor->compute(rgb2, keypoints2, descriptors2);

		// Match descriptors.
		std::cout << "Matching descriptors ..." << std::endl;
		switch (mactherFilterType)
		{
		case 0:
			{
				matcher->match(descriptors1, descriptors2, matches);
				//const int k = 5;
				//matcher->knnMatch(descriptors1, descriptors2, matches, k);
				//const float maxDistance = 5.0f;
				//matcher->radiusMatch(descriptors1, descriptors2, matches, maxDistance);
			}
			break;
		case 1:
			crossCheckMatching(matcher, descriptors1, descriptors2, matches, 1);
			break;
		}

		// Show results.
#if 1
		std::vector<int> queryIdxs(matches.size()), trainIdxs(matches.size());
		for (size_t i = 0; i < matches.size(); ++i)
		{
			queryIdxs[i] = matches[i].queryIdx;
			trainIdxs[i] = matches[i].trainIdx;
		}

		std::cout << "Computing homography ..." << std::endl;
		cv::KeyPoint::convert(keypoints1, points1, queryIdxs);
		cv::KeyPoint::convert(keypoints2, points2, trainIdxs);

		//H1to2 = cv::findHomography(cv::Mat(points1), cv::Mat(points2), 0, ransacReprojThreshold);
		//H1to2 = cv::findHomography(cv::Mat(points1), cv::Mat(points2), cv::LMEDS, ransacReprojThreshold);
		H1to2 = cv::findHomography(cv::Mat(points1), cv::Mat(points2), cv::RANSAC, ransacReprojThreshold);
		//H1to2 = cv::findHomography(cv::Mat(points1), cv::Mat(points2), cv::RHO, ransacReprojThreshold);

		//std::cout << "Homograph = " << H1to2 << std::endl;

		// Warp image.
		cv::warpPerspective(rgb1, img_warped, H1to2, cv::Size(300, 300), cv::INTER_LINEAR, cv::BORDER_CONSTANT, cv::Scalar());

		// Transform points.
		std::vector<char> matchesMask(matches.size(), 0);
		cv::perspectiveTransform(cv::Mat(points1), points1_transformed, H1to2);

		// Draw inliers.
		for (size_t i = 0; i < points1.size(); ++i)
			if (cv::norm(points2[i] - points1_transformed.at<cv::Point2f>((int)i, 0)) < inlier_threshold)  // Inlier.
				matchesMask[i] = 1;

		cv::drawMatches(rgb1, keypoints1, rgb2, keypoints2, matches, img_matches, CV_RGB(0, 255, 0), CV_RGB(0, 0, 255), matchesMask, cv::DrawMatchesFlags::DEFAULT);
		//cv::drawMatches(rgb1, keypoints1, rgb2, keypoints2, matches, img_matches, CV_RGB(0, 255, 0), CV_RGB(0, 0, 255), matchesMask, cv::DrawMatchesFlags::DRAW_RICH_KEYPOINTS);

#if 0
		// Draw outliers.
		for (size_t i = 0; i < matchesMask.size(); ++i)
			matchesMask[i] = !matchesMask[i];

		cv::drawMatches(rgb1, keypoints1, rgb2, keypoints2, matches, img_matches, CV_RGB(255, 0, 255), CV_RGB(255, 0, 0), matchesMask, cv::DrawMatchesFlags::DRAW_OVER_OUTIMG | cv::DrawMatchesFlags::NOT_DRAW_SINGLE_POINTS);
#endif
#else
		cv::drawMatches(rgb1, keypoints1, rgb2, keypoints2, matches, img_matches);
#endif

		cv::imshow("Feature - Match", img_matches);
		cv::imshow("Feature - Warp", img_warped);

		cv::waitKey(0);
	}

	cv::destroyAllWindows();
}
#endif

// REF [site] >> https://github.com/pablofdezalc/test_kaze_akaze_opencv/blob/master/src/utils.cpp
void draw_keypoints(cv::Mat& img, const std::vector<cv::KeyPoint>& kpts)
{
	int x = 0, y = 0;
	float radius = 0.0;

	for (size_t i = 0; i < kpts.size(); ++i)
	{
		x = (int)(kpts[i].pt.x + .5);
		y = (int)(kpts[i].pt.y + .5);
		radius = kpts[i].size / 2.0;
		cv::circle(img, cv::Point(x, y), 2.5*radius, cv::Scalar(0, 255, 0), 1);
		cv::circle(img, cv::Point(x, y), 1.0, cv::Scalar(0, 0, 255), -1);
	}
}

// REF [site] >> https://github.com/pablofdezalc/test_kaze_akaze_opencv/blob/master/src/utils.cpp
cv::Mat read_homography(const std::string& homography_path)
{
	float h11 = 0.0, h12 = 0.0, h13 = 0.0;
	float h21 = 0.0, h22 = 0.0, h23 = 0.0;
	float h31 = 0.0, h32 = 0.0, h33 = 0.0;
	const int tmp_buf_size = 256;
	char tmp_buf[tmp_buf_size];

	// Allocate memory for the OpenCV matrices.
	cv::Mat H1toN(cv::Mat::zeros(3, 3, CV_32FC1));

	std::ifstream infile;
	infile.exceptions(std::ifstream::eofbit | std::ifstream::failbit | std::ifstream::badbit);
	infile.open(homography_path.c_str(), std::ifstream::in);

	infile.getline(tmp_buf, tmp_buf_size);
	sscanf(tmp_buf, "%f %f %f", &h11, &h12, &h13);

	infile.getline(tmp_buf, tmp_buf_size);
	sscanf(tmp_buf, "%f %f %f", &h21, &h22, &h23);

	infile.getline(tmp_buf, tmp_buf_size);
	sscanf(tmp_buf, "%f %f %f", &h31, &h32, &h33);

	infile.close();

	H1toN.at<float>(0, 0) = h11 / h33;
	H1toN.at<float>(0, 1) = h12 / h33;
	H1toN.at<float>(0, 2) = h13 / h33;

	H1toN.at<float>(1, 0) = h21 / h33;
	H1toN.at<float>(1, 1) = h22 / h33;
	H1toN.at<float>(1, 2) = h23 / h33;

	H1toN.at<float>(2, 0) = h31 / h33;
	H1toN.at<float>(2, 1) = h32 / h33;
	H1toN.at<float>(2, 2) = h33 / h33;
	return H1toN;
}

// REF [site] >> https://github.com/pablofdezalc/test_kaze_akaze_opencv/blob/master/src/utils.cpp
void matches2points_nndr(const std::vector<cv::KeyPoint>& train, const std::vector<cv::KeyPoint>& query, const std::vector<std::vector<cv::DMatch> >& matches, std::vector<cv::Point2f>& pmatches, const float& nndr)
{
	float dist1 = 0.0, dist2 = 0.0;
	for (size_t i = 0; i < matches.size(); ++i)
	{
		const cv::DMatch &dmatch = matches[i][0];
		dist1 = matches[i][0].distance;
		dist2 = matches[i][1].distance;

		if (dist1 < nndr * dist2)
		{
			pmatches.push_back(train[dmatch.queryIdx].pt);
			pmatches.push_back(query[dmatch.trainIdx].pt);
		}
	}
}

// REF [site] >> https://github.com/pablofdezalc/test_kaze_akaze_opencv/blob/master/src/utils.cpp
void compute_inliers_homography(const std::vector<cv::Point2f>& matches, std::vector<cv::Point2f>& inliers, const cv::Mat& H, const float h_max_error)
{
	const float h11 = (float)H.at<double>(0, 0);
	const float h12 = (float)H.at<double>(0, 1);
	const float h13 = (float)H.at<double>(0, 2);
	const float h21 = (float)H.at<double>(1, 0);
	const float h22 = (float)H.at<double>(1, 1);
	const float h23 = (float)H.at<double>(1, 2);
	const float h31 = (float)H.at<double>(2, 0);
	const float h32 = (float)H.at<double>(2, 1);
	const float h33 = (float)H.at<double>(2, 2);

	inliers.clear();

	float x1 = 0.0, y1 = 0.0;
	float x2 = 0.0, y2 = 0.0;
	float x2m = 0.0, y2m = 0.0;
	float dist = 0.0, s = 0.0;
	for (size_t i = 0; i < matches.size(); i += 2)
	{
		x1 = matches[i].x;
		y1 = matches[i].y;
		x2 = matches[i + 1].x;
		y2 = matches[i + 1].y;

		s = h31*x1 + h32*y1 + h33;
		x2m = (h11*x1 + h12*y1 + h13) / s;
		y2m = (h21*x1 + h22*y1 + h23) / s;
		dist = std::sqrt(std::pow(x2m - x2, 2) + std::pow(y2m - y2, 2));

		if (dist <= h_max_error)
		{
			inliers.push_back(matches[i]);
			inliers.push_back(matches[i + 1]);
		}
	}
}

// REF [site] >> https://github.com/pablofdezalc/test_kaze_akaze_opencv/blob/master/src/utils.cpp
void draw_inliers(const cv::Mat& img1, const cv::Mat& imgN, cv::Mat& img_com, const std::vector<cv::Point2f>& ptpairs)
{
	int x1 = 0, y1 = 0, xN = 0, yN = 0;
	float rows1 = 0.0, cols1 = 0.0;
	float rowsN = 0.0, colsN = 0.0;
	float ufactor = 0.0, vfactor = 0.0;

	rows1 = img1.rows;
	cols1 = img1.cols;
	rowsN = imgN.rows;
	colsN = imgN.cols;
	ufactor = (float)(cols1) / (float)(colsN);
	vfactor = (float)(rows1) / (float)(rowsN);

	// This is in case the input images don't have the same resolution.
	cv::Mat img_aux(cv::Size(img1.cols, img1.rows), CV_8UC3);
	cv::resize(imgN, img_aux, cv::Size(img1.cols, img1.rows), 0, 0, cv::INTER_LINEAR);

	for (int i = 0; i < img_com.rows; ++i)
	{
		for (int j = 0; j < img_com.cols; ++j)
		{
			if (j < img1.cols)
			{
				*(img_com.ptr<unsigned char>(i) + 3 * j) = *(img1.ptr<unsigned char>(i) + 3 * j);
				*(img_com.ptr<unsigned char>(i) + 3 * j + 1) = *(img1.ptr<unsigned char>(i) + 3 * j + 1);
				*(img_com.ptr<unsigned char>(i) + 3 * j + 2) = *(img1.ptr<unsigned char>(i) + 3 * j + 2);
			}
			else
			{
				*(img_com.ptr<unsigned char>(i) + 3 * j) = *(imgN.ptr<unsigned char>(i) + 3 * (j - img_aux.cols));
				*(img_com.ptr<unsigned char>(i) + 3 * j + 1) = *(imgN.ptr<unsigned char>(i) + 3 * (j - img_aux.cols) + 1);
				*(img_com.ptr<unsigned char>(i) + 3 * j + 2) = *(imgN.ptr<unsigned char>(i) + 3 * (j - img_aux.cols) + 2);
			}
		}
	}

	for (size_t i = 0; i < ptpairs.size(); i += 2)
	{
		x1 = (int)(ptpairs[i].x + .5);
		y1 = (int)(ptpairs[i].y + .5);
		xN = (int)(ptpairs[i + 1].x*ufactor + img1.cols + .5);
		yN = (int)(ptpairs[i + 1].y*vfactor + .5);
		cv::line(img_com, cv::Point(x1, y1), cv::Point(xN, yN), cv::Scalar(255, 0, 0), 2);
	}
}

// REF [site] >> https://github.com/pablofdezalc/test_kaze_akaze_opencv/blob/master/test_kaze_match.cpp
// REF [site] >> https://github.com/pablofdezalc/test_kaze_akaze_opencv/blob/master/test_akaze_match.cpp
void kaze_match_test1()
{
	const std::string img1_filename("../data/machine_vision/opencv/graf1.png");
	const std::string imgN_filename("../data/machine_vision/opencv/graf3.png");
	const std::string H_filename("../data/machine_vision/opencv/H1to3p.xml");

	// Open the input image.
	cv::Mat img1(cv::imread(img1_filename, cv::IMREAD_COLOR));
	cv::Mat imgN(cv::imread(imgN_filename, cv::IMREAD_COLOR));
#if 0
	const cv::Mat H1toN(read_homography(H_filename));
#else
	cv::Mat H1toN;
	{
		cv::FileStorage fs(H_filename, cv::FileStorage::READ);
		if (fs.isOpened())
			fs.getFirstTopLevelNode() >> H1toN;  // CV_64FC1.
	}
#endif
	//std::cout << "H1toN = " << H1toN << std::endl;

	// Nearest neighbor distance ratio (NNDR).
	//	NNDR = d1 / d2.
	//		d1, d2: distances to the nearest and 2nd nearest neighbors.
	//	If NNDR is small, nearest neighbor is a good match.
	const float nndr = 0.8f;
	const float max_h_error = 2.5f;

	// Create KAZE/AKAZE object.
	//cv::Ptr<cv::Feature2D> dkaze(cv::KAZE::create());
	cv::Ptr<cv::Feature2D> dkaze(cv::AKAZE::create());

	// Timing information.
	double t1 = 0.0, t2 = 0.0;
	double tkaze = 0.0, tmatch = 0.0;

	// Detect KAZE/AKAZE features in the images.
	std::vector<cv::KeyPoint> keypoints1, keypointsN;
	cv::Mat descriptors1, descriptorsN;

	t1 = cv::getTickCount();
	dkaze->detectAndCompute(img1, cv::noArray(), keypoints1, descriptors1);
	dkaze->detectAndCompute(imgN, cv::noArray(), keypointsN, descriptorsN);
	t2 = cv::getTickCount();
	tkaze = 1000.0 * (t2 - t1) / cv::getTickFrequency();

	const int nr_kpts1 = keypoints1.size();
	const int nr_kptsN = keypointsN.size();

	// Match the descriptors using NNDR matching strategy.
	std::vector<std::vector<cv::DMatch> > dmatches;
	std::vector<cv::Point2f> matches, inliers;
	//cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create("BruteForce"));  // For KAZE.
	cv::Ptr<cv::DescriptorMatcher> matcher(cv::DescriptorMatcher::create("BruteForce-Hamming"));  // For AKAZE.

	t1 = cv::getTickCount();
	matcher->knnMatch(descriptors1, descriptorsN, dmatches, 2);
	matches2points_nndr(keypoints1, keypointsN, dmatches, matches, nndr);
	t2 = cv::getTickCount();
	tmatch = 1000.0 * (t2 - t1) / cv::getTickFrequency();

	// Compute the inliers using the ground truth homography.
	compute_inliers_homography(matches, inliers, H1toN, max_h_error);

	// Compute the inliers statistics.
	const int nr_matches = matches.size() / 2;
	const int nr_inliers = inliers.size() / 2;
	const int nr_outliers = nr_matches - nr_inliers;
	const float ratio = 100.0f * ((float)nr_inliers / (float)nr_matches);

	std::cout << "KAZE/AKAZE Matching Results" << std::endl;
	std::cout << "*******************************" << std::endl;
	std::cout << "# Keypoints 1:                        \t" << nr_kpts1 << std::endl;
	std::cout << "# Keypoints N:                        \t" << nr_kptsN << std::endl;
	std::cout << "# Matches:                            \t" << nr_matches << std::endl;
	std::cout << "# Inliers:                            \t" << nr_inliers << std::endl;
	std::cout << "# Outliers:                           \t" << nr_outliers << std::endl;
	std::cout << "Inliers Ratio (%):                    \t" << ratio << std::endl;
	std::cout << "Time Detection+Description (ms):      \t" << tkaze << std::endl;
	std::cout << "Time Matching (ms):                   \t" << tmatch << std::endl;
	std::cout << std::endl;

	// Visualization.
	cv::Mat img_com(cv::Size(2 * img1.cols, img1.rows), CV_8UC3);
	draw_keypoints(img1, keypoints1);
	draw_keypoints(imgN, keypointsN);
	draw_inliers(img1, imgN, img_com, inliers);

	cv::imshow("KAZE/AKAZE Matching", img_com);
	cv::waitKey(0);
}

// REF [site] >> https://docs.opencv.org/master/db/d70/tutorial_akaze_matching.html
void kaze_match_test2()
{
	const std::string img1_filename("../data/machine_vision/opencv/graf1.png");
	const std::string imgN_filename("../data/machine_vision/opencv/graf3.png");
	const std::string H_filename("../data/machine_vision/opencv/H1to3p.xml");

	// Open the input image.
	cv::Mat img1(cv::imread(img1_filename, cv::IMREAD_COLOR));
	cv::Mat imgN(cv::imread(imgN_filename, cv::IMREAD_COLOR));
	cv::Mat H1toN;
	{
		cv::FileStorage fs(H_filename, cv::FileStorage::READ);
		if (fs.isOpened())
			fs.getFirstTopLevelNode() >> H1toN;  // CV_64FC1.
	}
	//std::cout << "H1toN = " << H1toN << std::endl;

	const float inlier_threshold = 2.5f;  // Distance threshold to identify inliers.
	const float nn_match_ratio = 0.8f;  // Nearest neighbor matching ratio.

	std::vector<cv::KeyPoint> keypoints1, keypointsN;
	cv::Mat descriptors1, descriptorsN;

	//cv::Ptr<cv::KAZE> kaze(cv::KAZE::create());
	cv::Ptr<cv::AKAZE> akaze(cv::AKAZE::create());
	akaze->detectAndCompute(img1, cv::noArray(), keypoints1, descriptors1);
	akaze->detectAndCompute(imgN, cv::noArray(), keypointsN, descriptorsN);

	//cv::BFMatcher matcher;  // For KAZE. (?)
	cv::BFMatcher matcher(cv::NORM_HAMMING);  // For AKAZE.
	std::vector<std::vector<cv::DMatch> > nn_matches;
	matcher.knnMatch(descriptors1, descriptorsN, nn_matches, 2);

	std::vector<cv::KeyPoint> matched1, matchedN, inliers1, inliersN;
	std::vector<cv::DMatch> good_matches;
	for (size_t i = 0; i < nn_matches.size(); ++i)
	{
		const cv::DMatch &first = nn_matches[i][0];
		const float dist1 = nn_matches[i][0].distance;
		const float dist2 = nn_matches[i][1].distance;

		if (dist1 < nn_match_ratio * dist2)
		{
			matched1.push_back(keypoints1[first.queryIdx]);
			matchedN.push_back(keypointsN[first.trainIdx]);
		}
	}

	for (unsigned i = 0; i < matched1.size(); ++i)
	{
		cv::Mat col = cv::Mat::ones(3, 1, CV_64F);
		col.at<double>(0) = matched1[i].pt.x;
		col.at<double>(1) = matched1[i].pt.y;

		col = H1toN * col;
		col /= col.at<double>(2);
		const double dist = std::sqrt(std::pow(col.at<double>(0) - matchedN[i].pt.x, 2) + std::pow(col.at<double>(1) - matchedN[i].pt.y, 2));

		if (dist < inlier_threshold)
		{
			const int new_i = static_cast<int>(inliers1.size());
			inliers1.push_back(matched1[i]);
			inliersN.push_back(matchedN[i]);
			good_matches.push_back(cv::DMatch(new_i, new_i, 0));
		}
	}

	cv::Mat res;
	cv::drawMatches(img1, inliers1, imgN, inliersN, good_matches, res);
	//cv::imwrite("akaze_result.png", res);

	const double inlier_ratio = inliers1.size() * 1.0 / matched1.size();
	std::cout << "KAZE/AKAZE Matching Results" << std::endl;
	std::cout << "*******************************" << std::endl;
	std::cout << "# Keypoints 1:                        \t" << keypoints1.size() << std::endl;
	std::cout << "# Keypoints 2:                        \t" << keypointsN.size() << std::endl;
	std::cout << "# Matches:                            \t" << matched1.size() << std::endl;
	std::cout << "# Inliers:                            \t" << inliers1.size() << std::endl;
	std::cout << "# Inliers Ratio:                      \t" << inlier_ratio << std::endl;
	std::cout << std::endl;

	cv::imshow("KAZE/AKAZE Matching", res);
	cv::waitKey();
}

}  // namespace local
}  // unnamed namespace

namespace my_opencv {

void feature_extraction_and_matching()
{
	//local::feature_extraction_and_matching();

	//local::kaze_match_test1();
	local::kaze_match_test2();
}

}  // namespace my_opencv
