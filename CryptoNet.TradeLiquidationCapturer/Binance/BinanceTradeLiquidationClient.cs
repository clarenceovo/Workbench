using CryptoNet.TradeLiquidationCapturer.Abstractions;
using CryptoNet.TradeLiquidationCapturer.Options;
using CryptoNet.TradeLiquidationCapturer.WebSockets;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace CryptoNet.TradeLiquidationCapturer.Binance;

internal sealed class BinanceTradeLiquidationClient : WebSocketTradeLiquidationClient, IBinanceTradeLiquidationClient
{
    public BinanceTradeLiquidationClient(IOptions<TradeLiquidationCapturerOptions> options, ILogger<BinanceTradeLiquidationClient> logger)
        : base(
            ResolveEndpoint(options, out var resolvedOptions),
            logger,
            resolvedOptions.ReceiveBufferSize,
            resolvedOptions.KeepAliveInterval,
            Normalize(resolvedOptions.BinanceSubscriptionMessage))
    {
    }

    public override string Exchange => "Binance";

    private static Uri ResolveEndpoint(IOptions<TradeLiquidationCapturerOptions>? options, out TradeLiquidationCapturerOptions resolved)
    {
        resolved = options?.Value ?? new TradeLiquidationCapturerOptions();
        resolved.EnsureValid();
        return resolved.BinanceEndpoint;
    }

    private static string? Normalize(string? message)
        => string.IsNullOrWhiteSpace(message) ? null : message;
}
