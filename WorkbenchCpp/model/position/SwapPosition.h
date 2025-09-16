#ifndef MODEL_POSITION_SWAPPOSITION_H
#define MODEL_POSITION_SWAPPOSITION_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct SwapPosition {
    std::string symbol;
    std::string long_leg;
    std::string short_leg;
};

#endif // MODEL_POSITION_SWAPPOSITION_H
