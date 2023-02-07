//#include "stdafx.h"
#include <cmath>
#include <random>
#include <vector>
#include <map>
#include <iostream>
#include <fstream>
#include <glog/logging.h>
#include <gflags/gflags.h>
#include <ceres/ceres.h>
#include <ceres/dynamic_autodiff_cost_function.h>
// REF [file] >> https://github.com/ceres-solver/ceres-solver/blob/master/examples/slam/common/read_g2o.h
#include "read_g2o.h"


namespace {
namespace local {

// g2o_simulator3d can be used to generate g2o files.
//	g2o_simulator3d -hasPoseSensor simulator3d_out.g2o
DEFINE_string(input, "../simulator3d_out.g2o", "The pose graph definition filename in g2o format.");

struct Pose3d
{
	Eigen::Vector3d p;
	Eigen::Quaterniond q;

	// The name of the data type in the g2o file format.
	static std::string name() { return "VERTEX_SE3:QUAT"; }

	EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

inline std::istream& operator>>(std::istream& input, Pose3d& pose)
{
	input >> pose.p.x() >> pose.p.y() >> pose.p.z() >> pose.q.x() >> pose.q.y() >> pose.q.z() >> pose.q.w();
	// Normalize the quaternion to account for precision loss due to serialization.
	pose.q.normalize();
	return input;
}

using MapOfPoses = std::map<int, Pose3d, std::less<int>, Eigen::aligned_allocator<std::pair<const int, Pose3d>>>;

// The constraint between two vertices in the pose graph. The constraint is the
// transformation from vertex id_begin to vertex id_end.
struct Constraint3d
{
	int id_begin;
	int id_end;

	// The transformation that represents the pose of the end frame E w.r.t. the
	// begin frame B. In other words, it transforms a vector in the E frame to
	// the B frame.
	Pose3d t_be;

	// The inverse of the covariance matrix for the measurement. The order of the
	// entries are x, y, z, delta orientation.
	Eigen::Matrix<double, 6, 6> information;

	// The name of the data type in the g2o file format.
	static std::string name() { return "EDGE_SE3:QUAT"; }

	EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

inline std::istream& operator>>(std::istream& input, Constraint3d& constraint)
{
	Pose3d& t_be = constraint.t_be;
	input >> constraint.id_begin >> constraint.id_end >> t_be;

	for (int i = 0; i < 6 && input.good(); ++i)
	{
		for (int j = i; j < 6 && input.good(); ++j)
		{
			input >> constraint.information(i, j);
			if (i != j)
			{
				constraint.information(j, i) = constraint.information(i, j);
			}
		}
	}
	return input;
}

using VectorOfConstraints = std::vector<Constraint3d, Eigen::aligned_allocator<Constraint3d>>;

// Computes the error term for two poses that have a relative pose measurement
// between them. Let the hat variables be the measurement. We have two poses x_a
// and x_b. Through sensor measurements we can measure the transformation of
// frame B w.r.t frame A denoted as t_ab_hat. We can compute an error metric
// between the current estimate of the poses and the measurement.
//
// In this formulation, we have chosen to represent the rigid transformation as
// a Hamiltonian quaternion, q, and position, p. The quaternion ordering is
// [x, y, z, w].

// The estimated measurement is:
//      t_ab = [ p_ab ]  = [ R(q_a)^T * (p_b - p_a) ]
//             [ q_ab ]    [ q_a^{-1] * q_b         ]
//
// where ^{-1} denotes the inverse and R(q) is the rotation matrix for the
// quaternion. Now we can compute an error metric between the estimated and
// measurement transformation. For the orientation error, we will use the
// standard multiplicative error resulting in:
//
//   error = [ p_ab - \hat{p}_ab                 ]
//           [ 2.0 * Vec(q_ab * \hat{q}_ab^{-1}) ]
//
// where Vec(*) returns the vector (imaginary) part of the quaternion. Since
// the measurement has an uncertainty associated with how accurate it is, we
// will weight the errors by the square root of the measurement information
// matrix:
//
//   residuals = I^{1/2) * error
// where I is the information matrix which is the inverse of the covariance.
class PoseGraph3dErrorTerm
{
public:
	PoseGraph3dErrorTerm(Pose3d t_ab_measured, Eigen::Matrix<double, 6, 6> sqrt_information)
	: t_ab_measured_(std::move(t_ab_measured)), sqrt_information_(std::move(sqrt_information))
	{}

	template <typename T>
	bool operator()(const T* const p_a_ptr, const T* const q_a_ptr, const T* const p_b_ptr, const T* const q_b_ptr, T* residuals_ptr) const
	{
		Eigen::Map<const Eigen::Matrix<T, 3, 1>> p_a(p_a_ptr);
		Eigen::Map<const Eigen::Quaternion<T>> q_a(q_a_ptr);

		Eigen::Map<const Eigen::Matrix<T, 3, 1>> p_b(p_b_ptr);
		Eigen::Map<const Eigen::Quaternion<T>> q_b(q_b_ptr);

		// Compute the relative transformation between the two frames.
		Eigen::Quaternion<T> q_a_inverse = q_a.conjugate();
		Eigen::Quaternion<T> q_ab_estimated = q_a_inverse * q_b;

		// Represent the displacement between the two frames in the A frame.
		Eigen::Matrix<T, 3, 1> p_ab_estimated = q_a_inverse * (p_b - p_a);

		// Compute the error between the two orientation estimates.
		Eigen::Quaternion<T> delta_q = t_ab_measured_.q.template cast<T>() * q_ab_estimated.conjugate();

		// Compute the residuals.
		// [ position         ]   [ delta_p          ]
		// [ orientation (3x1)] = [ 2 * delta_q(0:2) ]
		Eigen::Map<Eigen::Matrix<T, 6, 1>> residuals(residuals_ptr);
		residuals.template block<3, 1>(0, 0) = p_ab_estimated - t_ab_measured_.p.template cast<T>();
		residuals.template block<3, 1>(3, 0) = T(2.0) * delta_q.vec();

		// Scale the residuals by the measurement uncertainty.
		residuals.applyOnTheLeft(sqrt_information_.template cast<T>());

		return true;
	}

	static ceres::CostFunction* Create(const Pose3d& t_ab_measured, const Eigen::Matrix<double, 6, 6>& sqrt_information) 
	{
		return new ceres::AutoDiffCostFunction<PoseGraph3dErrorTerm, 6, 3, 4, 3, 4>(new PoseGraph3dErrorTerm(t_ab_measured, sqrt_information));
	}

	EIGEN_MAKE_ALIGNED_OPERATOR_NEW

private:
	// The measurement for the position of B relative to A in the A frame.
	const Pose3d t_ab_measured_;
	// The square root of the measurement information matrix.
	const Eigen::Matrix<double, 6, 6> sqrt_information_;
};

// Constructs the nonlinear least squares optimization problem from the pose graph constraints.
void BuildOptimizationProblem(const VectorOfConstraints& constraints, MapOfPoses* poses, ceres::Problem* problem)
{
	CHECK(poses != nullptr);
	CHECK(problem != nullptr);
	if (constraints.empty())
	{
		LOG(INFO) << "No constraints, no problem to optimize.";
		return;
	}

	ceres::LossFunction* loss_function = nullptr;
	ceres::Manifold* quaternion_manifold = new ceres::EigenQuaternionManifold;

	for (const auto& constraint : constraints)
	{
		auto pose_begin_iter = poses->find(constraint.id_begin);
		CHECK(pose_begin_iter != poses->end())
			<< "Pose with ID: " << constraint.id_begin << " not found.";
		auto pose_end_iter = poses->find(constraint.id_end);
		CHECK(pose_end_iter != poses->end())
			<< "Pose with ID: " << constraint.id_end << " not found.";

		const Eigen::Matrix<double, 6, 6> sqrt_information = constraint.information.llt().matrixL();
		// Ceres will take ownership of the pointer.
		ceres::CostFunction* cost_function = PoseGraph3dErrorTerm::Create(constraint.t_be, sqrt_information);

		problem->AddResidualBlock(
			cost_function,
			loss_function,
			pose_begin_iter->second.p.data(),
			pose_begin_iter->second.q.coeffs().data(),
			pose_end_iter->second.p.data(),
			pose_end_iter->second.q.coeffs().data()
		);

		problem->SetManifold(pose_begin_iter->second.q.coeffs().data(), quaternion_manifold);
		problem->SetManifold(pose_end_iter->second.q.coeffs().data(), quaternion_manifold);
	}

	// The pose graph optimization problem has six DOFs that are not fully
	// constrained. This is typically referred to as gauge freedom. You can apply
	// a rigid body transformation to all the nodes and the optimization problem
	// will still have the exact same cost. The Levenberg-Marquardt algorithm has
	// internal damping which mitigates this issue, but it is better to properly
	// constrain the gauge freedom. This can be done by setting one of the poses
	// as constant so the optimizer cannot change it.
	auto pose_start_iter = poses->begin();
	CHECK(pose_start_iter != poses->end()) << "There are no poses.";
	problem->SetParameterBlockConstant(pose_start_iter->second.p.data());
	problem->SetParameterBlockConstant(pose_start_iter->second.q.coeffs().data());
}

// Returns true if the solve was successful.
bool SolveOptimizationProblem(ceres::Problem* problem)
{
	CHECK(problem != nullptr);

	ceres::Solver::Options options;
	options.max_num_iterations = 200;
	options.linear_solver_type = ceres::SPARSE_NORMAL_CHOLESKY;

	ceres::Solver::Summary summary;
	ceres::Solve(options, problem, &summary);

	std::cout << summary.FullReport() << std::endl;

	return summary.IsSolutionUsable();
}

// Output the poses to the file with format: id x y z q_x q_y q_z q_w.
bool OutputPoses(const std::string& filename, const MapOfPoses& poses)
{
	std::fstream outfile;
	outfile.open(filename.c_str(), std::istream::out);
	if (!outfile)
	{
		LOG(ERROR) << "Error opening the file: " << filename;
		return false;
	}
	for (const auto& pair : poses)
	{
		outfile << pair.first << " " << pair.second.p.transpose() << " "
			<< pair.second.q.x() << " " << pair.second.q.y() << " "
			<< pair.second.q.z() << " " << pair.second.q.w() << std::endl;
	}
	return true;
}

}  // namespace local
}  // unnamed namespace

namespace my_ceres_solver {

// REF [site] >> https://github.com/ceres-solver/ceres-solver/blob/master/examples/slam/pose_graph_3d
void pose_graph_3d_example()
{
	CHECK(local::FLAGS_input != "") << "Need to specify the filename to read.";

	local::MapOfPoses poses;
	local::VectorOfConstraints constraints;

	CHECK(ceres::examples::ReadG2oFile(local::FLAGS_input, &poses, &constraints))
		<< "Error reading the file: " << local::FLAGS_input;

	std::cout << "Number of poses: " << poses.size() << std::endl;
	std::cout << "Number of constraints: " << constraints.size() << std::endl;

	CHECK(local::OutputPoses("./poses_original.txt", poses))
		<< "Error outputting to poses_original.txt";

	ceres::Problem problem;
	local::BuildOptimizationProblem(constraints, &poses, &problem);

	CHECK(local::SolveOptimizationProblem(&problem))
		<< "The solve was not successful, exiting.";

	CHECK(local::OutputPoses("./poses_optimized.txt", poses))
		<< "Error outputting to poses_original.txt";
}

}  // namespace my_ceres_solver
