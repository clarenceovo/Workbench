#ifndef MODEL_DTO_FUNDINGRATE_H
#define MODEL_DTO_FUNDINGRATE_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct FundingRate {
    int64_t timestamp;
    std::string exchange;
    std::string symbol;
    double annual_funding_rate;
};

#endif // MODEL_DTO_FUNDINGRATE_H
