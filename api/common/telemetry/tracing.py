import json
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Generator, Sequence

from opencensus.trace import Span, execution_context
from opencensus.trace.tracer import Tracer

__all__ = ["trace_block", "trace_calls"]


@contextmanager
def trace_block(
    name,
    annotation_description: str | None = None,
    annotation_kwargs: dict[str, str] | None = None,
    /,
    **attributes,
) -> Generator[Span]:
    """
    Trace a block of code using the `with` statement. Yields an OpenCensus tracing Span.

    Args:
        name (str): The name of the tracing Span.
        annotation_description (str, optional): A user-supplied message describing the event.
            The maximum length for the description is 256 bytes.
        annotation_kwargs (Dict[str, str], optional): Keyword arguments of annotation,
            e.g., {'failed': True, 'name': 'Caching'}.
        **attributes (str): Attribute key-value pairs.

    Yields:
        Span: The tracing Span.

    Example:
        with trace_block("my_span", annotation_description="Starting execution", annotation_kwargs={'failed': False}) as span:
            span.add_attribute("number", "123")
            span.add_attribute("operation", "query")
            pass
    """

    tracer: Tracer = execution_context.get_opencensus_tracer()

    with tracer.span(name) as span:
        if annotation_description:
            span.add_annotation(annotation_description, **(annotation_kwargs or {}))

        for k, v in attributes.items():
            span.add_attribute(k, v)

        yield span


def trace_calls(
    args: Sequence[int] | Callable | None = None, kwargs: Sequence[str] | None = None
) -> Callable:
    """
    Decorator for Callables to trace each call, can record arguments (by index) and keyword arguments (by name).

    Args:
        args (Optional[List[int]]): A list of indices of positional arguments to trace.
        kwargs (Optional[List[str]]): A list of names of keyword arguments to trace.

    Returns:
        Callable: The decorated function or method.

    Examples:
        1. Without specifying args and kwargs (no parenthesis required):

            @trace_calls
            def my_function(name, age, gender):
                pass

            @trace_calls() # same as above
            def equivalent (name, age, gender):
                pass

        2. Specifying args and/or kwargs: will trace the first two positional arguments `name` and `age`,
        and the keyword arguments `age` and `gender`. `age` can get traced either way,
        depending on the function call.

            @trace_calls(args=[0, 1], kwargs=['age', 'gender'])
            def my_function(name, age, gender):
                pass

        3. Tracing method calls:

            class A:
                @trace_calls(args=[1, 2], kwargs=['age', 'gender'])
                def __init__(self, name, age, gender):
                    pass

                @classmethod
                @trace_calls(args=[1, 2], kwargs=['age', 'gender'])
                def hello(cls, name, age, gender):
                    pass

                @staticmethod
                @trace_calls(args=[0, 1], kwargs=['age', 'gender'])
                def print(name, age, gender):
                    pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*_args, **_kwargs):
            with trace_block(func.__qualname__) as span:
                span.add_attribute("call.module", func.__module__)
                span.add_attribute("call.name", func.__name__)
                span.add_attribute("call.qualname", func.__qualname__)

                if args:
                    l = len(_args)
                    if v := [str(_args[i])[:128] for i in args if i < l]:
                        span.add_attribute("call.args", json.dumps(v))

                if kwargs:
                    if d := {str(k): str(_kwargs[k]) for k in kwargs if k in _kwargs}:
                        span.add_attribute("call.kwargs", json.dumps(d))

                return func(*_args, **_kwargs)

        return wrapper

    if callable(args):
        # Called as @trace_calls without arguments or empty parenthesis
        func = args
        args = []
        return decorator(func)

    # Called as @trace_calls() with or without arguments, but with parenthesis
    return decorator
