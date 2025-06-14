#ifndef MODEL_ORDER_ORDER_H
#define MODEL_ORDER_ORDER_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct Order {
    std::string exchange;
    std::string symbol;
    double quantity;
    std::string order_type;
    std::string direction;
    int64_t deal_ts;
    double price;
    bool is_completed;
    bool is_market_order;
    std::string client_order_id;
    std::string order_ref_id;
    bool reduce_only;
    bool is_close_order;
};

#endif // MODEL_ORDER_ORDER_H
