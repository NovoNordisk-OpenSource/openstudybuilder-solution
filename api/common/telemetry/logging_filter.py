import logging

from opencensus.log import (
    SAMPLING_DECISION_KEY,
    SPAN_ID_KEY,
    TRACE_ID_KEY,
    get_log_attrs,
)


class TracingContextFilter(logging.Filter):
    """This is a logging filter to add tracing context to the log record."""

    def filter(self, record: logging.LogRecord):
        if not all(
            (
                getattr(record, TRACE_ID_KEY, None),
                getattr(record, SPAN_ID_KEY, None),
                getattr(record, SAMPLING_DECISION_KEY, None),
            )
        ):
            trace_id, span_id, sampling_decision = get_log_attrs()
            setattr(record, TRACE_ID_KEY, trace_id)
            setattr(record, SPAN_ID_KEY, span_id)
            setattr(record, SAMPLING_DECISION_KEY, sampling_decision)
        return True
