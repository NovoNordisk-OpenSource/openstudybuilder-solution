# Tracing

Both _clinical-mdr-api_ and _consumer-api_ applications can trace the requests, execution flow, executed Cypher queries,
and exceptions raised. This can be particularly useful for debugging and discovering issues in development as well as in
live deployments.


## Tracing to Azure Monitor Application Insights 

- For tracing to Azure Monitor Application Insights:
    ```dotenv
    TRACING_ENABLED=true
    APPLICATIONINSIGHTS_CONNECTION_STRING='InstrumentationKey=00000000-0000-0000-0000-000000000000'
    ```


## Tracing to Zipkin

Zipkin can be used for capturing the recent traces in a local development environment.

`compose.dev.yaml` contains _zipkin_ service entry for easy starting of a Zipkin Docker container on
[localhost:9411](http://localhost:9411/)

```shell
COMPOSE_FILE=compose.dev.yaml docker compose up zipkin
```

The back-end API applications should be restarted with the `ZIPKIN_HOST` environment variable set.
(`COMPOSE_FILE` environment variable can also be set in the `.env` file)

```dotenv
TRACING_ENABLED=true
ZIPKIN_HOST=localhost # or "zipkin" if the API is started using Docker Compose
```

**Remarks:**

- Zipkin protocol limits attribute values to ~128 chars, e.g. Cypher query texts will get truncated.
- Jaeger can also be configured to receive traces via the Zipkin protocol. (Attribute value size is still limited.)
- Tracing to Azure takes preference over Zipkin tracing.


## Configuring Tracing

| environment variable               | type | default       |
|------------------------------------|------|---------------|
| TRACING_METRICS_HEADER             | bool | False         |
| TRACE_REQUEST_BODY **(!)**         | bool | False         |
| TRACE_REQUEST_BODY_MIN_STATUS_CODE | int  | 400           |
| TRACE_REQUEST_BODY_TRUNCATE_BYTES  | int  | 2048          |
| TRACE_QUERY_MAX_LEN                | int  | 4000          |
| ZIPKIN_HOST                        | str  | _empty_       |
| ZIPKIN_PORT                        | int  | 9411          |
| ZIPKIN_ENDPOINT                    | str  | /api/v2/spans |
| ZIPKIN_PROTOCOL                    | str  | http          |
| TRACEBACK_MAX_ENTRIES              | int  | 15            |


TRACING_METRICS_HEADER
: Returns tracing metrics in X-Metrics HTTP header, useful for local development.
(number of queries executed, cumulative wall-clock time spent on queries, slowest Cypher query)

```
x-metrics: {"cypher.count": 3, "cypher.times": 2.8785, "cypher.slowest.time": 2.7611}
```

TRACE_REQUEST_BODY
: **(!) Warning: enabling this feature can expose sensitive data via logging and tracing.**
Trace the contents of the request body if response status code is TRACE_REQUEST_BODY_MIN_STATUS_CODE or greater.
Limit the size of the traced data to TRACE_REQUEST_BODY_TRUNCATE_BYTES.

TRACE_QUERY_MAX_LEN
: Chops the traced Cypher query.

ZIPKIN_HOST
: Set to enable tracing to a Zipkin collector.
ZIPKIN_PORT, ZIPKIN_ENDPOINT, and ZIPKIN_PROTOCOL can be set for further configuration.

TRACEBACK_MAX_ENTRIES
: Limits the number of stack trace entries when tracebacks get logged and traced.


# Logging

Both _clinical-mdr-api_ and _consumer-api_ applications use Uvicorn, so logging can be configured using a YAML
config file set in the `UVICORN_LOG_CONFIG` environment variable.
See [Python logging.config](https://docs.python.org/3/library/logging.config.html#logging-config-api) for more details.


## Logging to Azure Monitor Application Insights 

- For sending logs to Azure Monitor:
    ```dotenv
    APPLICATIONINSIGHTS_CONNECTION_STRING='InstrumentationKey=00000000-0000-0000-0000-000000000000'
    UVICORN_LOG_CONFIG='logging-azure.yaml'
    ```

`logging-azure.yaml` is set up to send log and traceback messages to Azure Monitor. 
