//#include "stdafx.h"
#include <mrpt/math/dijkstra.h>
#include <mrpt/poses/CNetworkOfPoses.h>
#include <mrpt/gui/CDisplayWindowPlots.h>
#include <mrpt/utils/CTicTac.h>
#include <mrpt/random.h>
#include <string>
#include <vector>


namespace {
namespace local {

// The type of my Dijkstra problem:
typedef mrpt::math::CDijkstra<mrpt::poses::CNetworkOfPoses2D> my_Dijkstra_type;   // See other options in mrpt::graphs::CNetworkOfPoses<>

// adds a new edge to the graph. The edge is annotated with the relative position of the two nodes
void add_edge(mrpt::utils::TNodeID from, mrpt::utils::TNodeID to, const mrpt::aligned_containers<mrpt::utils::TNodeID, mrpt::poses::CPose2D>::map_t &real_poses, mrpt::graphs::CNetworkOfPoses2D &graph_links)
{
	const mrpt::poses::CPose2D p = real_poses.find(to)->second - real_poses.find(from)->second;
	graph_links.insertEdge(from, to, p);
}

// weight is the distance between two nodes.
double get_Dijkstra_weight(const my_Dijkstra_type::graph_t &g, const mrpt::utils::TNodeID from, const mrpt::utils::TNodeID to, const my_Dijkstra_type::edge_t &edge)
{
    //return 1;  // Topological distance.
	return edge.norm();  // Metric distance.
}

}  // namespace local
}  // unnamed namespace

namespace my_mrpt {

// REF [file] >> ${MRPT_HOME}/samples/dijkstra-example/test.cpp
void dijkstra()
{
	mrpt::utils::CTicTac tictac;
	mrpt::poses::CNetworkOfPoses2D graph_links;
	mrpt::poses::CNetworkOfPoses2D::global_poses_t optimal_poses, optimal_poses_dijkstra;
	mrpt::aligned_containers<mrpt::utils::TNodeID, mrpt::poses::CPose2D>::map_t real_poses;

	mrpt::random::randomGenerator.randomize(10);

	// create a random graph:
	const size_t N_VERTEX = 20;
	const double DIST_THRES = 10;
	const double NODES_XY_MAX = 15;

	std::vector<float> xs, ys;

	for (size_t j = 0; j < N_VERTEX; ++j)
	{
		mrpt::poses::CPose2D p(
			mrpt::random::randomGenerator.drawUniform(-NODES_XY_MAX, NODES_XY_MAX),
			mrpt::random::randomGenerator.drawUniform(-NODES_XY_MAX, NODES_XY_MAX),
			mrpt::random::randomGenerator.drawUniform(-M_PI, M_PI)
		);
		real_poses[j] = p;

		// for the figure:
		xs.push_back(p.x());
		ys.push_back(p.y());
	}

	// add some edges
	for (size_t i = 0; i < N_VERTEX; ++i)
	{
		for (size_t j = 0; j < N_VERTEX; ++j)
		{
			if (i == j) continue;
			if (real_poses[i].distanceTo(real_poses[j]) < DIST_THRES)
				local::add_edge(i, j, real_poses, graph_links);
		}
	}

	// Dijkstra
	tictac.Tic();
	const size_t SOURCE_NODE = 0;

	local::my_Dijkstra_type myDijkstra(
		graph_links,
		SOURCE_NODE,
		local::get_Dijkstra_weight
	);

	std::cout << "Dijkstra took " << tictac.Tac()*1e3 << " ms for " << graph_links.edges.size() << " edges." << std::endl;

	// Demo of getting the tree representation of the graph & visit its nodes.
	local::my_Dijkstra_type::tree_graph_t graph_as_tree;
	myDijkstra.getTreeGraph(graph_as_tree);

	// Text representation of the tree.
	std::cout << "TREE:\n" << graph_as_tree.getAsTextDescription() << std::endl;

	struct my_visitor_type : public local::my_Dijkstra_type::tree_graph_t::Visitor
	{
		/*virtual*/ void OnVisitNode(const mrpt::utils::TNodeID parent, const local::my_Dijkstra_type::tree_graph_t::TEdgeInfo &edge_to_child, const size_t depth_level)
		{
			std::cout << std::string(depth_level*3, ' ');
			std::cout << edge_to_child.id << std::endl;
		}
	};

	my_visitor_type myVisitor;

	std::cout << "Depth-first traverse of graph:\n";
	std::cout << SOURCE_NODE << std::endl;
	graph_as_tree.visitDepthFirst(SOURCE_NODE, myVisitor);

	std::cout << std::endl << "Breadth-first traverse of graph:\n";
	std::cout << SOURCE_NODE << std::endl;
	graph_as_tree.visitBreadthFirst(SOURCE_NODE, myVisitor);

	// display results graphically.
	mrpt::gui::CDisplayWindowPlots win("Dijkstra example");

	win.hold_on();
	win.axis_equal();

	for (mrpt::utils::TNodeID i = 0; i < N_VERTEX && win.isOpen(); ++i)
	{
		if (SOURCE_NODE == i) continue;

		local::my_Dijkstra_type::edge_list_t path;
		myDijkstra.getShortestPathTo(i, path);

		std::cout << "to " << i << " -> #steps= " << path.size() << std::endl;

        win.setWindowTitle(mrpt::format("Dijkstra path %u->%u", static_cast<unsigned int>(SOURCE_NODE), static_cast<unsigned int>(i)));

		win.clf();

		// plot all edges:
		for (mrpt::graphs::CNetworkOfPoses2D::iterator e = graph_links.begin(); e != graph_links.end(); ++e)
		{
			const mrpt::poses::CPose2D &p1 = real_poses[e->first.first];
			const mrpt::poses::CPose2D &p2 = real_poses[e->first.second];

			std::vector<float> X(2);
			std::vector<float> Y(2);
			X[0] = p1.x();  Y[0] = p1.y();
			X[1] = p2.x();  Y[1] = p2.y();
			win.plot(X, Y, "k1");
		}

		// draw the shortest path:
		for (local::my_Dijkstra_type::edge_list_t::const_iterator a = path.begin(); a != path.end(); ++a)
		{
			const mrpt::poses::CPose2D &p1 = real_poses[a->first];
			const mrpt::poses::CPose2D &p2 = real_poses[a->second];

			mrpt::vector_float X(2);
			mrpt::vector_float Y(2);
			X[0] = p1.x();  Y[0] = p1.y();
			X[1] = p2.x();  Y[1] = p2.y();
			win.plot(X, Y, "g3");
		}

		// draw All nodes:
		win.plot(xs, ys, ".b7");
		win.axis_fit(true);

        std::cout << "Press any key to show next shortest path, close window to end...";
        win.waitForKey();
	}

	win.clear();
}

}  // namespace my_mrpt
