"""
Plugins do Presidio PT — Data Protection & AI Security.

Submódulos:
    risk_scorer   → Classificação de risco de entidades PII.
    frameworks    → Mapeamento PII → frameworks regulatórios e AI Security.
    jira_plugin   → Plugin de integração com Jira Cloud/Server.
    confluence_plugin → Plugin de integração com Confluence Cloud/Server.
    demo_data     → Datasets fictícios para validação sem credenciais.
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
from plugins.confluence_plugin import (
    ConfluencePlugin,
    PAGE_STATUS_MAP,
)
from plugins.demo_data import (
    JIRA_DEMO_TRECHOS,
    CONFLUENCE_DEMO_TRECHOS,
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
    # Confluence plugin
    "ConfluencePlugin",
    "PAGE_STATUS_MAP",
    # Demo data
    "JIRA_DEMO_TRECHOS",
    "CONFLUENCE_DEMO_TRECHOS",
]
