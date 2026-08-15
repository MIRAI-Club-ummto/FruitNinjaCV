from .fruit import Fruit


class Orange(Fruit):
    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        super().__init__(x, y, vx, vy,
                         radius=44,
                         image_path="orange.png",
                         points=2)

    @property
    def color(self) -> tuple[int, int, int]:
        return (255, 140, 0)   # orange

    @property
    def name(self) -> str:
        return "Orange"
