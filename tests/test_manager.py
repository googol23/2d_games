import time
import pytest
from manager import Manager
from agent import Agent
from world_object import WorldObject

class DummyObject:
    """Used to test static object age updates."""
    def __init__(self):
        self.age = 0

class DummyAgent(Agent):
    """Agent with controlled update to track calls."""
    def __init__(self):
        super().__init__(0, 0)
        self.updated_with_dt = None

    def update(self, dt: float = 0):
        self.updated_with_dt = dt

def test_initialization():
    mgr = Manager()
    assert mgr.agents == []
    assert mgr.static_objects == []
    assert mgr.paused is True
    assert isinstance(mgr._last_update_time, type(None))
    assert mgr.play_time == 0

def test_pause_resume_toggle():
    mgr = Manager()
    mgr.resume()
    assert mgr.paused is False
    start = mgr.start_time

    mgr.pause()
    assert mgr.paused is True
    assert mgr.play_time >= 0

    mgr.toggle_pause()
    assert mgr.paused is False
    mgr.toggle_pause()
    assert mgr.paused is True

def test_session_time_and_days(monkeypatch):
    mgr = Manager()
    fake_time = [1000]

    def fake_time_func():
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_time_func)

    mgr.resume()
    fake_time[0] += 50
    assert mgr.session_time == 50
    expected_days = 50 / 100
    assert mgr.days == expected_days

    mgr.pause()
    assert mgr.session_time == 50

def test_update_static():
    obj = DummyObject()
    mgr = Manager(static_objects=[obj])
    mgr.resume()

    # Simulate session_time of 60
    mgr.play_time = 60
    mgr.update_static()
    # Age increment: (session_time / DAY_DURATION_S) / DAYS_PER_YEAR = (60/100)/6 = 0.1
    assert pytest.approx(obj.age, 0.001) == 0.1

def test_update_agents_paused_unpaused():
    agent = DummyAgent()
    mgr = Manager(agents=[agent])

    # Paused: should not call agent.update
    mgr.update_agents(dt=1.0)
    assert agent.updated_with_dt is None

    mgr.resume()
    mgr.update_agents(dt=2.0)
    assert agent.updated_with_dt == 2.0

def test_update_dt_calculation(monkeypatch):
    agent = DummyAgent()
    mgr = Manager(agents=[agent])
    mgr.resume()

    fake_time = [1000]
    def fake_time_func():
        return fake_time[0]

    monkeypatch.setattr(time, "time", fake_time_func)

    # First call: _last_update_time is None -> dt = 0
    mgr._last_update_time = None
    mgr.update()
    assert agent.updated_with_dt == 0

    # Second call: dt = now - _last_update_time
    mgr._last_update_time = 999
    mgr.update()
    assert agent.updated_with_dt == 1  # 1000 - 999

def test_update_paused_resets_last_update():
    agent = DummyAgent()
    mgr = Manager(agents=[agent])
    mgr.resume()
    mgr._last_update_time = 1234
    mgr.paused = True
    mgr.update()
    assert mgr._last_update_time is None
