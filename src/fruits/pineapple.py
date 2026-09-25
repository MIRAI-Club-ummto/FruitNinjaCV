from .fruit import Fruit


class Pineapple(Fruit):
    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        super().__init__(x, y, vx, vy,
                         radius=62,
                         image_path="pineapple.png",
                         points=2)

    @property
    def color(self) -> tuple[int, int, int]:
        return (255, 220, 0)   # jaune

    @property
    def name(self) -> str:
        return "Pineapple"
