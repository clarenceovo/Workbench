using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Options;
using StackExchange.Redis;

namespace CryptoNet.Common;

/// <summary>
/// Extension methods that register the Redis infrastructure with a dependency injection container.
/// </summary>
public static class RedisServiceCollectionExtensions
{
    /// <summary>
    /// Registers the Redis client infrastructure using values provided through configuration binding.
    /// </summary>
    /// <param name="services">The service collection to configure.</param>
    /// <param name="configuration">Configuration section that contains the <see cref="RedisOptions"/> values.</param>
    /// <returns>The same service collection instance for chaining.</returns>
    public static IServiceCollection AddRedisClient(this IServiceCollection services, IConfiguration configuration)
    {
        if (services is null)
        {
            throw new ArgumentNullException(nameof(services));
        }

        if (configuration is null)
        {
            throw new ArgumentNullException(nameof(configuration));
        }

        services.Configure<RedisOptions>(configuration);
        RegisterRedisServices(services);
        return services;
    }

    /// <summary>
    /// Registers the Redis client infrastructure using programmatic configuration.
    /// </summary>
    /// <param name="services">The service collection to configure.</param>
    /// <param name="configureOptions">Delegate used to configure <see cref="RedisOptions"/>.</param>
    /// <returns>The same service collection instance for chaining.</returns>
    public static IServiceCollection AddRedisClient(this IServiceCollection services, Action<RedisOptions> configureOptions)
    {
        if (services is null)
        {
            throw new ArgumentNullException(nameof(services));
        }

        if (configureOptions is null)
        {
            throw new ArgumentNullException(nameof(configureOptions));
        }

        services.Configure(configureOptions);
        RegisterRedisServices(services);
        return services;
    }

    private static void RegisterRedisServices(IServiceCollection services)
    {
        services.TryAddSingleton<IConnectionMultiplexer>(provider =>
        {
            var options = provider.GetRequiredService<IOptions<RedisOptions>>().Value;
            return CreateConnectionMultiplexer(options);
        });

        services.TryAddSingleton<IRedisClient, RedisClient>();
    }

    private static IConnectionMultiplexer CreateConnectionMultiplexer(RedisOptions options)
    {
        if (options is null)
        {
            throw new ArgumentNullException(nameof(options));
        }

        if (!string.IsNullOrWhiteSpace(options.ConnectionString))
        {
            return ConnectionMultiplexer.Connect(options.ConnectionString);
        }

        if (string.IsNullOrWhiteSpace(options.Host))
        {
            throw new InvalidOperationException("A Redis host or connection string must be provided.");
        }

        var configurationOptions = new ConfigurationOptions
        {
            AbortOnConnectFail = options.AbortOnConnectFail,
            Ssl = options.Ssl,
        };

        configurationOptions.EndPoints.Add(options.Host, options.Port);

        if (!string.IsNullOrWhiteSpace(options.Password))
        {
            configurationOptions.Password = options.Password;
        }

        if (!string.IsNullOrWhiteSpace(options.ClientName))
        {
            configurationOptions.ClientName = options.ClientName;
        }

        if (options.DefaultDatabase.HasValue)
        {
            configurationOptions.DefaultDatabase = options.DefaultDatabase.Value;
        }

        return ConnectionMultiplexer.Connect(configurationOptions);
    }
}
