from pathlib import Path

from agenteval.cli.scaffold import detect_project, generate_conftest, generate_example_test


def test_detect_project_finds_nothing(tmp_path: Path):
    result = detect_project(tmp_path)
    assert result["providers"] == []
    assert result["frameworks"] == []


def test_detect_project_from_pyproject(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\ndependencies = ["openai>=1.0", "boto3"]\n')
    result = detect_project(tmp_path)
    assert "openai" in result["providers"]
    assert "bedrock" in result["providers"]


def test_detect_project_from_requirements(tmp_path: Path):
    req = tmp_path / "requirements.txt"
    req.write_text("langchain>=0.1\nollama\n")
    result = detect_project(tmp_path)
    assert "ollama" in result["providers"]
    assert "langchain" in result["frameworks"]


def test_generate_conftest():
    conftest = generate_conftest(providers=["openai"], frameworks=[])
    assert "agent_runner" in conftest
    assert "import" in conftest
    assert "def agent" in conftest


def test_generate_example_test():
    test_code = generate_example_test(agent_type="tool_using")
    assert "def test_" in test_code
    assert "trace" in test_code
    assert "assert" in test_code


def test_generate_example_test_rag():
    test_code = generate_example_test(agent_type="rag")
    assert "hallucination" in test_code.lower() or "grounding" in test_code.lower()


def test_scaffolds_to_directory(tmp_path: Path):
    conftest = generate_conftest(providers=["openai"], frameworks=[])
    test_code = generate_example_test(agent_type="generic")

    test_dir = tmp_path / "tests" / "agent_evals"
    test_dir.mkdir(parents=True)
    (test_dir / "conftest.py").write_text(conftest)
    (test_dir / "test_example.py").write_text(test_code)

    assert (test_dir / "conftest.py").exists()
    assert (test_dir / "test_example.py").exists()
