import typing

import pygame


class Signal:
    
    def __init__(self):
        self.slots = list()
        
    def connect(self, func):
        self.slots.append(func)
        
    def emit(self, *args, **kwargs):
        for slot in self.slots:
            slot(*args, **kwargs)
            

class Panel:
    
    def __init__(self,
                 rect: typing.Optional[pygame.Rect] = None,
                 parent: typing.Optional['Panel'] = None):
        self._parent = None
        if parent is not None:
            parent.add_panel(self)
        self.rect = rect or pygame.Rect(0, 0, 0, 0)
        self.components = list()
        self.__hovered_components = set()
        self.visible = True
        
        self.mouse_pressed = Signal()
        self.mouse_released = Signal()
        self.mouse_entered = Signal()
        self.mouse_exited = Signal()
        self.mouse_moved = Signal()
    
    @property
    def parent(self) -> 'Panel':
        return self._parent
    
    @parent.setter
    def parent(self, panel: 'Panel'):
        if self.parent is None or panel is None:
            self._parent = panel
        else:
            raise Exception("Panel already has a parent")
        
    def add_panel(self, panel: 'Panel'):
        """Add a new child to that panel."""
        panel.parent = self
        self.components.append(panel)
        
    def remove_panel(self, panel: 'Panel'):
        """Remove a child from the panel."""
        self.components.remove(panel)
        self._hovered_components.discard(panel)
        panel.parent = None
        
    def update(self, *args, **kwargs):
        """Call update on all sprites and panels added to it."""
        self.components.update(*args, **kwargs)
        
    def __on_mouse_pressed(self,
                           pos: typing.Tuple[int, int],
                           event: pygame.event.Event):
        """Propagate a mouse pressed event to all child panels.

        Method called when the mouse button is pressed over the panel.
        Sends a mouse pressed event to all child component adjusting the
        position to the top-left corner of each of them.

        :param pos: cursor position relative to the top-left of the panel
        :param event: mouse event emitted by pygame
        """
        for panel in self.components:
            if panel.rect.collidepoint(pos):
                rel_pos = (pos[0] - panel.rect.x, pos[1] - panel.rect.y)
                panel.__on_mouse_pressed(rel_pos, event)
        self.mouse_pressed.emit(pos, event)
        
    def __on_mouse_released(self,
                            pos: typing.Tuple[int, int],
                            event: pygame.event.Event):
        """Propagate a mouse released event to all child panels.

        Method called when the mouse button is released over the panel.
        Sends a mouse released event to all child component adjusting the
        position to the top-left corner of each of them.

        :param pos: position relative to the top-left corner of the panel
        :param event: mouse event emitted by pygame
        """
        for panel in self.components:
            if panel.rect.collidepoint(pos):
                rel_pos = (pos[0] - panel.rect.x, pos[1] - panel.rect.y)
                panel.__on_mouse_released(rel_pos, event)
        self.mouse_released.emit(pos, event)
        
    def __on_mouse_moved(self,
                         pos: typing.Tuple[int, int],
                         event: pygame.event.Event):
        """Propagate a mouse moved event and sends mouse left/entered signals.

        Method called then the cursor is moved over a panel. If the mouse
        enters/leaves the area of the child component, a corresponding
        function ``on_mouse_entered`` or ``on_mouse_left`` is called.
        Also, sends a mouse moved event to all child panels with ajdusted
        position parameter to be relative to their top-left corner.

        :param pos: position relative to the top-left corner of the panel
        :param event: original event emitted by pygame
        """
        hovered = set()
        for panel in self.components:
            if panel.rect.collidepoint(pos):
                rel_pos = (pos[0] - panel.rect.x, pos[1] - panel.rect.y)
                panel.__on_mouse_moved(rel_pos, event)
                hovered.add(panel)
        self.mouse_moved.emit(pos, event)
        for panel in hovered.difference(self.__hovered_components):
            panel.__on_mouse_entered(event)
        for panel in self.__hovered_components.difference(hovered):
            panel.__on_mouse_exited(event)
        self.__hovered_components = hovered
        
    def __on_mouse_entered(self, event):
        """Called when mouse enters the panel area."""
        self.mouse_entered.emit(event)
        
    def __on_mouse_exited(self, event):
        """Called when mouse leaves the panel area."""
        for panel in self.__hovered_components:
            panel.__on_mouse_exited(event)
        self.mouse_exited.emit(event)
        self.__hovered_components.clear()
        
    def paint(self, canvas: pygame.Surface):
        """Paint the panel surface and it's children.

        This method should be extended in the subclasses and provide
        drawing capability of the panel. In order to repaint the
        child panels ``super().paint(canvas)`` should be called.

        :param canvas: pygame surface for drawing.
        """
        for panel in self.components:
            if panel.visible:
                panel.paint(canvas.subsurface(panel.rect))

    def get_canvas(self) -> pygame.Surface:
        return self.parent.get_canvas().subsurface(self.rect)
    

class TopLevelPanel(Panel):
    """
    Specialised subclass of ``Panel`` suited to be a parent window.
    It has it's own drawing surface instead of delegating painting
    to the parent's surface.
    """
    
    def __init__(self, surface: pygame.Surface):
        super().__init__(rect=surface.get_rect(), parent=None)
        self.surface = surface

    def render(self):
        self.paint(self.get_canvas())
        
    def get_canvas(self) -> pygame.Surface:
        return self.surface
    
    def dispatch_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self._Panel__on_mouse_moved(event.pos, event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._Panel__on_mouse_pressed(event.pos, event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._Panel__on_mouse_released(event.pos, event)
