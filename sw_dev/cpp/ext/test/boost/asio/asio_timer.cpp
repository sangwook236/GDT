#include <boost/asio.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/bind.hpp>
#include <iostream>


namespace {
namespace local {

void print(const boost::system::error_code & /*e*/, boost::asio::deadline_timer *timer, int *count)
{
	if (*count < 5)
	{
		std::cout << *count << std::endl;
		++(*count);

        //timer->expires_from_now(boost::posix_time::seconds(1));
		timer->expires_at(timer->expires_at() + boost::posix_time::seconds(1));
		timer->async_wait(boost::bind(print, boost::asio::placeholders::error, timer, count));
	}
}

void asio_async_timer()
{
	boost::asio::io_service ioService;
	boost::asio::deadline_timer timer(ioService, boost::posix_time::seconds(1));

	int count = 0;
	timer.async_wait(boost::bind(print, boost::asio::placeholders::error, &timer, &count));

	ioService.run();

	std::cout << "Final count is " << count << std::endl;
	std::cout << "io_service is terminated" << std::endl;
}

void asio_sync_timer()
{
	boost::asio::io_service ioService;
	boost::asio::deadline_timer timer(ioService, boost::posix_time::seconds(3));

	timer.wait();

	std::cout << "3 secs are elapsed !!!" << std::endl;
}

}  // namespace local
}  // unnamed namespace

void asio_timer()
{
	local::asio_async_timer();
	local::asio_sync_timer();
}
