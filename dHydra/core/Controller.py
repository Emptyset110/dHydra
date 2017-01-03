# coding: utf-8


def controller(func):
    def _controller(
            query_arguments,
            body_arguments,
            get_query_argument,
            get_body_argument
    ):
        result = func(
            query_arguments,
            body_arguments,
            get_query_argument,
            get_body_argument
        )
        return result
    return _controller

def controller_post(func):
    def _controller(
            query_arguments,
            body_arguments,
            get_query_argument,
            get_body_argument
    ):
        result = func(
            query_arguments,
            body_arguments,
            get_query_argument,
            get_body_argument
        )
        return result
    return _controller

def controller_get(func):
    def _controller(
            query_arguments,
            get_query_argument,
    ):
        result = func(
            query_arguments,
            get_query_argument,
        )
        return result
    return _controller