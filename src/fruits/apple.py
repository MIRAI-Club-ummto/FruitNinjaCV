from .fruit import Fruit


class Apple(Fruit):
    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        super().__init__(x, y, vx, vy,
                         radius=46,
                         image_path="apple.png",
                         points=1)

    @property
    def color(self) -> tuple[int, int, int]:
        return (220, 50, 50)   # rouge

    @property
    def name(self) -> str:
        return "Apple"
