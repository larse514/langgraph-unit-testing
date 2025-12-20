"""Pytest configuration for eval tests."""

import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--judge-model",
        action="store",
        default=None,
        help="LLM model to use for judge evaluations (default: gpt-4o-mini)"
    )


@pytest.fixture(scope="session", autouse=True)
def set_judge_model(request):
    model = request.config.getoption("--judge-model")
    if model:
        os.environ["LLM_JUDGE_MODEL"] = model

