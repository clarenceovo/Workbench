#ifndef MODEL_CONFIG_SWAPARBCONFIG_H
#define MODEL_CONFIG_SWAPARBCONFIG_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct SwapArbConfig {
    bool is_trading;
    std::string exchange_a;
    std::string exchange_b;
    std::vector<std::string> exchange_a_market_list;
    std::vector<std::string> exchange_b_market_list;
    std::string long_leg_execution_mode;
    std::string short_leg_execution_mode;
    double upper_bound_entry_bp;
    double lower_bound_entry_bp;
    int64_t position_leverage;
    double exit_bp;
    double max_trade_size_usd;
    int64_t max_position;
    bool is_depth_check;
};

#endif // MODEL_CONFIG_SWAPARBCONFIG_H
