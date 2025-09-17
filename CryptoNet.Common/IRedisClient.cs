using System;
using System.Threading.Tasks;

namespace CryptoNet.Common;

/// <summary>
/// Abstraction over a Redis client that exposes a small set of common operations
/// used throughout the application. The abstraction keeps the dependency on the
/// StackExchange.Redis library isolated and simplifies testing by allowing the
/// implementation to be mocked.
/// </summary>
public interface IRedisClient
{
    /// <summary>
    /// Retrieve the value stored for <paramref name="key" /> and deserialize it into <typeparamref name="T" />.
    /// </summary>
    /// <typeparam name="T">Type that the stored value will be deserialized into.</typeparam>
    /// <param name="key">Redis key.</param>
    /// <returns>The stored value or <c>null</c> when the key does not exist.</returns>
    Task<T?> GetAsync<T>(string key);

    /// <summary>
    /// Store <paramref name="value" /> at <paramref name="key" /> optionally setting a key expiration.
    /// </summary>
    /// <typeparam name="T">Type of value to persist.</typeparam>
    /// <param name="key">Redis key.</param>
    /// <param name="value">
    /// Value to persist. The value will be serialized to JSON when it is not a string or byte array.
    /// </param>
    /// <param name="expiry">Optional expiration for the key.</param>
    Task SetAsync<T>(string key, T value, TimeSpan? expiry = null);

    /// <summary>
    /// Delete the value stored for <paramref name="key" />.
    /// </summary>
    /// <param name="key">Redis key.</param>
    /// <returns><c>true</c> when a key was removed.</returns>
    Task<bool> DeleteAsync(string key);

    /// <summary>
    /// Check whether the provided key exists in Redis.
    /// </summary>
    /// <param name="key">Redis key.</param>
    /// <returns><c>true</c> when the key exists.</returns>
    Task<bool> ExistsAsync(string key);
}
