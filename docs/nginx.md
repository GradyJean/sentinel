# 配置 Nginx 日志格式以支持 Sentinel 系统数据统计

为了方便 Sentinel 系统对访问数据进行统计和分析，需要自定义 Nginx 的日志格式。通过自定义日志格式，可以将访问的关键信息（如客户端 IP、响应状态码、请求 URI、用户代理 UA 等）以统一且易于解析的格式记录下来，便于后续的数据处理和统计。

## 自定义日志格式示例

以下是一个推荐的 `log_format` 定义示例，使用 `||` 作为字段分隔符，方便后续对日志进行拆分和解析：

```nginx
log_format sentinel_log '$remote_addr||$remote_user||$time_local||$request||$status||$body_bytes_sent||$http_referer||$http_user_agent';
```

各字段含义如下：

- `$remote_addr`：客户端 IP 地址
- `$remote_user`：客户端用户名（如果有）
- `$time_local`：本地时间
- `$request`：请求的完整内容（方法、URI、协议）
- `$status`：响应状态码
- `$body_bytes_sent`：响应体大小（字节）
- `$http_referer`：来源页面
- `$http_user_agent`：客户端浏览器或 UA 信息

## 配置 access_log

在 Nginx 配置文件中，使用自定义的日志格式来记录访问日志：

```nginx
access_log /var/log/nginx/sentinel_access.log sentinel_log;
```

这样，所有访问日志将按照 `sentinel_log` 格式写入指定文件，方便 Sentinel 系统读取和统计。

## 示例日志行

```
192.168.1.1||-||10/Jun/2024:14:22:01 +0800||"GET /index.html HTTP/1.1"||200||1024||"http://example.com"||"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
```

该日志行表示：

- 客户端 IP 为 `192.168.1.1`
- 无用户名（`-`）
- 访问时间为 `10/Jun/2024:14:22:01 +0800`
- 请求为 `GET /index.html HTTP/1.1`
- 响应状态码为 `200`
- 响应体大小为 `1024` 字节
- 来源页面为 `http://example.com`
- 用户代理为 `Mozilla/5.0 (Windows NT 10.0; Win64; x64)`

通过这种格式，Sentinel 系统可以方便地对访问日志进行字段拆分和统计分析。
