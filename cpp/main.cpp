#include "TimeUtil.h"
#include "SwapArbStrategyBot.h"
#include <iostream>
#include <thread>
#include <chrono>

int main() {
    TimeUtil::printNow();
    std::cout << "Starting example bot...\n";
    SwapArbStrategyBot bot("EXAMPLE");
    std::thread t([&bot](){ bot.run(); });
    std::this_thread::sleep_for(std::chrono::seconds(1));
    if (t.joinable()) t.join();
    return 0;
}
