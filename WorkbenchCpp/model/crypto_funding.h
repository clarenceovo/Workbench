#ifndef MODEL_CRYPTO_FUNDING_H
#define MODEL_CRYPTO_FUNDING_H

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>

struct CryptoFunding {
    int64_t tickerId;
    std::chrono::system_clock::time_point fundingTime;
    double funding_rate;
    double mark_price;
};

#endif // MODEL_CRYPTO_FUNDING_H
