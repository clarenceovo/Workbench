#include "TimeUtil.h"
#include <iostream>
#include <iomanip>

namespace TimeUtil {

using namespace std::chrono;

void printNow() {
    auto now = system_clock::now();
    std::time_t tt = system_clock::to_time_t(now);
    std::cout << std::put_time(std::localtime(&tt), "%Y-%m-%d %H:%M:%S") << std::endl;
}

void printNowUTC() {
    auto now = system_clock::now();
    std::time_t tt = system_clock::to_time_t(now);
    std::cout << std::put_time(std::gmtime(&tt), "%Y-%m-%d %H:%M:%S") << std::endl;
}

system_clock::time_point getNow() {
    return system_clock::now();
}

system_clock::time_point getNowUTC() {
    return system_clock::now();
}

double getTimestamp() {
    return duration<double>(system_clock::now().time_since_epoch()).count();
}

std::string getNowUTCString() {
    auto now = system_clock::now();
    std::time_t tt = system_clock::to_time_t(now);
    char buf[20];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::gmtime(&tt));
    return buf;
}

std::string getNowHKTString() {
    auto now = system_clock::now();
    std::time_t tt = system_clock::to_time_t(now + hours(8));
    char buf[20];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::gmtime(&tt));
    return buf;
}

std::string getNowUTCDate() {
    auto now = system_clock::now();
    std::time_t tt = system_clock::to_time_t(now);
    char buf[11];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d", std::gmtime(&tt));
    return buf;
}

std::string getUTCDate(int backwardDays) {
    auto now = system_clock::now() - hours(24 * backwardDays);
    std::time_t tt = system_clock::to_time_t(now);
    char buf[11];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d", std::gmtime(&tt));
    return buf;
}

long long getUTCNowMs() {
    return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

long long getHKTNowMs() {
    return duration_cast<milliseconds>((system_clock::now() + hours(8)).time_since_epoch()).count();
}

long long getLatencyMs(long long eventTs) {
    return eventTs - getUTCNowMs();
}

long long getUTCTsNs() {
    return duration_cast<nanoseconds>(system_clock::now().time_since_epoch()).count();
}

long long msToNs(long long ms) {
    return ms * 1'000'000;
}

} // namespace TimeUtil

