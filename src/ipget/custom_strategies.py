import random

from hypothesis import strategies as st


def everything_except(excluded_types):
    return (
        st.from_type(type)
        .flatmap(st.from_type)
        .filter(lambda x: not isinstance(x, excluded_types))
    )


def _generate_casing_variations(input_string: str):
    return [
        input_string.upper(),  # Uppercase
        input_string.lower(),  # Lowercase
        input_string.capitalize(),  # Capitalize first letter
        input_string.swapcase(),
    ]


@st.composite
def random_casing(draw: st.DrawFn, string_list: list[str]):
    rand_level = random.choice(string_list)
    return draw(st.sampled_from(_generate_casing_variations(rand_level)))
