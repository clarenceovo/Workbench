using System.Runtime.CompilerServices;
using CryptoNet.TradeLiquidationCapturer.Models;

namespace CryptoNet.TradeLiquidationCapturer.Abstractions;

public interface ITradeLiquidationStreamClient : IAsyncDisposable
{
    string Exchange { get; }

    Task ConnectAsync(CancellationToken cancellationToken = default);

    IAsyncEnumerable<TradeLiquidationEvent> StreamLiquidationsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default);
}
