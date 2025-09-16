#include "SwapArbStrategyBot.h"
#include "TimeUtil.h"
#include <iostream>
#include <chrono>
#include <thread>

SwapArbStrategyBot::SwapArbStrategyBot(const std::string &botId)
    : botId_(botId) {}

void SwapArbStrategyBot::initBot() {
    std::cout << "Initializing SwapArbStrategyBot with ID: " << botId_ << "\n";
    subscribeMarketData();
    positionThread_ = std::thread(&SwapArbStrategyBot::publishPosition, this);
}

void SwapArbStrategyBot::sendMessage(const std::string &msg) {
    std::cout << "[MSG] " << msg << "\n";
}

void SwapArbStrategyBot::subscribeMarketData() {
    std::cout << "Subscribing to market data...\n";
}

void SwapArbStrategyBot::publishPosition() {
    for (int i = 0; i < 3 && isActive_; ++i) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
        std::lock_guard<std::mutex> guard(entryLock_);
        std::cout << "Publishing positions at " << TimeUtil::getNowUTCString() << "\n";
    }
}

void SwapArbStrategyBot::checkPositionUnwind() {
    // Stubbed method
}

void SwapArbStrategyBot::cal() {
    // Stubbed calculation logic
}

void SwapArbStrategyBot::checkConnection() {
    // Stubbed connection check logic
}

void SwapArbStrategyBot::run() {
    initBot();
    for (int i = 0; i < 3; ++i) {
        cal();
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    isActive_ = false;
    if (positionThread_.joinable()) {
        positionThread_.join();
    }
}
