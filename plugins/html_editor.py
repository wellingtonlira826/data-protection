"""
Componente Streamlit de editor HTML com suporte a paste do Outlook.

Captura o evento de paste e preserva o HTML completo (formatação,
imagens inline base64, links), enviando de volta ao Python via
protocolo de componentes Streamlit.
"""
from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent / "html_editor_component"

_html_paste_editor = components.declare_component(
    "html_paste_editor",
    path=str(_COMPONENT_DIR),
)


def html_paste_editor(value: str = "", key: str | None = None) -> str:
    """Editor HTML que preserva conteúdo colado do Outlook (imagens, formatação).

    Returns:
        HTML string confirmado pelo usuário via "Salvar assinatura",
        ou string vazia se nenhuma ação foi tomada.
    """
    result = _html_paste_editor(value=value, key=key, default=None)
    return result if result is not None else value
