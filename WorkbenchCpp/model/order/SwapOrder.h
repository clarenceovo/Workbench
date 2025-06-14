#ifndef MODEL_ORDER_SWAPORDER_H
#define MODEL_ORDER_SWAPORDER_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct SwapOrder {
    std::string exchange;
    std::string symbol;
    std::string long_leg;
    std::string short_leg;
    double long_price;
    double short_price;
};

#endif // MODEL_ORDER_SWAPORDER_H
