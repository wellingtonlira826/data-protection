"""
Presidio com suporte completo ao português brasileiro.
Detecta e anonimiza: CPF, CNPJ, RG, CEP, Telefone BR, CNH, PIS/PASEP,
Título de Eleitor, nomes, emails, URLs e mais.
"""

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine


def _build_registry() -> RecognizerRegistry:
    registry = RecognizerRegistry(supported_languages=["pt", "en"])
    registry.load_predefined_recognizers(languages=["pt", "en"])

    recognizers = [
        PatternRecognizer(
            supported_entity="CPF",
            supported_language="pt",
            patterns=[
                Pattern("CPF formatado", r"\d{3}\.\d{3}\.\d{3}-\d{2}", 0.9),
                Pattern("CPF sem formatação", r"\b\d{11}\b", 0.5),
            ],
        ),
        PatternRecognizer(
            supported_entity="CNPJ",
            supported_language="pt",
            patterns=[
                Pattern("CNPJ formatado", r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", 0.9),
                Pattern("CNPJ sem formatação", r"\b\d{14}\b", 0.5),
            ],
        ),
        PatternRecognizer(
            supported_entity="RG",
            supported_language="pt",
            patterns=[
                Pattern("RG formatado", r"\d{1,2}\.\d{3}\.\d{3}-[\dxX]", 0.85),
                Pattern("RG SP", r"\b\d{8,9}\b", 0.4),
            ],
        ),
        PatternRecognizer(
            supported_entity="CEP",
            supported_language="pt",
            patterns=[
                Pattern("CEP formatado", r"\d{5}-\d{3}", 0.9),
                Pattern("CEP sem formatação", r"\b\d{8}\b", 0.4),
            ],
        ),
        PatternRecognizer(
            supported_entity="TELEFONE_BR",
            supported_language="pt",
            patterns=[
                Pattern("Celular BR", r"(\+55\s?)?(\(?\d{2}\)?\s?)9\d{4}[-\s]?\d{4}", 0.9),
                Pattern("Fixo BR", r"(\+55\s?)?(\(?\d{2}\)?\s?)\d{4}[-\s]?\d{4}", 0.8),
            ],
        ),
        PatternRecognizer(
            supported_entity="CNH",
            supported_language="pt",
            patterns=[
                Pattern("CNH", r"\b\d{11}\b", 0.4),  # complementado por contexto
            ],
            context=["cnh", "habilitação", "carteira de motorista", "renach"],
        ),
        PatternRecognizer(
            supported_entity="PIS_PASEP",
            supported_language="pt",
            patterns=[
                Pattern("PIS/PASEP formatado", r"\d{3}\.\d{5}\.\d{2}-\d", 0.9),
            ],
        ),
        PatternRecognizer(
            supported_entity="TITULO_ELEITOR",
            supported_language="pt",
            patterns=[
                Pattern("Título de Eleitor", r"\b\d{12}\b", 0.4),
            ],
            context=["título de eleitor", "titulo eleitor", "zona eleitoral", "seção eleitoral"],
        ),
        PatternRecognizer(
            supported_entity="CARTAO_CREDITO",
            supported_language="pt",
            patterns=[
                Pattern("Cartão formatado", r"\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}", 0.95),
                Pattern("Cartão sem formatação", r"\b\d{16}\b", 0.5),
            ],
            context=["cartão", "visa", "mastercard", "crédito", "débito", "cvv"],
        ),
        PatternRecognizer(
            supported_entity="EMAIL_ADDRESS",
            supported_language="pt",
            patterns=[
                Pattern("Email", r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", 0.95),
            ],
        ),
        # ── Secrets e credenciais (risco OWASP LLM Top 10) ───────────────────
        PatternRecognizer(
            supported_entity="JWT_TOKEN",
            supported_language="pt",
            patterns=[
                Pattern(
                    "JWT",
                    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
                    0.97,
                ),
            ],
            context=["bearer", "authorization", "token", "jwt", "access_token"],
        ),
        PatternRecognizer(
            supported_entity="AWS_ACCESS_KEY",
            supported_language="pt",
            patterns=[
                Pattern("AWS Access Key", r"AKIA[0-9A-Z]{16}", 0.99),
                Pattern("AWS Secret Key", r"(?i)aws.{0,20}secret.{0,10}['\"]?[A-Za-z0-9/+=]{40}['\"]?", 0.90),
            ],
        ),
        PatternRecognizer(
            supported_entity="GITHUB_TOKEN",
            supported_language="pt",
            patterns=[
                Pattern("GitHub PAT", r"gh[pousr]_[A-Za-z0-9]{36,}", 0.99),
                Pattern("GitHub App Token", r"ghs_[A-Za-z0-9]{36,}", 0.99),
            ],
        ),
        PatternRecognizer(
            supported_entity="PRIVATE_KEY",
            supported_language="pt",
            patterns=[
                Pattern(
                    "PEM Private Key",
                    r"-----BEGIN (RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----",
                    0.99,
                ),
            ],
        ),
        PatternRecognizer(
            supported_entity="CONNECTION_STRING",
            supported_language="pt",
            patterns=[
                Pattern(
                    "DB Connection String",
                    r"(postgresql|postgres|mysql|mongodb(\+srv)?|redis|amqp|mssql|oracle)://[^\s\"'<>]{8,}",
                    0.95,
                ),
            ],
        ),
        PatternRecognizer(
            supported_entity="SECRET_IN_CONTEXT",
            supported_language="pt",
            patterns=[
                Pattern(
                    "Key=Value Secret",
                    r"(?i)(api[_\-]?key|apikey|secret[_\-]?key|password|passwd|senha|token|bearer"
                    r"|credential|auth[_\-]?token|access[_\-]?token|private[_\-]?key)\s*[=:]\s*"
                    r"['\"]?[A-Za-z0-9_\-\.]{10,}['\"]?",
                    0.80,
                ),
            ],
            context=[
                "authorization", "auth", "authenticate", "secret", "password",
                "senha", "token", "key", "credential", "api",
            ],
        ),
    ]

    for r in recognizers:
        registry.add_recognizer(r)

    return registry


def build_analyzer() -> AnalyzerEngine:
    """Cria e retorna um AnalyzerEngine configurado para português."""
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "pt", "model_name": "pt_core_news_lg"},
            {"lang_code": "en", "model_name": "en_core_web_lg"},
        ],
    })
    nlp_engine = provider.create_engine()
    registry = _build_registry()
    return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=["pt", "en"])


def analisar(texto: str, analyzer: AnalyzerEngine | None = None) -> list:
    """Detecta PII em português. Retorna lista de ResultadoPII."""
    if analyzer is None:
        analyzer = build_analyzer()
    return analyzer.analyze(text=texto, language="pt")


def anonimizar(texto: str, analyzer: AnalyzerEngine | None = None) -> str:
    """Detecta e anonimiza PII em português. Retorna texto limpo."""
    if analyzer is None:
        analyzer = build_analyzer()
    anonymizer = AnonymizerEngine()
    resultados = analyzer.analyze(text=texto, language="pt")
    return anonymizer.anonymize(text=texto, analyzer_results=resultados).text


def imprimir_deteccoes(texto: str, analyzer: AnalyzerEngine | None = None) -> None:
    """Imprime todas as detecções de PII encontradas no texto."""
    if analyzer is None:
        analyzer = build_analyzer()
    resultados = analyzer.analyze(text=texto, language="pt")
    if not resultados:
        print("Nenhum PII detectado.")
        return
    print(f"{'Tipo':<20} {'Valor':<35} {'Confiança':>10}")
    print("-" * 68)
    for r in sorted(resultados, key=lambda x: x.start):
        valor = texto[r.start:r.end]
        print(f"{r.entity_type:<20} {valor:<35} {r.score:>10.0%}")


if __name__ == "__main__":
    print("Inicializando Presidio com suporte a português...\n")
    analyzer = build_analyzer()

    exemplos = [
        "Meu CPF é 123.456.789-09 e meu email é joao@empresa.com.br",
        "CNPJ da empresa: 12.345.678/0001-90, CEP: 01310-100",
        "RG: 12.345.678-9, telefone: (11) 98765-4321",
        "PIS: 123.45678.90-1, cartão: 4111 1111 1111 1111",
        "João Silva mora na Rua das Flores, 123 - São Paulo",
    ]

    for texto in exemplos:
        print(f"TEXTO: {texto}")
        imprimir_deteccoes(texto, analyzer)
        print(f"ANONIMIZADO: {anonimizar(texto, analyzer)}")
        print()
