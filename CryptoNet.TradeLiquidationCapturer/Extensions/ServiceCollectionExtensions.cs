using CryptoNet.TradeLiquidationCapturer.Abstractions;
using CryptoNet.TradeLiquidationCapturer.Binance;
using CryptoNet.TradeLiquidationCapturer.Hyperliquid;
using CryptoNet.TradeLiquidationCapturer.Options;
using Microsoft.Extensions.DependencyInjection;

namespace CryptoNet.TradeLiquidationCapturer.Extensions;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddTradeLiquidationCapturer(this IServiceCollection services, Action<TradeLiquidationCapturerOptions>? configure = null)
    {
        ArgumentNullException.ThrowIfNull(services);

        var builder = services.AddOptions<TradeLiquidationCapturerOptions>();
        builder.PostConfigure(options => options.EnsureValid());

        if (configure is not null)
        {
            builder.Configure(configure);
        }

        services.AddSingleton<IBinanceTradeLiquidationClient, BinanceTradeLiquidationClient>();
        services.AddSingleton<IHyperliquidTradeLiquidationClient, HyperliquidTradeLiquidationClient>();
        services.AddSingleton<ITradeLiquidationStreamClient>(sp => sp.GetRequiredService<IBinanceTradeLiquidationClient>());
        services.AddSingleton<ITradeLiquidationStreamClient>(sp => sp.GetRequiredService<IHyperliquidTradeLiquidationClient>());

        return services;
    }
}
