import pytest
from agent import Agent

def test_initialization():
    agent = Agent(0, 0, speed=2.0)
    assert agent.x == 0
    assert agent.y == 0
    assert agent.get_speed() == 2.0
    assert agent.path == []
    assert agent.moving is False

def test_set_path():
    agent = Agent(0, 0)
    path = [(1, 1), (2, 2)]
    agent.set_path(path)
    assert agent.path == path
    assert agent.needs_redraw is True

