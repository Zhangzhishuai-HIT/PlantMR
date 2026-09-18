"""Plant-native Mendelian randomization toolkit."""

__version__ = "1.1.0"

from .gxe import GxEResult, gxe_ivw, select_gxe_instruments

__all__ = ["GxEResult", "gxe_ivw", "select_gxe_instruments", "__version__"]
