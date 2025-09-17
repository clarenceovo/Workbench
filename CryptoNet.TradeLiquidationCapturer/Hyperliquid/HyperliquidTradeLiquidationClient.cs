using CryptoNet.TradeLiquidationCapturer.Abstractions;
using CryptoNet.TradeLiquidationCapturer.Options;
using CryptoNet.TradeLiquidationCapturer.WebSockets;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace CryptoNet.TradeLiquidationCapturer.Hyperliquid;

internal sealed class HyperliquidTradeLiquidationClient : WebSocketTradeLiquidationClient, IHyperliquidTradeLiquidationClient
{
    public HyperliquidTradeLiquidationClient(IOptions<TradeLiquidationCapturerOptions> options, ILogger<HyperliquidTradeLiquidationClient> logger)
        : base(
            ResolveEndpoint(options, out var resolvedOptions),
            logger,
            resolvedOptions.ReceiveBufferSize,
            resolvedOptions.KeepAliveInterval,
            Normalize(resolvedOptions.HyperliquidSubscriptionMessage))
    {
    }

    public override string Exchange => "Hyperliquid";

    private static Uri ResolveEndpoint(IOptions<TradeLiquidationCapturerOptions>? options, out TradeLiquidationCapturerOptions resolved)
    {
        resolved = options?.Value ?? new TradeLiquidationCapturerOptions();
        resolved.EnsureValid();
        return resolved.HyperliquidEndpoint;
    }

    private static string? Normalize(string? message)
        => string.IsNullOrWhiteSpace(message) ? null : message;
}
