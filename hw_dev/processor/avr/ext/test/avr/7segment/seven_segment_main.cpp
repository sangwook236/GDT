#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdint.h>


namespace {
namespace local {

void system_init()
{
	/*
	 *	analog comparator
	 */
	ACSR &= ~(_BV(ACIE));  // analog comparator interrupt disable
	ACSR |= _BV(ACD);  // analog comparator disable

	/*
	 *	I/O port
	 */
	// uses all pins on PortA & PortC for output
	DDRA = 0xFF;
	DDRC = 0xFF;
}

}  // namespace local
}  // unnamed namespace

int seven_segment_main(int argc, char *argv[])
{
	void four_digit_seven_segment_anode_commmon(const uint16_t four_digits);
	void four_digit_seven_segment_cathode_commmon(const uint16_t four_digits);

	cli();
	local::system_init();
	sei();

	const uint16_t num1 = 1234;
	const uint16_t num2 = 5678;
	uint16_t num = num1;
	uint16_t i = 0;
	while (1)
	{
		//four_digit_seven_segment_anode_commmon(num);
		four_digit_seven_segment_cathode_commmon(num);

		i = (i + 1) % 100;
		if (0 == i)
			num = (num1 == num) ? num2 : num1;
	}

	return 0;
}
