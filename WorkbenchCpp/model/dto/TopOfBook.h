#ifndef MODEL_DTO_TOPOFBOOK_H
#define MODEL_DTO_TOPOFBOOK_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct TopOfBook {
    int64_t timestamp;
    std::string exchange;
    std::string symbol;
    double bid_price;
    double bid_qty;
    double ask_price;
    double ask_qty;
};

#endif // MODEL_DTO_TOPOFBOOK_H
