import pygame
from  manager import SelectionManager
from camera import Camera

import logging
logger = logging.getLogger("pgi")

class PGISelectionController:
    def __init__(self, selection_manager: SelectionManager, camera: Camera, box_size: float=20):
        """
        Args:
            selection_manager (SelectionManager): your selection backend
            box_size (float): tolerance in pixels for click selection
        """
        self.selection_manager:SelectionManager = selection_manager
        self.box_size: float = box_size
        self.dragging: bool = False
        self.drag_start: tuple[float,float] = (0, 0)
        self.drag_end: tuple[float,float] = (0, 0)
        self.camera: Camera = camera

    def handle_events(self, events, agents):
        """
        Handle pygame events and update selection.

        Args:
            events: list of pygame events from pygame.event.get()
            agents: list of Agent objects
        """
        for event in events:
            # --- Left mouse button down: start drag ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.drag_start = event.pos
                self.dragging = True

            # --- Left mouse button up: finalize selection ---
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.drag_end = event.pos

                    # Detect shift/ctrl for multi-selection
                    mods = pygame.key.get_mods()
                    multi = (mods & pygame.KMOD_SHIFT) or (mods & pygame.KMOD_CTRL)

                    dx = self.drag_end[0] - self.drag_start[0]
                    dy = self.drag_end[1] - self.drag_start[1]

                    if dx*dx + dy*dy > 25:  # drag selection if moved more than 5px
                        # convert to world coords only here
                        start_world = self.camera.screen_to_world(*self.drag_start)
                        end_world   = self.camera.screen_to_world(*self.drag_end)
                        self.selection_manager.select_by_box(
                            agents, start_world, end_world, multi=multi
                        )
                        logger.info(f"Calling select_by_box(({self.drag_start}){start_world}, ({self.drag_end}){end_world})")
                    else:
                        # convert click position to world coords
                        end_world = self.camera.screen_to_world(*self.drag_end)
                        self.selection_manager.select_by_click(
                            agents, end_world, box_size=self.box_size, multi=multi
                        )
                        logger.info(f"Calling select_by_click({end_world})")
                self.dragging = False

    def draw_drag_box(self, surface):
        """Draw the current drag rectangle on the given surface (optional for feedback)."""
        if self.dragging:
            x1, y1 = self.drag_start
            x2, y2 = pygame.mouse.get_pos()
            rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            pygame.draw.rect(surface, (0, 255, 255), rect, 1)
