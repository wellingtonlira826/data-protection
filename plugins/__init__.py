"""
Plugins do Presidio PT — Data Protection & AI Security.

Submódulos:
    risk_scorer       → Classificação de risco de entidades PII e secrets.
    frameworks        → Mapeamento PII/secrets → frameworks regulatórios e AI Security.
    jira_plugin       → Plugin de integração com Jira Cloud/Server.
    confluence_plugin → Plugin de integração com Confluence Cloud/Server.
    scan_state        → Persistência de estado incremental via SQLite.
    scanner           → Processamento paralelo de chunks com ThreadPoolExecutor.
    scheduler         → Agendamento de varreduras periódicas (APScheduler + SQLite).
    demo_data         → Datasets fictícios para validação sem credenciais.
"""

from plugins.risk_scorer import (
    score,
    score_nivel,
    score_label,
    sort_key,
    RISK_MAP,
)
from plugins.frameworks import (
    PII_FRAMEWORK_MAP,
    AI_FRAMEWORKS,
    NIVEL_COR,
    NIVEL_LABELS,
    frameworks_para_entidade,
    frameworks_impactados,
)
from plugins.jira_plugin import (
    JiraPlugin,
    ISSUE_TYPES_PADRAO,
    CAMPOS_DISPONIVEIS,
)
from plugins.jira_actions import (
    JiraActions,
    LABEL_SECRET,
    LABEL_PII_HIGH,
    LABEL_PII_MEDIUM,
    LABEL_REVIEWED,
    LABEL_SCRUBBED,
)
from plugins.confluence_plugin import (
    ConfluencePlugin,
    PAGE_STATUS_MAP,
)
from plugins.scan_state import (
    ScanStateStore,
    DEFAULT_DB_PATH,
)
from plugins.attachment_scanner import (
    AnexoInfo,
    ResultadoAnexo,
    escanear_anexos,
    extrair_texto,
    MIME_SUPORTADOS,
    MAX_TAMANHO_BYTES,
)
from plugins.scanner import (
    scan_chunks,
    resumir,
    ResultadoChunk,
    Deteccao,
    SECRET_ENTITIES,
)
from plugins.scheduler import (
    ScanScheduler,
    DEFAULT_SCHEDULE_DB as DEFAULT_SCHEDULE_DB_PATH,
    _cron_para_descricao,
    FREQ_CRON,
    DIA_SEMANA_NUM,
)
from plugins.demo_data import (
    JIRA_DEMO_TRECHOS,
    CONFLUENCE_DEMO_TRECHOS,
    JIRA_DEMO_PROJETOS,
    CONFLUENCE_DEMO_SPACES,
    EXEC_DEMO_HISTORICO,
)

__all__ = [
    # Risk scorer
    "score",
    "score_nivel",
    "score_label",
    "sort_key",
    "RISK_MAP",
    # Frameworks
    "PII_FRAMEWORK_MAP",
    "AI_FRAMEWORKS",
    "NIVEL_COR",
    "NIVEL_LABELS",
    "frameworks_para_entidade",
    "frameworks_impactados",
    # Jira plugin
    "JiraPlugin",
    "ISSUE_TYPES_PADRAO",
    "CAMPOS_DISPONIVEIS",
    # Jira actions
    "JiraActions",
    "LABEL_SECRET",
    "LABEL_PII_HIGH",
    "LABEL_PII_MEDIUM",
    "LABEL_REVIEWED",
    # Confluence plugin
    "ConfluencePlugin",
    "PAGE_STATUS_MAP",
    # Scan state
    "ScanStateStore",
    "DEFAULT_DB_PATH",
    # Attachment scanner
    "AnexoInfo",
    "ResultadoAnexo",
    "escanear_anexos",
    "extrair_texto",
    "MIME_SUPORTADOS",
    "MAX_TAMANHO_BYTES",
    # Scanner paralelo
    "scan_chunks",
    "resumir",
    "ResultadoChunk",
    "Deteccao",
    "SECRET_ENTITIES",
    # Scheduler
    "ScanScheduler",
    "DEFAULT_SCHEDULE_DB_PATH",
    "FREQ_CRON",
    "DIA_SEMANA_NUM",
    # Demo data
    "JIRA_DEMO_TRECHOS",
    "CONFLUENCE_DEMO_TRECHOS",
    "JIRA_DEMO_PROJETOS",
    "CONFLUENCE_DEMO_SPACES",
    "EXEC_DEMO_HISTORICO",
    # Jira actions extras
    "LABEL_SCRUBBED",
]
