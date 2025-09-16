#ifndef MODEL_DTO_OPENINTEREST_H
#define MODEL_DTO_OPENINTEREST_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct OpenInterest {
    std::chrono::system_clock::time_point timestamp;
    std::string exchange;
    std::string symbol;
    double open_interest;
};

#endif // MODEL_DTO_OPENINTEREST_H
