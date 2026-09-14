"""
Extração de texto de anexos Jira/Confluence para detecção de PII e secrets.

Tipos suportados:
    Imagem (PNG/JPG/TIFF/BMP)  → OCR via pytesseract + Pillow
    PDF (texto nativo)         → pdfminer.six
    PDF (escaneado)            → OCR via pytesseract após rasterização
    DOCX                       → python-docx
    XLSX / XLS                 → openpyxl
    CSV / TXT                  → decodificação direta

Dependências são opcionais — cada extrator falha graciosamente se o
pacote não estiver instalado, e reporta o motivo no campo `erro`.

Instalar tudo:  pip install "data-protection-plugins[attachments]"
"""
from __future__ import annotations

import io
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from presidio_analyzer import AnalyzerEngine

from plugins.scanner import scan_chunks, ResultadoChunk

logger = logging.getLogger(__name__)

# ── Imports opcionais ─────────────────────────────────────────────────────────

try:
    from PIL import Image as _PILImage
    import pytesseract as _pytesseract
    _HAS_OCR = True
except ImportError:
    _HAS_OCR = False

try:
    from pdfminer.high_level import extract_text as _pdf_extract_text
    _HAS_PDFMINER = True
except ImportError:
    _HAS_PDFMINER = False

try:
    from docx import Document as _DocxDocument
    _HAS_DOCX = True
except ImportError:
    _HAS_DOCX = False

try:
    from openpyxl import load_workbook as _load_workbook
    _HAS_OPENPYXL = True
except ImportError:
    _HAS_OPENPYXL = False

# ── Constantes ────────────────────────────────────────────────────────────────

MAX_TAMANHO_BYTES: int = 10 * 1024 * 1024  # 10 MB — pula anexos maiores

MIME_IMAGEM: frozenset[str] = frozenset({
    "image/png", "image/jpeg", "image/jpg",
    "image/tiff", "image/bmp", "image/gif", "image/webp",
})
MIME_PDF: frozenset[str] = frozenset({"application/pdf"})
MIME_DOCX: frozenset[str] = frozenset({
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
})
MIME_XLSX: frozenset[str] = frozenset({
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
})
MIME_TEXTO: frozenset[str] = frozenset({"text/plain", "text/csv", "text/comma-separated-values"})

MIME_SUPORTADOS: frozenset[str] = MIME_IMAGEM | MIME_PDF | MIME_DOCX | MIME_XLSX | MIME_TEXTO


# ── Tipos ─────────────────────────────────────────────────────────────────────

@dataclass
class AnexoInfo:
    """Metadados de um anexo Jira ou Confluence."""

    id: str
    nome: str
    mime_type: str
    tamanho: int          # bytes
    url_download: str
    parent_key: str       # issue_key (Jira) ou page_id (Confluence)
    source: str           # "jira" | "confluence"


# ── Extratores de texto ───────────────────────────────────────────────────────

def _extrair_imagem(conteudo: bytes) -> str:
    if not _HAS_OCR:
        raise ImportError("pytesseract e Pillow necessários: pip install Pillow pytesseract")
    image = _PILImage.open(io.BytesIO(conteudo))
    return _pytesseract.image_to_string(image, lang="por+eng")


def _extrair_pdf(conteudo: bytes) -> str:
    if not _HAS_PDFMINER:
        raise ImportError("pdfminer.six necessário: pip install pdfminer.six")
    texto = _pdf_extract_text(io.BytesIO(conteudo))
    # PDF escaneado: pdfminer retorna vazio — fallback para OCR se disponível
    if not texto.strip() and _HAS_OCR:
        return _ocr_pdf(conteudo)
    return texto or ""


def _ocr_pdf(conteudo: bytes) -> str:
    """OCR de PDF escaneado — requer pdf2image + poppler instalados."""
    try:
        from pdf2image import convert_from_bytes  # type: ignore[import]
    except ImportError:
        logger.warning("PDF escaneado ignorado — instale pdf2image e poppler para OCR de PDFs.")
        return ""
    paginas = convert_from_bytes(conteudo, dpi=200)
    textos = [_pytesseract.image_to_string(p, lang="por+eng") for p in paginas]
    return "\n".join(textos)


def _extrair_docx(conteudo: bytes) -> str:
    if not _HAS_DOCX:
        raise ImportError("python-docx necessário: pip install python-docx")
    doc = _DocxDocument(io.BytesIO(conteudo))
    partes: list[str] = []
    for paragrafo in doc.paragraphs:
        if paragrafo.text.strip():
            partes.append(paragrafo.text.strip())
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                if celula.text.strip():
                    partes.append(celula.text.strip())
    return "\n".join(partes)


def _extrair_xlsx(conteudo: bytes) -> str:
    if not _HAS_OPENPYXL:
        raise ImportError("openpyxl necessário: pip install openpyxl")
    wb = _load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    partes: list[str] = []
    for ws in wb.worksheets:
        for linha in ws.iter_rows(values_only=True):
            for celula in linha:
                if celula and isinstance(celula, str) and celula.strip():
                    partes.append(celula.strip())
    wb.close()
    return "\n".join(partes)


def _extrair_texto(conteudo: bytes) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return conteudo.decode(encoding)
        except UnicodeDecodeError:
            continue
    return conteudo.decode("utf-8", errors="replace")


def extrair_texto(conteudo: bytes, mime_type: str, nome: str) -> str:
    """Despacha para o extrator correto com base no tipo MIME."""
    mime = mime_type.lower().split(";")[0].strip()

    if mime in MIME_IMAGEM:
        return _extrair_imagem(conteudo)
    if mime in MIME_PDF:
        return _extrair_pdf(conteudo)
    if mime in MIME_DOCX:
        return _extrair_docx(conteudo)
    if mime in MIME_XLSX:
        return _extrair_xlsx(conteudo)
    if mime in MIME_TEXTO:
        return _extrair_texto(conteudo)

    # Fallback: tenta ler como texto se não binário pelo nome
    ext = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    if ext in ("txt", "csv", "log", "md", "json", "xml", "yaml", "yml"):
        return _extrair_texto(conteudo)

    raise ValueError(f"Tipo MIME nao suportado: {mime_type} ({nome})")


# ── Chunk para reutilizar pipeline do scanner.py ──────────────────────────────

def _anexo_para_chunk(info: AnexoInfo, texto: str) -> dict[str, Any]:
    """Converte anexo em formato de chunk compatível com scan_chunks."""
    return {
        "texto": texto,
        "autor": "desconhecido",
        "campo": f"Anexo ({info.mime_type}): {info.nome}",
        "issue_key": info.parent_key,
        "issue_url": "",
        "issue_type": "attachment",
        "prioridade": "",
        # campos extras para identificação na UI
        "anexo_id": info.id,
        "anexo_nome": info.nome,
        "anexo_mime": info.mime_type,
        "anexo_tamanho": info.tamanho,
        "anexo_source": info.source,
    }


# ── Scanner de um anexo ───────────────────────────────────────────────────────

@dataclass
class ResultadoAnexo:
    """Resultado de scan de um anexo individual."""

    info: AnexoInfo
    resultado: ResultadoChunk | None = None
    erro: str | None = None
    ignorado: bool = False
    motivo_ignorado: str = ""

    @property
    def total_deteccoes(self) -> int:
        return self.resultado.total_deteccoes if self.resultado else 0

    @property
    def tem_high(self) -> bool:
        return self.resultado.tem_high if self.resultado else False

    @property
    def tem_secret(self) -> bool:
        return self.resultado.tem_secret if self.resultado else False


def escanear_anexo(
    info: AnexoInfo,
    conteudo: bytes,
    analyzer: AnalyzerEngine,
    language: str = "pt",
) -> ResultadoAnexo:
    """Extrai texto de um anexo e executa análise de PII/secrets."""
    if info.tamanho > MAX_TAMANHO_BYTES:
        return ResultadoAnexo(
            info=info,
            ignorado=True,
            motivo_ignorado=f"Anexo ignorado: tamanho {info.tamanho / 1_048_576:.1f} MB > limite {MAX_TAMANHO_BYTES / 1_048_576:.0f} MB",
        )

    mime = info.mime_type.lower().split(";")[0].strip()
    if mime not in MIME_SUPORTADOS:
        ext = info.nome.rsplit(".", 1)[-1].lower() if "." in info.nome else ""
        if ext not in ("txt", "csv", "log", "md", "json", "xml", "yaml", "yml"):
            return ResultadoAnexo(
                info=info,
                ignorado=True,
                motivo_ignorado=f"Tipo nao suportado: {info.mime_type}",
            )

    try:
        texto = extrair_texto(conteudo, info.mime_type, info.nome)
    except Exception as exc:
        logger.warning("Erro ao extrair texto de '%s': %s", info.nome, exc)
        return ResultadoAnexo(info=info, erro=str(exc))

    if not texto.strip():
        return ResultadoAnexo(
            info=info,
            ignorado=True,
            motivo_ignorado="Texto vazio apos extracao",
        )

    chunk = _anexo_para_chunk(info, texto)
    resultados = scan_chunks([chunk], analyzer, language=language, max_workers=1)
    resultado = resultados[0] if resultados else None

    return ResultadoAnexo(info=info, resultado=resultado)


# ── Scanner paralelo de múltiplos anexos ─────────────────────────────────────

def escanear_anexos(
    anexos: list[tuple[AnexoInfo, bytes]],
    analyzer: AnalyzerEngine,
    language: str = "pt",
    max_workers: int = 4,
    progress_cb: Callable[[int, int], None] | None = None,
) -> list[ResultadoAnexo]:
    """Processa lista de anexos em paralelo.

    Args:
        anexos: Lista de (AnexoInfo, conteúdo em bytes).
        analyzer: AnalyzerEngine compartilhado entre threads.
        language: Idioma para análise.
        max_workers: Threads paralelas (padrão 4 — menor que text scan por ser mais pesado).
        progress_cb: Callback(concluidos, total) para progresso.

    Returns:
        Lista de ResultadoAnexo na mesma ordem de entrada.
    """
    total = len(anexos)
    if total == 0:
        return []

    resultados: list[ResultadoAnexo | None] = [None] * total
    concluidos = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(escanear_anexo, info, conteudo, analyzer, language): idx
            for idx, (info, conteudo) in enumerate(anexos)
        }

        for future in as_completed(futures):
            idx = futures[future]
            try:
                resultados[idx] = future.result()
            except Exception as exc:
                logger.error("Worker falhou no anexo %d: %s", idx, exc)
                resultados[idx] = ResultadoAnexo(info=anexos[idx][0], erro=str(exc))

            concluidos += 1
            if progress_cb:
                try:
                    progress_cb(concluidos, total)
                except Exception:
                    pass

    final = [r for r in resultados if r is not None]

    detectados = sum(1 for r in final if r.total_deteccoes > 0)
    ignorados = sum(1 for r in final if r.ignorado)
    logger.info(
        "Scan de anexos: %d total | %d com deteccoes | %d ignorados",
        len(final), detectados, ignorados,
    )
    return final
