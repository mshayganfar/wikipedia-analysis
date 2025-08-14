class ColorPalette:
    def __init__(self, colors):
        self.colors = colors

class PastelPalette(ColorPalette):
    def __init__(self):
        super().__init__(["#ffe6e6", "#ffd7be", "#ffffb3", "#c9e4ca", "#b2bec3", "#eaebef"])

class BrightPalette(ColorPalette):
    def __init__(self):
        super().__init__(["#ff69b4", "#ffb31a", "#ffff00", "#33cc33", "#0099cc", "#6600cc"])

class DarkPalette(ColorPalette):
    def __init__(self):
        super().__init__(["#333333", "#666666", "#999999", "#cccccc", "#b3b3b3", "#e6e6e6"])

class NeutralPalette(ColorPalette):
    def __init__(self):
        super().__init__(["#f5f5f5", "#e5e5e5", "#d3d3d3", "#bdbdbd", "#9c9c9c", "#808080"])

class RGBPalette(ColorPalette):
    def __init__(self):
        super().__init__(["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"])    

def get_all_color_palettes():
    return {
        "pastel": PastelPalette(),
        "bright": BrightPalette(),
        "dark": DarkPalette(),
        "neutral": NeutralPalette(),
        "rgb": RGBPalette()
    }