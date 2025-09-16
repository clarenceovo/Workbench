#ifndef TIME_UTIL_H
#define TIME_UTIL_H

#include <chrono>
#include <string>

namespace TimeUtil {

void printNow();
void printNowUTC();
std::chrono::system_clock::time_point getNow();
std::chrono::system_clock::time_point getNowUTC();
double getTimestamp();
std::string getNowUTCString();
std::string getNowHKTString();
std::string getNowUTCDate();
std::string getUTCDate(int backwardDays = 0);
long long getUTCNowMs();
long long getHKTNowMs();
long long getLatencyMs(long long eventTs);
long long getUTCTsNs();
long long msToNs(long long ms);

}

#endif // TIME_UTIL_H
