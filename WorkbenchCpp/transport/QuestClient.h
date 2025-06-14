#ifndef TRANSPORT_QUESTCLIENT_H
#define TRANSPORT_QUESTCLIENT_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct QuestBatch {
    std::string topic;
    std::string symbol;
    std::string columns;
    std::chrono::system_clock::time_point timestamp;
};

#endif // TRANSPORT_QUESTCLIENT_H
