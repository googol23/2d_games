import pytest
from agent import Agent

def test_initialization():
    agent = Agent(0, 0, speed=2.0)
    assert agent.x == 0
    assert agent.y == 0
    assert agent.speed == 2.0
    assert agent.path == []
    assert agent.moving is False

def test_set_path():
    agent = Agent(0, 0)
    path = [(1, 1), (2, 2)]
    agent.set_path(path)
    assert agent.path == path
    assert agent.needs_redraw is True

def test_basic_movement():
    agent = Agent(0, 0, speed=1.0)
    agent.set_path([(2, 0)])
    agent.moving = True

    agent.update(dt=1.0)  # moves 1 unit per second
    assert pytest.approx(agent.x, 0.001) == 1
    assert pytest.approx(agent.y, 0.001) == 0

    agent.update(dt=1.0)
    assert pytest.approx(agent.x, 0.001) == 2
    assert pytest.approx(agent.y, 0.001) == 0
    assert agent.moving is False

def test_partial_movement():
    agent = Agent(0, 0, speed=1.5)
    agent.set_path([(1, 0)])
    agent.moving = True

    agent.update(dt=1.0)  # step > distance
    assert pytest.approx(agent.x, 0.001) == 1
    assert pytest.approx(agent.y, 0.001) == 0
    assert agent.moving is False

def test_empty_path():
    agent = Agent(0, 0)
    agent.moving = True
    agent.update(dt=1.0)
    assert agent.x == 0 and agent.y == 0
    assert agent.moving is True  # Still True because path is empty

def test_diagonal_path():
    agent = Agent(0, 0, speed=1.0)
    agent.set_path([(2, 2)])
    agent.moving = True

    agent.update(dt=1.0)
    assert pytest.approx(agent.x, 0.001) == 0.7071  # moves along diagonal
    assert pytest.approx(agent.y, 0.001) == 0.7071

    agent.update(dt=1.0)
    assert pytest.approx(agent.x, 0.001) == 1.4142
    assert pytest.approx(agent.y, 0.001) == 1.4142
