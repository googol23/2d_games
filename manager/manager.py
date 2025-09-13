import time

from world import World
from world_object import WorldObject
from character import Character, Human
from agent import Agent, MoveMode
from functools import cached_property

import logging
logger = logging.getLogger("manager")
DAY_DURATION_S = 100
DAYS_PER_YEAR = 6

# ---------------- Selection ----------------
class SelectionManager(set):

    def select(self, agent:Agent):
        self.add(agent.id)
        logger.info(f"Agent selected: {agent.id}, {agent.state}")

    def deselect(self, agent:Agent):
        self.discard(agent.id)

    # --- selection methods ---
    def select_by_click(self, agents, mouse_pos, box_size=1, multi=False):
        """
        Select the closest agent to the click inside a box
        Args:
            agents: iterable of Agent objects
            mouse_pos: (mx, my) in world coordinates
            box_size: half-width of the selection box in meters
            multi: keep existing selection if True
        """
        mx, my = mouse_pos
        closest_agent = None
        min_dist_sq = box_size ** 2

        for agent in agents:
            dx = agent.x - mx
            dy = agent.y - my
            dist_sq = dx * dx + dy * dy
            if dist_sq <= min_dist_sq:
                if closest_agent is None or dist_sq < min_dist_sq:
                    closest_agent = agent
                    min_dist_sq = dist_sq

        if not multi:
            self.clear()

        if closest_agent:
            self.select(closest_agent)

    def select_by_box(self, agents, box_start, box_end, multi=False):
        """Select all agents in the rectangular box."""
        x1, y1 = box_start
        x2, y2 = box_end
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)

        if not multi:
            self.clear()

        for agent in agents:
            if left <= agent.x <= right and top <= agent.y <= bottom:
                self.select(agent)

# ----------------- Manager -----------------
class Manager:
    """Handles the updating of dynamic elements in the world.

    Responsibilities:
    - Updates static objects (e.g., trees, plants) based on elapsed time.
    - Updates character positions and other dynamic attributes.
    - Tracks in-game time and supports pause/resume functionality.
    """

    def __init__(self, agents: list[Agent] | None = None,
                 static_objects: list[WorldObject] | None = None,
                 selection_manager: SelectionManager | None = None):
        """
        Initialize the Manager.

        Args:
            world (World, optional): Reference to the game world.
            agents (list[Agents]): List of dynamic agents.
            static_objects (list[WorldObject], optional): List of static world objects.
        """
        self.world = World.get_instance()
        self.agents:dict[int, Agent] = {agent.id: agent for agent in agents}
        self.static_objects = static_objects if static_objects is not None else []

        self.day_counter: int = 0
        self.play_time: float = 0.0  # Accumulated session time while unpaused
        self.start_time: float = time.time()  # Last unpause start timestamp
        self.paused = True  # Tracks pause/resume state

        self._last_update_time: float | None = None  # <-- track last update internally

        self.selection: SelectionManager = SelectionManager() if selection_manager is None else selection_manager

    def get_agents_id(self):
        return self.agents.keys()

    def get_agents(self):
        return self.agents.values()

    def toggle_pause(self):
        """Toggle the paused state of the game."""
        if self.paused:
            self.resume()
        else:
            self.pause()

    def resume(self):
        """Resume the game if it is paused."""
        if self.paused:
            self.start_time = time.time()  # Reset start timestamp
            self._last_update_time = time.time()  # reset for dt calculatio
            self.paused = False

    def pause(self):
        """Pause the game and accumulate elapsed play time."""
        if not self.paused:
            # Add elapsed time since last resume to total play_time
            self.play_time += time.time() - self.start_time
            self.paused = True

    @property
    def session_time(self) -> float:
        """
        Returns the total elapsed session time in seconds.

        Returns:
            float: Total session time, including current unpaused period if applicable.
        """
        if self.paused:
            return self.play_time
        else:
            return self.play_time + (time.time() - self.start_time)

    @property
    def days(self) -> float:
        """
        Returns the total number of in-game days elapsed.

        Returns:
            float: Days elapsed, based on DAY_DURATION_S constant.
        """
        return self.day_counter + self.session_time / DAY_DURATION_S

    def broadcast(self, command, agent_ids):
        for aid in agent_ids:
            if aid in self.agents.keys():
                self.agents[aid].assign_command(command)

    def update_static(self):
        """
        Update static objects like plants and trees based on session time.

        Each object's age is incremented proportional to elapsed days per year.
        """
        elapsed_days = self.session_time / DAY_DURATION_S
        for obj in self.static_objects:
            if hasattr(obj, "age"):
                # Age is incremented fractionally based on DAYS_PER_YEAR
                obj.age += elapsed_days / DAYS_PER_YEAR

    def update_agents(self, dt:float = 0):
        """
        Update all dynamic agents in the world.

        Args:
            dt (float): Time elapsed since the last update (in seconds).
                        Should be computed only while the game is unpaused.
        """
        if self.paused:
            return  # Don't update agents while paused

        for agent in self.agents.values():
            # Update selection modifier
            color = (0,222,0) if agent.id in self.selection else (200,20,20)
            agent.dummy_render_color = color

            # Ensure the agent is updated based on the elapsed time
            agent.update(dt)

    def update(self):
        """
        Update manager state, including agents and static objects.
        Automatically calculates dt based on real time, ignoring paused time.
        """
        if self.paused:
            self._last_update_time = None
            return

        now = time.time()
        if self._last_update_time is None:
            dt = 0
        else:
            dt = now - self._last_update_time
        self._last_update_time = now

        # Update world
        self.update_static()
        self.update_agents(dt)

