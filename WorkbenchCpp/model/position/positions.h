#ifndef MODEL_POSITION_POSITIONS_H
#define MODEL_POSITION_POSITIONS_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct Position {
    std::string exchange;
    std::string symbol;
    double quantity;
    double notional;
    double entryPrice;
    double markPrice;
    int64_t lastUpdate_ts;
    std::string order_type;
    std::string direction;
    double contract_size;
};

#endif // MODEL_POSITION_POSITIONS_H
