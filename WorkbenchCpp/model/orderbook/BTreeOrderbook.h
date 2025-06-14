#ifndef MODEL_ORDERBOOK_BTREEORDERBOOK_H
#define MODEL_ORDERBOOK_BTREEORDERBOOK_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct Order {
    int64_t timestamp;
    double price;
    double qty;
    std::string side;
};

#endif // MODEL_ORDERBOOK_BTREEORDERBOOK_H
