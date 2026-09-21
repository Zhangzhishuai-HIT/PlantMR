import sys

from plant_mr.platform.external import run_external_command


def test_external_adapter_runs_without_shell_and_checks_outputs(tmp_path):
    output = tmp_path / "result.txt"
    result = run_external_command(
        [sys.executable, "-c", "from pathlib import Path; Path('result.txt').write_text('ok')"],
        cwd=tmp_path,
        expected_outputs=[output],
    )

    assert result.returncode == 0
    assert output.read_text() == "ok"
    assert result.command[0] == sys.executable
