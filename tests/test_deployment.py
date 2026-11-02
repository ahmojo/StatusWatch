import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def resolve_release(tmp_path):
    if os.name == "nt":
        bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        if not bash.is_file():
            pytest.skip("Git Bash is required for deployment shell tests")
    else:
        bash = shutil.which("bash")
        if not bash:
            pytest.skip("Bash is required for deployment shell tests")

    workflow = (Path(__file__).parents[1] / ".github/workflows/deploy.yml").read_text()
    step = workflow.split("      - name: Resolve tested release and public image\n", 1)[1]
    body = re.search(r"        run: \|\n((?:          .*\n|\n)+)", step)
    assert body is not None
    # Replace external commands; execute the actual workflow shell without network access.
    script = """
git() {
  case "$1" in
    fetch) return 0 ;;
    rev-parse) printf '%s\\n' "$TEST_COMMIT" ;;
    merge-base) return "$TEST_ANCESTOR_EXIT" ;;
    *) return 1 ;;
  esac
}
gh() {
  [[ "$*" == *"--commit $TEST_COMMIT --event push --status success"* ]] || return 1
  printf '%s\\n' "$TEST_RELEASE_URL"
}
docker() {
  case "$*" in
    *:sha-*) printf '%s\\n' "$TEST_SHA_DIGEST" ;;
    *) printf '%s\\n' "$TEST_VERSION_DIGEST" ;;
  esac
}
jq() { cat; }
""" + textwrap.dedent(body[1])
    path = tmp_path / "resolve.sh"
    path.write_text(script, encoding="utf-8", newline="\n")
    output = tmp_path / "output"
    summary = tmp_path / "summary"

    def run(**changes):
        env = os.environ | {
            "VERSION": "v0.1.4", "GITHUB_EVENT_NAME": "workflow_run",
            "GITHUB_REPOSITORY": "ahmojo/StatusWatch",
            "RELEASE_COMMIT": "a" * 40, "TEST_COMMIT": "a" * 40,
            "TEST_ANCESTOR_EXIT": "0", "TEST_RELEASE_URL": "https://example.test/run/1",
            "TEST_VERSION_DIGEST": "sha256:" + "b" * 64,
            "TEST_SHA_DIGEST": "sha256:" + "b" * 64,
            "GITHUB_OUTPUT": output.as_posix(), "GITHUB_STEP_SUMMARY": summary.as_posix(),
        } | changes
        result = subprocess.run(
            [str(bash), "--noprofile", "--norc", "-eo", "pipefail", path.as_posix()],
            env=env, capture_output=True, text=True, timeout=15,
        )
        return result, output.read_text() if output.exists() else ""

    return run


def test_successful_release_resolves_exact_image(resolve_release):
    result, output = resolve_release()
    assert result.returncode == 0, result.stderr
    assert output == (
        f"commit={'a' * 40}\n"
        f"image=ghcr.io/ahmojo/statuswatch@sha256:{'b' * 64}\n"
    )


@pytest.mark.parametrize("changes", [
    {"VERSION": "v01.2.3"},
    {"VERSION": "v0.1.4; echo unexpected"},
    {"RELEASE_COMMIT": "c" * 40},
    {"TEST_ANCESTOR_EXIT": "1"},
    {"TEST_RELEASE_URL": ""},
    {"TEST_SHA_DIGEST": "sha256:" + "c" * 64},
    {"TEST_VERSION_DIGEST": "invalid", "TEST_SHA_DIGEST": "invalid"},
])
def test_invalid_release_produces_no_deployment_output(resolve_release, changes):
    result, output = resolve_release(**changes)
    assert result.returncode != 0
    assert output == ""


def test_manual_rollback_can_use_an_older_tested_commit(resolve_release):
    result, output = resolve_release(GITHUB_EVENT_NAME="workflow_dispatch", RELEASE_COMMIT="")
    assert result.returncode == 0, result.stderr
    assert f"commit={'a' * 40}" in output
