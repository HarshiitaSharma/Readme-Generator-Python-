from pathlib import Path

from readme_generator.render import render_readme
from readme_generator.scanner import scan_project

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_node_project():
    info = scan_project(str(FIXTURES / "fake_node_project"))
    assert info.project_type == "node"
    assert info.name == "fake-node-project"
    assert "react" in info.dependencies
    assert "dev" in info.scripts


def test_detects_python_project():
    info = scan_project(str(FIXTURES / "fake_python_project"))
    assert info.project_type == "python"
    assert "requests" in info.dependencies
    assert "click" in info.dependencies
    assert info.has_license is True
    assert info.has_tests is True


def test_render_node_readme_contains_key_sections():
    info = scan_project(str(FIXTURES / "fake_node_project"))
    text = render_readme(info)
    assert "# Fake Node Project" in text
    assert "npm install" in text
    assert "npm run dev" in text


def test_render_python_readme_mentions_pip_and_license():
    info = scan_project(str(FIXTURES / "fake_python_project"))
    text = render_readme(info)
    assert "pip install -r requirements.txt" in text
    assert "MIT" in text
    assert "pytest" in text
