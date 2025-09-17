using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;
using StackExchange.Redis;

namespace CryptoNet.Common;

/// <inheritdoc cref="IRedisClient" />
public class RedisClient : IRedisClient
{
    private readonly IDatabase _database;
    private readonly JsonSerializerOptions _serializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisClient"/> class.
    /// </summary>
    /// <param name="connectionMultiplexer">The shared Redis connection.</param>
    /// <param name="options">Options that control how values are serialized and which database is targeted.</param>
    public RedisClient(IConnectionMultiplexer connectionMultiplexer, IOptions<RedisOptions> options)
    {
        if (connectionMultiplexer is null)
        {
            throw new ArgumentNullException(nameof(connectionMultiplexer));
        }

        if (options is null)
        {
            throw new ArgumentNullException(nameof(options));
        }

        var redisOptions = options.Value ?? throw new ArgumentException("Options value cannot be null.", nameof(options));
        _database = connectionMultiplexer.GetDatabase(redisOptions.DefaultDatabase ?? -1);
        _serializerOptions = new JsonSerializerOptions(JsonSerializerDefaults.Web);
    }

    /// <inheritdoc />
    public async Task<T?> GetAsync<T>(string key)
    {
        EnsureKey(key);

        var redisValue = await _database.StringGetAsync(key).ConfigureAwait(false);
        if (redisValue.IsNullOrEmpty)
        {
            return default;
        }

        if (typeof(T) == typeof(string))
        {
            return (T)(object)redisValue.ToString();
        }

        if (typeof(T) == typeof(byte[]))
        {
            return (T)(object)((byte[])redisValue);
        }

        if (typeof(T) == typeof(RedisValue))
        {
            return (T)(object)redisValue;
        }

        try
        {
            var json = redisValue.ToString();
            return JsonSerializer.Deserialize<T>(json, _serializerOptions);
        }
        catch (JsonException exception)
        {
            throw new InvalidOperationException(
                $"Unable to deserialize the value stored at key '{key}' to type '{typeof(T)}'.",
                exception);
        }
    }

    /// <inheritdoc />
    public Task SetAsync<T>(string key, T value, TimeSpan? expiry = null)
    {
        EnsureKey(key);

        if (value is null)
        {
            throw new ArgumentNullException(nameof(value));
        }

        RedisValue redisValue = value switch
        {
            RedisValue rv => rv,
            string stringValue => stringValue,
            byte[] bytes => bytes,
            _ => JsonSerializer.Serialize(value, _serializerOptions)
        };

        return _database.StringSetAsync(key, redisValue, expiry);
    }

    /// <inheritdoc />
    public Task<bool> DeleteAsync(string key)
    {
        EnsureKey(key);
        return _database.KeyDeleteAsync(key);
    }

    /// <inheritdoc />
    public Task<bool> ExistsAsync(string key)
    {
        EnsureKey(key);
        return _database.KeyExistsAsync(key);
    }

    private static void EnsureKey(string key)
    {
        if (string.IsNullOrWhiteSpace(key))
        {
            throw new ArgumentException("Redis key cannot be null or whitespace.", nameof(key));
        }
    }
}
