from shared_lib import format_greeting


def test_format_greeting_strips_and_defaults():
    assert format_greeting("  Ada  ") == "Hello, Ada!"
    assert format_greeting(" ") == "Hello, there!"
