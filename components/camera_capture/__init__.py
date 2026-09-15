from pathlib import Path
from typing import Optional
import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent
_camera_capture = components.declare_component("camera_capture", path=str(_COMPONENT_DIR))


def camera_capture(key: Optional[str] = None) -> Optional[str]:
    """Retorna a foto capturada como data URL base64, ou None se ainda não houver captura."""
    return _camera_capture(key=key, default=None)
