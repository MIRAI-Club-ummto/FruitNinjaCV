from .fruit import Fruit


class Watermelon(Fruit):
    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        super().__init__(x, y, vx, vy,
                         radius=62,
                         image_path="watermelon.png",
                         points=3)

    @property
    def color(self) -> tuple[int, int, int]:
        return (50, 180, 80)   # vert

    @property
    def name(self) -> str:
        return "Watermelon"
