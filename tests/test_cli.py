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


def test_profile_file_parser():
    args = build_parser().parse_args(
        [
            "run",
            "study.csv",
            "--profile-file",
            "policy/org.json",
        ]
    )
    assert args.command == "run"
    assert args.profile_file == "policy/org.json"


def test_approve_egress_parser():
    args = build_parser().parse_args(
        [
            "approve-egress",
            "run/egress/safe.json",
            "--workspace",
            "run/egress",
            "--ledger",
            "approvals.jsonl",
            "--purpose",
            "interpret aggregate statistics",
        ]
    )
    assert args.command == "approve-egress"
    assert args.purpose == "interpret aggregate statistics"



def test_sign_run_parser():
    args = build_parser().parse_args(
        [
            "sign-run",
            "longgate-runs/LG-demo",
            "--signing-key",
            "signing-key.pem",
        ]
    )
    assert args.command == "sign-run"
    assert args.signing_key == "signing-key.pem"


def test_verify_run_public_key_parser():
    args = build_parser().parse_args(
        [
            "verify-run",
            "longgate-runs/LG-demo",
            "--public-key",
            "verification-key.pem",
        ]
    )
    assert args.command == "verify-run"
    assert args.public_key == "verification-key.pem"
