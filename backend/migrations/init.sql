CREATE TABLE IF NOT EXISTS persona_group (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    source TEXT NOT NULL DEFAULT 'description',
    persona_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_persona_group_tenant_id ON persona_group(tenant_id);

CREATE TABLE IF NOT EXISTS persona (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    city TEXT NOT NULL,
    occupation TEXT NOT NULL,
    monthly_income INTEGER NOT NULL,
    personality TEXT NOT NULL,
    consumer_profile TEXT NOT NULL,
    media_behavior TEXT NOT NULL,
    social_behavior TEXT NOT NULL,
    agent_config TEXT NOT NULL,
    backstory TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_persona_tenant_id ON persona(tenant_id);
CREATE INDEX IF NOT EXISTS idx_persona_group_id ON persona(group_id);

CREATE TABLE IF NOT EXISTS focus_group_session (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    persona_group_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    product_context TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    summary TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fg_session_tenant_id ON focus_group_session(tenant_id);

CREATE TABLE IF NOT EXISTS focus_group_message (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    sender_type TEXT NOT NULL,
    persona_id INTEGER,
    persona_name TEXT,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fg_message_session_id ON focus_group_message(session_id);

CREATE TABLE IF NOT EXISTS simulation_session (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    persona_group_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    content_text TEXT NOT NULL,
    config TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_rounds INTEGER NOT NULL DEFAULT 8,
    current_round INTEGER NOT NULL DEFAULT 0,
    metrics_timeline TEXT NOT NULL,
    actions TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sim_session_tenant_id ON simulation_session(tenant_id);

CREATE TABLE IF NOT EXISTS simulation_report (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL UNIQUE,
    payload TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ab_test (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    persona_group_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workshop_session (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    persona_group_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    brand_tone TEXT NOT NULL,
    brief TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planning',
    payload TEXT NOT NULL,
    insights TEXT NOT NULL,
    ab_test_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_workshop_session_tenant_id ON workshop_session(tenant_id);

CREATE TABLE IF NOT EXISTS market_graph (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    source_text TEXT NOT NULL,
    entities TEXT NOT NULL,
    relations TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_market_graph_tenant_id ON market_graph(tenant_id);

CREATE TABLE IF NOT EXISTS market_report (
    id INTEGER PRIMARY KEY,
    graph_id INTEGER NOT NULL UNIQUE,
    payload TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sentiment_guard_session (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    event_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payload TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sg_session_tenant_id ON sentiment_guard_session(tenant_id);

CREATE TABLE IF NOT EXISTS strategy_advisor_session (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    context_info TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payload TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sa_session_tenant_id ON strategy_advisor_session(tenant_id);

CREATE TABLE IF NOT EXISTS persona_memory (
    id INTEGER PRIMARY KEY,
    persona_id INTEGER NOT NULL,
    session_type TEXT NOT NULL,
    session_id INTEGER NOT NULL,
    memory_summary TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pm_persona_id ON persona_memory(persona_id);

CREATE TABLE IF NOT EXISTS content_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workshop_session_id INTEGER NOT NULL,
    variant TEXT NOT NULL,
    went_live INTEGER NOT NULL DEFAULT 0,
    actual_engagement_rate REAL,
    actual_conversion_rate REAL,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cr_workshop ON content_result(workshop_session_id);

CREATE TABLE IF NOT EXISTS workflow_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL DEFAULT 1,
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    config TEXT NOT NULL DEFAULT '{}',
    steps TEXT NOT NULL DEFAULT '[]',
    current_step TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_workflow_tenant ON workflow_session(tenant_id);

CREATE TABLE IF NOT EXISTS knowledge_project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_doc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    char_count INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_kd_project_id ON knowledge_doc(project_id);

CREATE TABLE IF NOT EXISTS knowledge_chunk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_kc_project_id ON knowledge_chunk(project_id);
CREATE INDEX IF NOT EXISTS idx_kc_doc_id ON knowledge_chunk(doc_id);
