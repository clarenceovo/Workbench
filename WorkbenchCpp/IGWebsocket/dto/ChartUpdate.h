#ifndef IGWEBSOCKET_DTO_CHARTUPDATE_H
#define IGWEBSOCKET_DTO_CHARTUPDATE_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct ChartUpdate {
    std::string topic;
    int64_t utm;
    double day_open_mid;
    double day_net_chg_mid;
    double day_perc_chg_mid;
    double day_high;
    double day_low;
    double ofr_open;
    double ofr_high;
    double ofr_low;
    double ofr_close;
    double bid_open;
    double bid_high;
    double bid_low;
    double bid_close;
    std::chrono::system_clock::time_point time;
    double current_mid;
    double bid_to_mid;
    double ask_to_mid;
};

#endif // IGWEBSOCKET_DTO_CHARTUPDATE_H
