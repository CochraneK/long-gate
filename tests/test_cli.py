from longgate.cli import build_parser


def test_model_setup_parser():
    args = build_parser().parse_args(
        [
            "model",
            "setup",
            "--ram-gb",
            "16",
        ]
    )
    assert args.command == "model"
    assert args.model_command == "setup"
    assert args.ram_gb == 16.0


def test_semantic_auto_model_parser():
    args = build_parser().parse_args(
        [
            "semantic-transform-local",
            "input.txt",
            "--model",
            "auto",
            "--out",
            "preview.txt",
        ]
    )
    assert args.command == "semantic-transform-local"
    assert args.model == "auto"
    assert args.out == "preview.txt"


def test_setup_prompt_parser():
    args = build_parser().parse_args(
        [
            "setup-prompt",
        ]
    )
    assert args.command == "setup-prompt"
