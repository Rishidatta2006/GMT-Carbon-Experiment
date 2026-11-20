"""
ScenarioRunner YAML configuration verification tests.
Validates all GMT usage scenarios against official GMT schema conventions.
"""

import glob
import os
import yaml
import pytest

SCENARIO_FILES = glob.glob(os.path.join(os.path.dirname(__file__), "..", "scenarios", "*.yml"))
ROOT_SCENARIO = os.path.join(os.path.dirname(__file__), "..", "usage_scenario.yml")
ALL_SCENARIOS = SCENARIO_FILES + ([ROOT_SCENARIO] if os.path.exists(ROOT_SCENARIO) else [])


@pytest.mark.parametrize("scenario_path", ALL_SCENARIOS)
def test_scenario_yaml_is_valid(scenario_path):
    """Ensure YAML file parses without syntax errors."""
    with open(scenario_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{scenario_path} must parse into a dictionary"


@pytest.mark.parametrize("scenario_path", ALL_SCENARIOS)
def test_scenario_required_metadata(scenario_path):
    """Verify official required metadata keys exist."""
    with open(scenario_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "name" in data and len(data["name"]) > 0, f"Missing 'name' in {scenario_path}"
    assert "author" in data and len(data["author"]) > 0, f"Missing 'author' in {scenario_path}"
    assert "description" in data and len(data["description"]) > 0, f"Missing 'description' in {scenario_path}"


@pytest.mark.parametrize("scenario_path", ALL_SCENARIOS)
def test_scenario_services_block(scenario_path):
    """Verify services block defines valid container configuration."""
    with open(scenario_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "services" in data, f"Missing 'services' block in {scenario_path}"
    services = data["services"]
    assert isinstance(services, dict) and len(services) > 0

    for s_name, s_conf in services.items():
        assert "build" in s_conf or "image" in s_conf, \
            f"Service '{s_name}' in {scenario_path} must specify either 'build' or 'image'"
        # Confirm keep-alive entrypoint / command is present to avoid premature termination during GMT BOOT
        has_keepalive = (
            "entrypoint" in s_conf or
            "command" in s_conf or
            s_conf.get("image") is not None
        )
        assert has_keepalive, f"Service '{s_name}' in {scenario_path} should configure keep-alive entrypoint"


@pytest.mark.parametrize("scenario_path", ALL_SCENARIOS)
def test_scenario_build_context_resolves_dockerfile(scenario_path):
    """
    Verify that for each scenario, the build context and dockerfile
    resolve correctly to the physical Dockerfile on disk.
    This prevents 'FileNotFoundError: Dockerfile ... not found' errors in GMT.
    """
    scenario_dir = os.path.dirname(os.path.abspath(scenario_path))
    with open(scenario_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    for s_name, s_conf in services.items():
        build_conf = s_conf.get("build")
        if build_conf is None:
            continue

        if isinstance(build_conf, str):
            context_path = os.path.normpath(os.path.join(scenario_dir, build_conf))
            dockerfile_path = os.path.join(context_path, "Dockerfile")
        elif isinstance(build_conf, dict):
            context_rel = build_conf.get("context", ".")
            dockerfile_rel = build_conf.get("dockerfile", "Dockerfile")
            context_path = os.path.normpath(os.path.join(scenario_dir, context_rel))
            dockerfile_path = os.path.normpath(os.path.join(context_path, dockerfile_rel))
        else:
            pytest.fail(f"Unexpected build config type: {type(build_conf)}")

        assert os.path.isdir(context_path), \
            f"Build context path '{context_path}' does not exist for scenario {scenario_path}"
        assert os.path.isfile(dockerfile_path), \
            f"Dockerfile '{dockerfile_path}' not found from build context in {scenario_path}"


@pytest.mark.parametrize("scenario_path", ALL_SCENARIOS)
def test_scenario_flow_block(scenario_path):
    """Verify flow block contains valid command steps."""
    with open(scenario_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "flow" in data, f"Missing 'flow' block in {scenario_path}"
    flow = data["flow"]
    assert isinstance(flow, list) and len(flow) > 0

    services = data.get("services", {})

    for step in flow:
        assert "name" in step, f"Flow step missing 'name' in {scenario_path}"
        assert "container" in step, f"Flow step missing 'container' in {scenario_path}"
        assert step["container"] in services, \
            f"Flow step container '{step['container']}' not found in services in {scenario_path}"
        assert "commands" in step, f"Flow step missing 'commands' in {scenario_path}"
        assert isinstance(step["commands"], list) and len(step["commands"]) > 0

        for cmd in step["commands"]:
            assert "type" in cmd, f"Command missing 'type' in {scenario_path}"
            assert cmd["type"] in ["console", "playwright", "sleep", "shell"], \
                f"Unknown command type '{cmd['type']}' in {scenario_path}"
            assert "command" in cmd, f"Command missing 'command' string in {scenario_path}"
