from test_app.main import build_parser


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.name == "there"
