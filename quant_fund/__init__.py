"""
Multi-Agent Autonomous Quant Fund (LangGraph + Google GenAI SDK)
================================================================
Architecture:
- CEO Agent (`gemini-4-argon`): Macro/Market Context, Research Selection, Final Review
- Quant Worker Agent (`gemini-3.8-flash`): C# cBot Coding, Compilation, Backtesting, Bug Fixing
- Risk Manager Agent (`gemini-4-argon`): Gatekeeper with Veto Power (Hard SL, No Look-ahead, DD & PF checks)
- Human-in-the-Loop (HITL): LangGraph Checkpointer with `interrupt_before=["deploy_to_cloud"]`

Note on Models:
Per current Google Gemini API standards, legacy `gemini-2.5-*` models are deprecated.
We use `gemini-4-argon` for Pro/Reasoning roles (CEO & Risk Manager) and `gemini-3.8-flash` for Worker execution.
"""

MODEL_CEO = "gemini-4-argon"
MODEL_RISK_MANAGER = "gemini-4-argon"
MODEL_WORKER = "gemini-3.8-flash"

__all__ = ["MODEL_CEO", "MODEL_RISK_MANAGER", "MODEL_WORKER"]
