namespace CryptoNet.Common;

/// <summary>
/// Options used to configure the Redis connection and default behaviour for <see cref="RedisClient"/>.
/// </summary>
public class RedisOptions
{
    /// <summary>
    /// Connection string that will be used when provided. When not specified the <see cref="Host"/> and <see cref="Port"/>
    /// values will be used to build a <see cref="StackExchange.Redis.ConfigurationOptions"/> instance.
    /// </summary>
    public string? ConnectionString { get; set; }

    /// <summary>
    /// Host of the Redis server. Defaults to <c>localhost</c>.
    /// </summary>
    public string Host { get; set; } = "localhost";

    /// <summary>
    /// Port of the Redis server. Defaults to the standard Redis port 6379.
    /// </summary>
    public int Port { get; set; } = 6379;

    /// <summary>
    /// Password required to authenticate against the Redis server.
    /// </summary>
    public string? Password { get; set; }

    /// <summary>
    /// Default database to use. When <c>null</c> the connection default will be used.
    /// </summary>
    public int? DefaultDatabase { get; set; }

    /// <summary>
    /// Optional logical client name.
    /// </summary>
    public string? ClientName { get; set; }

    /// <summary>
    /// Whether SSL should be used for the connection.
    /// </summary>
    public bool Ssl { get; set; }

    /// <summary>
    /// Controls the value of <see cref="StackExchange.Redis.ConfigurationOptions.AbortOnConnectFail"/>.
    /// </summary>
    public bool AbortOnConnectFail { get; set; } = true;
}
