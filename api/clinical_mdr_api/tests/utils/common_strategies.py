from hypothesis.strategies import composite, from_regex


@composite
def strings_with_at_least_one_non_space_char(draw):
    return draw(from_regex(r"[^\s]"))


@composite
def stripped_non_empty_strings(draw):
    return draw(strings_with_at_least_one_non_space_char().map(lambda _: _.strip()))
