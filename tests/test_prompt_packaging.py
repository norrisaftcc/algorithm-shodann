"""Where the prompt library is found, and that it ships in the wheel.

The templates are documents in the top-level ``prompts/`` directory. A wheel
built before 2026-10-17 contained none of them, so ``render_prompt`` worked only
from a source checkout. These tests pin the two halves of the fix: the
resolution order in `shodann.prompts`, and the build configuration that puts the
files in the wheel.

The build configuration is asserted from ``pyproject.toml`` as text-level data
because building a wheel needs the network (setuptools in an isolated build
environment). The wheel itself was built and inspected by hand when this was
written; the commit body records the listing.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

from shodann import prompts
from shodann.prompts import (
    BASE_TEMPLATE,
    PROMPTS_DIR,
    default_prompts_dir,
    render_prompt,
)
from test_prompts import sample_context

ROOT = Path(__file__).parent.parent
POISON = "POISONED-TEMPLATE-FROM-THE-WORKING-DIRECTORY"


def _template_copy(destination: Path) -> Path:
    """Copy the real base template into ``destination`` (a stand-in for package data)."""
    destination.mkdir(parents=True, exist_ok=True)
    (destination / BASE_TEMPLATE).write_text(
        (PROMPTS_DIR / BASE_TEMPLATE).read_text(encoding="utf-8"), encoding="utf-8"
    )
    return destination


# --- resolution order -----------------------------------------------------


def test_the_source_checkout_is_the_default_here() -> None:
    """If this fails the other tests are measuring a different tree than the one shipped."""
    assert (PROMPTS_DIR / BASE_TEMPLATE).is_file()
    assert Path(default_prompts_dir()) == PROMPTS_DIR


def test_resolution_falls_to_package_data_when_there_is_no_source_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercises the real `importlib.resources` lookup against a throwaway package.

    The package is named like an installed one (a regular package on ``sys.path``)
    and ``PACKAGED_PROMPTS`` is pointed at it, so the code under test is the
    production code path and only the *location* is simulated.
    """
    package = tmp_path / "site" / "fake_prompt_library"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    _template_copy(package)
    monkeypatch.syspath_prepend(str(package.parent))
    monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path / "no-such-checkout")
    monkeypatch.setattr(prompts, "PACKAGED_PROMPTS", "fake_prompt_library")

    chosen = default_prompts_dir()
    rendered = render_prompt(sample_context())

    assert (chosen / BASE_TEMPLATE).is_file()
    assert "no-such-checkout" not in str(chosen)
    assert "SHODANN" in rendered
    assert "{{" not in rendered


def test_package_data_without_an_init_file_still_resolves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The wheel ships ``shodann/_prompts/`` with no ``__init__.py`` (verified on 3.11-3.13)."""
    parent = tmp_path / "site" / "fake_namespace_parent"
    parent.mkdir(parents=True)
    (parent / "__init__.py").write_text("", encoding="utf-8")
    _template_copy(parent / "_prompts")
    monkeypatch.syspath_prepend(str(parent.parent))
    monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path / "no-such-checkout")
    monkeypatch.setattr(prompts, "PACKAGED_PROMPTS", "fake_namespace_parent._prompts")

    assert "SHODANN" in render_prompt(sample_context())


def test_neither_location_present_raises_a_clear_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path / "no-such-checkout")
    monkeypatch.setattr(prompts, "PACKAGED_PROMPTS", "shodann_no_such_package.prompts")

    with pytest.raises(FileNotFoundError) as excinfo:
        render_prompt(sample_context())

    message = str(excinfo.value)
    assert "prompt library is not installed" in message
    assert BASE_TEMPLATE in message


def test_a_package_that_exists_but_lacks_the_template_is_not_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wheel built before the fix imports fine and holds no templates."""
    package = tmp_path / "site" / "empty_prompt_library"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.syspath_prepend(str(package.parent))
    monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path / "no-such-checkout")
    monkeypatch.setattr(prompts, "PACKAGED_PROMPTS", "empty_prompt_library")

    with pytest.raises(FileNotFoundError):
        default_prompts_dir()


# --- the working directory is never consulted -----------------------------


@pytest.mark.parametrize("checkout_present", [True, False], ids=["checkout", "packaged"])
def test_a_prompts_directory_in_the_working_directory_is_never_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checkout_present: bool
) -> None:
    """The privileged job runs with the citizen's checkout as its working directory."""
    hostile = tmp_path / "citizen-checkout"
    (hostile / "prompts").mkdir(parents=True)
    (hostile / "prompts" / BASE_TEMPLATE).write_text(
        f"<!-- TEMPLATE:BEGIN -->\n{POISON} {{{{ CITIZEN_USERNAME }}}}\n<!-- TEMPLATE:END -->\n",
        encoding="utf-8",
    )
    if not checkout_present:
        package = tmp_path / "site" / "fake_prompt_library"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        _template_copy(package)
        monkeypatch.syspath_prepend(str(package.parent))
        monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path / "no-such-checkout")
        monkeypatch.setattr(prompts, "PACKAGED_PROMPTS", "fake_prompt_library")
    monkeypatch.chdir(hostile)

    rendered = render_prompt(sample_context())

    assert POISON not in rendered
    assert "SHODANN" in rendered


def test_the_poisoned_working_directory_is_not_used_even_when_nothing_else_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no library installed the answer is an error, not the nearest ``prompts/``."""
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / BASE_TEMPLATE).write_text(
        f"<!-- TEMPLATE:BEGIN -->\n{POISON}\n<!-- TEMPLATE:END -->\n", encoding="utf-8"
    )
    monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path / "no-such-checkout")
    monkeypatch.setattr(prompts, "PACKAGED_PROMPTS", "shodann_no_such_package.prompts")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError):
        render_prompt(sample_context())


def test_an_explicit_prompts_dir_override_still_wins(tmp_path: Path) -> None:
    override = _template_copy(tmp_path / "elsewhere")

    assert "SHODANN" in render_prompt(sample_context(), prompts_dir=override)


def test_prompts_dir_is_still_exported() -> None:
    assert "PROMPTS_DIR" in prompts.__all__
    assert prompts.PROMPTS_DIR == PROMPTS_DIR


# --- the build configuration ----------------------------------------------


@pytest.fixture(scope="module")
def setuptools_config() -> dict:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["setuptools"]


def test_the_wheel_is_configured_to_carry_the_prompts_directory(setuptools_config: dict) -> None:
    assert setuptools_config["package-dir"] == {"": "src", "shodann._prompts": "prompts"}
    assert setuptools_config["packages"] == ["shodann", "shodann._prompts"]
    assert setuptools_config["package-data"] == {"shodann._prompts": ["*.md"]}


def test_the_packaged_name_matches_what_the_resolver_imports(setuptools_config: dict) -> None:
    assert prompts.PACKAGED_PROMPTS in setuptools_config["packages"]


def test_the_package_data_glob_covers_every_template() -> None:
    templates = sorted(path.name for path in PROMPTS_DIR.glob("*.md"))

    # Seven documents today (01-06 and the README). A count of zero would make
    # the glob assertion above vacuous; a different count means this docstring
    # and the wheel check in the PR body need updating.
    assert BASE_TEMPLATE in templates
    assert len(templates) == 7
    assert not [p for p in PROMPTS_DIR.iterdir() if p.is_file() and p.suffix != ".md"]


def test_pytest_imports_shodann_from_src_not_an_installed_copy() -> None:
    """A stale installed wheel would make every resolution test above meaningless."""
    assert Path(prompts.__file__).resolve().is_relative_to(ROOT / "src")
    assert "site-packages" not in sys.modules["shodann"].__file__
