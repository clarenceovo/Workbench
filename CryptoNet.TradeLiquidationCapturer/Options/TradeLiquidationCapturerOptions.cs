namespace CryptoNet.TradeLiquidationCapturer.Options;

/// <summary>
/// Provides configuration values for the trade liquidation WebSocket clients.
/// </summary>
public sealed class TradeLiquidationCapturerOptions
{
    private static readonly Uri DefaultBinanceEndpoint = new("wss://fstream.binance.com/stream?streams=!forceOrder@arr");
    private static readonly Uri DefaultHyperliquidEndpoint = new("wss://api.hyperliquid.xyz/ws");

    /// <summary>
    /// Gets or sets the WebSocket endpoint for Binance liquidation streams.
    /// </summary>
    public Uri BinanceEndpoint { get; set; } = DefaultBinanceEndpoint;

    /// <summary>
    /// Gets or sets an optional subscription message sent immediately after the Binance connection is established.
    /// </summary>
    public string? BinanceSubscriptionMessage { get; set; }

    /// <summary>
    /// Gets or sets the WebSocket endpoint for Hyperliquid liquidation streams.
    /// </summary>
    public Uri HyperliquidEndpoint { get; set; } = DefaultHyperliquidEndpoint;

    /// <summary>
    /// Gets or sets an optional subscription message sent immediately after the Hyperliquid connection is established.
    /// </summary>
    public string? HyperliquidSubscriptionMessage { get; set; }

    /// <summary>
    /// Gets or sets the keep-alive interval applied to the WebSocket connections.
    /// </summary>
    public TimeSpan KeepAliveInterval { get; set; } = TimeSpan.FromSeconds(15);

    /// <summary>
    /// Gets or sets the size, in bytes, of the receive buffer used for incoming WebSocket messages.
    /// </summary>
    public int ReceiveBufferSize { get; set; } = 8192;

    internal void EnsureValid()
    {
        BinanceEndpoint ??= DefaultBinanceEndpoint;
        HyperliquidEndpoint ??= DefaultHyperliquidEndpoint;

        if (ReceiveBufferSize <= 0)
        {
            throw new InvalidOperationException("ReceiveBufferSize must be greater than zero.");
        }

        if (KeepAliveInterval < TimeSpan.Zero)
        {
            throw new InvalidOperationException("KeepAliveInterval must not be negative.");
        }

        if (!BinanceEndpoint.IsAbsoluteUri)
        {
            throw new InvalidOperationException("BinanceEndpoint must be an absolute URI.");
        }

        if (!HyperliquidEndpoint.IsAbsoluteUri)
        {
            throw new InvalidOperationException("HyperliquidEndpoint must be an absolute URI.");
        }

        if (!IsWebSocketScheme(BinanceEndpoint))
        {
            throw new InvalidOperationException("BinanceEndpoint must use the ws or wss scheme.");
        }

        if (!IsWebSocketScheme(HyperliquidEndpoint))
        {
            throw new InvalidOperationException("HyperliquidEndpoint must use the ws or wss scheme.");
        }
    }

    private static bool IsWebSocketScheme(Uri uri)
        => string.Equals(uri.Scheme, "ws", StringComparison.OrdinalIgnoreCase)
           || string.Equals(uri.Scheme, "wss", StringComparison.OrdinalIgnoreCase);
}
