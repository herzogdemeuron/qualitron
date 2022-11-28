import colorsys


class Color:
    """
    Class for basic color operations.
    """

    def __init__(self):
        """
        Inits a new Color instance.
        """
        pass
    
    @staticmethod
    def HSVtoRGB(hsv):
        """
        Convert a color from hsv to rgb.

        Args:
            hsv (tuple): A color in hsv format.

        Returns:
            tuple: A color in rgb format
        """
        return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2]))

    @staticmethod
    def RGBtoHEX(rgb):
        return '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])

    @staticmethod
    def HEXtoRGB(hex):
        """
        Converts a hex color string to rgb.

        Args:
            hex (sting): The hex color

        Returns:
            tuple: The rgb color
        """
        hex = hex.lstrip('#')
        return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

