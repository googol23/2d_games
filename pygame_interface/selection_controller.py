import pygame
from  manager import SelectionManager
class PygameSelectionController:
    def __init__(self, selection_manager: SelectionManager, box_size: float=20):
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
                self.drag_end = event.pos
                if self.dragging:
                    # Detect shift/ctrl for multi-selection
                    multi = pygame.key.get_mods() & pygame.KMOD_SHIFT

                    # If mouse moved enough, do box selection
                    if abs(self.drag_start[0]-self.drag_end[0]) > 5 or abs(self.drag_start[1]-self.drag_end[1]) > 5:
                        self.selection_manager.select_by_box(agents, self.drag_start, self.drag_end, multi=multi)
                    else:
                        # Otherwise, do click selection
                        self.selection_manager.select_by_click(agents, self.drag_end, box_size=self.box_size, multi=multi)
                self.dragging = False

    def draw_drag_box(self, surface):
        """Draw the current drag rectangle on the given surface (optional for feedback)."""
        if self.dragging:
            x1, y1 = self.drag_start
            x2, y2 = pygame.mouse.get_pos()
            rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            pygame.draw.rect(surface, (0, 255, 255), rect, 1)
