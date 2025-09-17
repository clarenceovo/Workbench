namespace CryptoNet.TradeLiquidationCapturer.Models;

/// <summary>
/// Represents a raw liquidation message emitted by an exchange WebSocket stream.
/// </summary>
/// <param name="Exchange">The exchange that emitted the message.</param>
/// <param name="RawMessage">The raw JSON payload received from the WebSocket stream.</param>
/// <param name="ReceivedAt">The timestamp (in UTC) when the message was received by the client.</param>
public sealed record TradeLiquidationEvent(string Exchange, string RawMessage, DateTimeOffset ReceivedAt);
