#ifndef MODEL_CRYPTO_TICKER_H
#define MODEL_CRYPTO_TICKER_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct TickerSeries {
};

struct CryptoTicker {
    int64_t tickerId;
    std::chrono::system_clock::time_point time;
    double open;
    double high;
    double low;
    double close;
    double volume;
    std::string series_type;
};

#endif // MODEL_CRYPTO_TICKER_H
