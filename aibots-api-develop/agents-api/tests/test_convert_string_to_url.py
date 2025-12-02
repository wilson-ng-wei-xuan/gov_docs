
from agents.utils import convert_string_to_url

import pytest


class TestConvertStringToUrl:

    @pytest.mark.parametrize(
        argnames=["test_input", "test_output"],
        argvalues=[
            pytest.param("Hello World", "hello-world", id="with_space"),
            pytest.param("This is a test!", "this-is-a-test", id="phrases"),
            pytest.param("123 Test", "123-test", id="with_numbers"),
            pytest.param("", "", id="empty_string"),
            pytest.param("   ", "", id="spaces_only"),
            pytest.param("  Test  ", "test", id="leading_trailing_spaces"),
            pytest.param("HELLO", "hello", id="uppercase"),
            pytest.param("Hello     World", "hello-world", id="multiple_spaces"),
            pytest.param("Café", "cafe", id="non_ascii"),
        ]
    )
    def test_convert_string_to_url(self, test_input, test_output):
        assert convert_string_to_url(test_input) == test_output
