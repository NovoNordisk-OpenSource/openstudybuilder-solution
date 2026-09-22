import aiohttp


def request_tracer(results_collector):
    async def on_request_start(
        session: aiohttp.ClientSession, context, params: aiohttp.TraceRequestStartParams
    ):
        context.on_request_start = session.loop.time()
        context.method = params.method
        context.url = params.url

    async def on_request_end(
        session: aiohttp.ClientSession, context, params: aiohttp.TraceRequestEndParams
    ):
        total = session.loop.time() - context.on_request_start
        context.on_request_end = total
        context.status = params.response.status
        context.response = await params.response.text()
        print(context)

    trace_config = aiohttp.TraceConfig()

    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)

    return trace_config
