-- ============================================================================
-- Antigravity Trading Platform (V2) — Supabase PostgreSQL Schema & RLS
-- Paradigm: Build (AI) -> Prove (Math/Stats) -> Protect (Deterministic Rules)
-- รันใน Supabase Dashboard -> SQL Editor
-- ============================================================================

-- 1. Immutable Risk Policies (Managed ONLY by System Admin; Read-Only for AI)
CREATE TABLE IF NOT EXISTS public.risk_policies (
    id                          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner                       UUID REFERENCES auth.users ON DELETE CASCADE,
    policy_version              TEXT NOT NULL UNIQUE,
    hard_max_dd_pct             NUMERIC NOT NULL DEFAULT 18.0,
    hard_max_risk_per_trade_pct NUMERIC NOT NULL DEFAULT 2.0,
    hard_min_profit_factor      NUMERIC NOT NULL DEFAULT 1.15,
    hard_min_oos_pf             NUMERIC NOT NULL DEFAULT 1.03,
    hard_max_mc_ruin_prob_pct   NUMERIC NOT NULL DEFAULT 1.0,
    max_worker_iterations       INT NOT NULL DEFAULT 3,
    daily_token_limit           INT NOT NULL DEFAULT 500000,
    daily_cost_limit_usd        NUMERIC NOT NULL DEFAULT 5.00,
    created_by                  TEXT NOT NULL DEFAULT 'SYSTEM_ADMIN',
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Strategy Hypotheses (Market Research Team + CEO Strategist Policy)
CREATE TABLE IF NOT EXISTS public.strategy_hypotheses (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner                   UUID REFERENCES auth.users ON DELETE CASCADE,
    risk_policy_id          BIGINT REFERENCES public.risk_policies(id),
    hypothesis_code         TEXT NOT NULL UNIQUE,
    symbol                  TEXT NOT NULL,
    paper_reference         TEXT,
    market_research_context JSONB NOT NULL DEFAULT '{}',
    ceo_proposed_policy     JSONB NOT NULL DEFAULT '{}',
    status                  TEXT NOT NULL DEFAULT 'IN_PROGRESS',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Strategy Versions (Tracks C# Source Hash & Dataset Hash per Iteration)
CREATE TABLE IF NOT EXISTS public.strategy_versions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner              UUID REFERENCES auth.users ON DELETE CASCADE,
    hypothesis_id      TEXT NOT NULL,
    strategy_code      TEXT NOT NULL,
    symbol             TEXT NOT NULL,
    iteration_num      INT NOT NULL CHECK (iteration_num BETWEEN 1 AND 3),
    csharp_class_name  TEXT NOT NULL,
    csharp_file_path   TEXT,
    source_code_sha256 TEXT NOT NULL,
    dataset_sha256     TEXT NOT NULL,
    parameters_json    JSONB NOT NULL DEFAULT '{}',
    compile_passed     BOOLEAN NOT NULL DEFAULT FALSE,
    unit_test_passed   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Deterministic Backtest Math Reports (Computed 100% by Python Math Engine)
CREATE TABLE IF NOT EXISTS public.backtest_math_reports (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner                  UUID REFERENCES auth.users ON DELETE CASCADE,
    strategy_version_id    UUID NOT NULL UNIQUE REFERENCES public.strategy_versions(id) ON DELETE CASCADE,
    cost_assumptions       JSONB NOT NULL,
    full_period_metrics    JSONB NOT NULL DEFAULT '{}',
    in_sample_metrics      JSONB NOT NULL,
    validation_metrics     JSONB NOT NULL,
    out_of_sample_metrics  JSONB NOT NULL,
    walk_forward_matrix    JSONB NOT NULL,
    monte_carlo_summary    JSONB NOT NULL,
    parameter_sensitivity  JSONB NOT NULL,
    computed_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Gatekeeper Boolean Checklist Validation (Replaces legacy 0-100 score)
CREATE TABLE IF NOT EXISTS public.validation_checklists (
    id                           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner                        UUID REFERENCES auth.users ON DELETE CASCADE,
    strategy_version_id          UUID NOT NULL UNIQUE REFERENCES public.strategy_versions(id) ON DELETE CASCADE,
    has_hard_stop_loss           BOOLEAN NOT NULL DEFAULT FALSE,
    risk_per_trade_within_limit  BOOLEAN NOT NULL DEFAULT FALSE,
    max_dd_within_limit          BOOLEAN NOT NULL DEFAULT FALSE,
    pf_above_minimum             BOOLEAN NOT NULL DEFAULT FALSE,
    oos_profitable               BOOLEAN NOT NULL DEFAULT FALSE,
    walk_forward_passed          BOOLEAN NOT NULL DEFAULT FALSE,
    monte_carlo_passed           BOOLEAN NOT NULL DEFAULT FALSE,
    no_lookahead_bias_verified   BOOLEAN NOT NULL DEFAULT FALSE,
    ai_security_audit_passed     BOOLEAN NOT NULL DEFAULT FALSE,
    overall_passed               BOOLEAN GENERATED ALWAYS AS (
        has_hard_stop_loss AND risk_per_trade_within_limit AND max_dd_within_limit AND
        pf_above_minimum AND oos_profitable AND walk_forward_passed AND
        monte_carlo_passed AND no_lookahead_bias_verified AND ai_security_audit_passed
    ) STORED,
    veto_reasons                 JSONB NOT NULL DEFAULT '[]',
    ai_auditor_model             TEXT NOT NULL,
    audited_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Node-Level Workflow Audit Logs & Token/Cost Circuit Breaker Tracking
CREATE TABLE IF NOT EXISTS public.workflow_audit_logs (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner               UUID REFERENCES auth.users ON DELETE CASCADE,
    hypothesis_id       TEXT,
    strategy_version_id TEXT,
    node_name           TEXT NOT NULL,
    agent_model         TEXT NOT NULL,
    prompt_version      TEXT NOT NULL,
    policy_version      TEXT NOT NULL,
    input_payload       JSONB NOT NULL DEFAULT '{}',
    output_payload      JSONB NOT NULL DEFAULT '{}',
    tokens_used         INT NOT NULL DEFAULT 0,
    estimated_cost_usd  NUMERIC NOT NULL DEFAULT 0.0,
    verdict             TEXT,
    verdict_reasons     JSONB NOT NULL DEFAULT '[]',
    executed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Two-Stage Human-in-the-Loop Deployment Approvals (Paper vs Live)
CREATE TABLE IF NOT EXISTS public.deployment_approvals (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner                  UUID REFERENCES auth.users ON DELETE CASCADE,
    strategy_version_id    UUID NOT NULL REFERENCES public.strategy_versions(id),
    stage_type             TEXT NOT NULL CHECK (stage_type IN ('PAPER_TRADING', 'LIVE_TRADING')),
    approved_by            TEXT NOT NULL,
    target_environment     TEXT NOT NULL,
    forward_test_days      INT DEFAULT 0,
    forward_vs_bt_drift    NUMERIC DEFAULT 0.0,
    kill_switch_triggered  BOOLEAN NOT NULL DEFAULT FALSE,
    rollback_reason        TEXT,
    approved_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Strategy Memory (Separates Empirical Math Facts from Untrusted AI Notes)
CREATE TABLE IF NOT EXISTS public.strategy_memory (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner                 UUID REFERENCES auth.users ON DELETE CASCADE,
    strategy_version_id   TEXT NOT NULL,
    symbol                TEXT NOT NULL,
    market_regime         TEXT NOT NULL,
    empirical_facts_json  JSONB NOT NULL,
    ai_postmortem_notes   JSONB NOT NULL,
    verified_by_human     BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by           TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Web Dashboard Alerts (Primary Notification Channel on Existing Web UI)
CREATE TABLE IF NOT EXISTS public.web_alerts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner          UUID REFERENCES auth.users ON DELETE CASCADE,
    severity       TEXT NOT NULL DEFAULT 'INFO', -- CRITICAL, WARNING, HITL_GATE, PASS, INFO
    strategy_code  TEXT,
    symbol         TEXT,
    title          TEXT NOT NULL,
    message        TEXT NOT NULL,
    acknowledged   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS web_alerts_created_idx ON public.web_alerts (created_at DESC);
CREATE INDEX IF NOT EXISTS workflow_audit_logs_executed_idx ON public.workflow_audit_logs (executed_at DESC);

-- Enable Row Level Security (RLS) matching public.strategies & public.backtest_runs
ALTER TABLE public.risk_policies         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.strategy_hypotheses   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.strategy_versions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.backtest_math_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_audit_logs   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deployment_approvals  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.strategy_memory       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.web_alerts            ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "owner reads risk_policies" ON public.risk_policies;
CREATE POLICY "owner reads risk_policies" ON public.risk_policies FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads strategy_hypotheses" ON public.strategy_hypotheses;
CREATE POLICY "owner reads strategy_hypotheses" ON public.strategy_hypotheses FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads strategy_versions" ON public.strategy_versions;
CREATE POLICY "owner reads strategy_versions" ON public.strategy_versions FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads backtest_math_reports" ON public.backtest_math_reports;
CREATE POLICY "owner reads backtest_math_reports" ON public.backtest_math_reports FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads validation_checklists" ON public.validation_checklists;
CREATE POLICY "owner reads validation_checklists" ON public.validation_checklists FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads workflow_audit_logs" ON public.workflow_audit_logs;
CREATE POLICY "owner reads workflow_audit_logs" ON public.workflow_audit_logs FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads deployment_approvals" ON public.deployment_approvals;
CREATE POLICY "owner reads deployment_approvals" ON public.deployment_approvals FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads strategy_memory" ON public.strategy_memory;
CREATE POLICY "owner reads strategy_memory" ON public.strategy_memory FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

DROP POLICY IF EXISTS "owner reads web_alerts" ON public.web_alerts;
CREATE POLICY "owner reads web_alerts" ON public.web_alerts FOR SELECT TO authenticated USING (owner IS NULL OR owner = (SELECT auth.uid()));

INSERT INTO public.risk_policies (
    policy_version, hard_max_dd_pct, hard_max_risk_per_trade_pct,
    hard_min_profit_factor, hard_min_oos_pf, hard_max_mc_ruin_prob_pct,
    max_worker_iterations, daily_token_limit, daily_cost_limit_usd
) VALUES (
    'RISK-POL-V2.0', 18.0, 2.0, 1.15, 1.03, 1.0, 3, 500000, 5.00
) ON CONFLICT (policy_version) DO NOTHING;
