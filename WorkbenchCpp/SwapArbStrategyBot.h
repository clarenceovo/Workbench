#ifndef SWAP_ARB_STRATEGY_BOT_H
#define SWAP_ARB_STRATEGY_BOT_H

#include <string>
#include <thread>
#include <mutex>
#include <unordered_map>
#include <vector>

// This is a minimal C++ translation of Workbench/StrategyBot/SwapArbStrategyBot.py
// It is not a full implementation of the trading logic but mirrors the structure
// of the original Python class.

class SwapArbStrategyBot {
public:
    explicit SwapArbStrategyBot(const std::string &botId);

    void initBot();
    void sendMessage(const std::string &msg);

    // Public loop entry point
    void run();

private:
    void subscribeMarketData();
    void publishPosition();
    void checkPositionUnwind();
    void cal();
    void checkConnection();

    std::string botId_;
    bool isActive_ {true};
    std::thread positionThread_;
    std::mutex entryLock_;
    std::mutex unwindLock_;
    std::unordered_map<std::string, double> spreadBook_;
};

#endif // SWAP_ARB_STRATEGY_BOT_H
