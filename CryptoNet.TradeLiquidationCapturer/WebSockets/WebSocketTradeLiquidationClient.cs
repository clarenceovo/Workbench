using System.Buffers;
using System.Net.WebSockets;
using System.Text;
using CryptoNet.TradeLiquidationCapturer.Abstractions;
using CryptoNet.TradeLiquidationCapturer.Models;
using Microsoft.Extensions.Logging;

namespace CryptoNet.TradeLiquidationCapturer.WebSockets;

internal abstract class WebSocketTradeLiquidationClient : ITradeLiquidationStreamClient
{
    private readonly SemaphoreSlim _connectionLock = new(1, 1);
    private readonly Uri _endpoint;
    private readonly ILogger _logger;
    private readonly int _receiveBufferSize;
    private readonly TimeSpan _keepAliveInterval;
    private readonly string? _subscriptionMessage;
    private ClientWebSocket? _client;
    private bool _disposed;
    private int _isStreaming;

    protected WebSocketTradeLiquidationClient(
        Uri endpoint,
        ILogger logger,
        int receiveBufferSize,
        TimeSpan keepAliveInterval,
        string? subscriptionMessage = null)
    {
        _endpoint = endpoint ?? throw new ArgumentNullException(nameof(endpoint));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));

        if (receiveBufferSize <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(receiveBufferSize), receiveBufferSize, "The receive buffer size must be greater than zero.");
        }

        if (keepAliveInterval < TimeSpan.Zero)
        {
            throw new ArgumentOutOfRangeException(nameof(keepAliveInterval), keepAliveInterval, "The keep-alive interval cannot be negative.");
        }

        _receiveBufferSize = receiveBufferSize;
        _keepAliveInterval = keepAliveInterval;
        _subscriptionMessage = string.IsNullOrWhiteSpace(subscriptionMessage) ? null : subscriptionMessage;
    }

    public abstract string Exchange { get; }

    public async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        ThrowIfDisposed();

        await _connectionLock.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            ThrowIfDisposed();

            if (_client?.State == WebSocketState.Open)
            {
                return;
            }

            _client?.Dispose();
            _client = new ClientWebSocket();
            _client.Options.KeepAliveInterval = _keepAliveInterval;
            ConfigureClientWebSocketOptions(_client.Options);

            _logger.LogInformation("Connecting to {Exchange} liquidation stream at {Endpoint}", Exchange, _endpoint);
            await _client.ConnectAsync(_endpoint, cancellationToken).ConfigureAwait(false);
            await OnConnectedAsync(_client, cancellationToken).ConfigureAwait(false);

            if (_subscriptionMessage is { } message)
            {
                var payload = Encoding.UTF8.GetBytes(message);
                await _client.SendAsync(new ArraySegment<byte>(payload), WebSocketMessageType.Text, true, cancellationToken).ConfigureAwait(false);
                _logger.LogDebug("Sent subscription message to {Exchange}: {Message}", Exchange, message);
            }
        }
        finally
        {
            _connectionLock.Release();
        }
    }

    protected virtual void ConfigureClientWebSocketOptions(ClientWebSocketOptions options)
    {
        options.SetRequestHeader("User-Agent", "CryptoNet.TradeLiquidationCapturer");
    }

    protected virtual ValueTask OnConnectedAsync(ClientWebSocket socket, CancellationToken cancellationToken) => ValueTask.CompletedTask;

    public async IAsyncEnumerable<TradeLiquidationEvent> StreamLiquidationsAsync([System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ThrowIfDisposed();

        if (Interlocked.CompareExchange(ref _isStreaming, 1, 0) != 0)
        {
            throw new InvalidOperationException("The WebSocket client is already streaming.");
        }

        try
        {
            await ConnectAsync(cancellationToken).ConfigureAwait(false);
            var socket = _client ?? throw new InvalidOperationException("The WebSocket client is not connected.");

            var buffer = new byte[_receiveBufferSize];
            var writer = new ArrayBufferWriter<byte>(_receiveBufferSize);

            while (!cancellationToken.IsCancellationRequested)
            {
                WebSocketReceiveResult result;
                try
                {
                    result = await socket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken).ConfigureAwait(false);
                }
                catch (OperationCanceledException)
                {
                    yield break;
                }

                if (result.MessageType == WebSocketMessageType.Close)
                {
                    _logger.LogWarning("{Exchange} closed the WebSocket connection with status {Status} ({Description}).", Exchange, result.CloseStatus, result.CloseStatusDescription);

                    try
                    {
                        await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing as requested by server.", cancellationToken).ConfigureAwait(false);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogDebug(ex, "Error while acknowledging close frame from {Exchange}.", Exchange);
                    }

                    yield break;
                }

                if (result.MessageType != WebSocketMessageType.Text)
                {
                    _logger.LogDebug("Ignoring non-text WebSocket message from {Exchange}. MessageType: {MessageType}", Exchange, result.MessageType);
                    continue;
                }

                if (result.Count > 0)
                {
                    writer.Write(buffer.AsSpan(0, result.Count));
                }

                if (!result.EndOfMessage)
                {
                    continue;
                }

                var rawMessage = Encoding.UTF8.GetString(writer.WrittenSpan);
                writer.Clear();

                if (string.IsNullOrWhiteSpace(rawMessage))
                {
                    continue;
                }

                var @event = CreateEvent(rawMessage);
                if (@event is not null)
                {
                    yield return @event;
                }
            }
        }
        finally
        {
            Interlocked.Exchange(ref _isStreaming, 0);
        }
    }

    protected virtual TradeLiquidationEvent? CreateEvent(string rawMessage)
        => new TradeLiquidationEvent(Exchange, rawMessage, DateTimeOffset.UtcNow);

    public async ValueTask DisposeAsync()
    {
        if (_disposed)
        {
            return;
        }

        _disposed = true;

        _connectionLock.Dispose();

        if (_client is null)
        {
            return;
        }

        try
        {
            if (_client.State is WebSocketState.Open or WebSocketState.CloseReceived)
            {
                await _client.CloseAsync(WebSocketCloseStatus.NormalClosure, "Disposing client", CancellationToken.None).ConfigureAwait(false);
            }
        }
        catch (Exception ex)
        {
            _logger.LogDebug(ex, "Failed to close WebSocket connection for {Exchange} gracefully.", Exchange);
        }
        finally
        {
            _client.Dispose();
            _client = null;
        }
    }

    protected void ThrowIfDisposed()
    {
        if (_disposed)
        {
            throw new ObjectDisposedException(GetType().Name);
        }
    }
}
