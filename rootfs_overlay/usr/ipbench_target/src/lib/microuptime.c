#include "ipbench.h"
#include "util.h"
#include "microuptime.h"

double tick_rate;

static void
selectsleep(unsigned us) {
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = us;

        select(0,0,0,0,&tv);
}

void
microuptime_calibrate(void)
{
	double sumx = 0;
	double sumy = 0;
	double sumxx = 0;
	double sumxy = 0;
	double slope;
	clk_t start;
	clk_t now;

	// least squares linear regression of ticks onto real time
	// as returned by gettimeofday.

	dbprintf("Begin microuptime calibration\n");
  
	const unsigned n = 50;
	unsigned i;
  
	for (i = 0; i < n; i++) {
		double real,ticks,sleeptime, ran;
    
		ran = drand48();
		sleeptime = (100000 + ran * 200000);

		now = real_time();
		start = time_stamp();

		selectsleep((unsigned int) sleeptime);

		ticks = time_stamp() - start;
		real = real_time() - now;

		sumx += real;
		sumxx += real * real;
		sumxy += real * ticks;
		sumy += ticks;
	}
	slope = ((sumxy - (sumx*sumy) / n) /
		 (sumxx - (sumx*sumx) / n));
	tick_rate = slope;

	dbprintf("... done\n");
}
