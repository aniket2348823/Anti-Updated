import asyncio
import difflib
import random
import collections
from backend.core.hive import BaseAgent, EventType, HiveEvent
from backend.core.protocol import JobPacket, ResultPacket, AgentID, TaskPriority, ModuleConfig
from backend.core.hyper_hive import negotiator
# Hybrid AI Engine
from backend.ai.cortex import CortexEngine

class GammaAgent(BaseAgent):
    """
    AGENT GAMMA: THE AUDITOR
    Role: Logic Verification.
    Capabilities:
    - Diff-Based Anomaly Detection (Baseline vs Attack).
    - Verification Mode.
    """
    def __init__(self, bus):
        super().__init__("agent_gamma", bus)
        # Arsenal stripped. Gamma is now purely a tactical router.
        # Hybrid AI Engine for anomaly classification
        self.cortex = CortexEngine()

    async def setup(self):
        self.bus.subscribe(EventType.JOB_ASSIGNED, self.handle_job)
        self.bus.subscribe(EventType.CONTROL_SIGNAL, self.handle_control)

    async def handle_control(self, event: HiveEvent):
        """Purge scan-scoped memory when the scan completes. Handled natively by ScanContext now."""
        pass

    async def handle_job(self, event: HiveEvent):
        # ... (Argument parsing)
        payload = event.payload
        try:
            packet = JobPacket(**payload)
        except: return

        if packet.config.agent_id != AgentID.GAMMA:
            return

        print(f"[{self.name}] Auditing Job {packet.id}")

        # BROADCAST AUDIT ACTIVITY
        await self.bus.publish(HiveEvent(
            type=EventType.LIVE_ATTACK,
            source=self.name,
            payload={
                "url": packet.target.url,
                "arsenal": "Logic Auditor",
                "action": "Analyzing behavioral anomalies",
                "payload": "Heuristic Audit Pass"
            }
        ))

        # Cyber-Organism Protocol: Verification Mode
        # If this is a re-scan request (e.g. from Beta finding), we lower aggression
        if packet.config.aggression > 5 and packet.priority == TaskPriority.CRITICAL:
            print(f"[{self.name}] [VERIFY] MODE. Lowering aggression to 1 for confirmation.")
            packet.config.aggression = 1 
        
        # SOTA: ANOMALY DIFFING
        # If we have a baseline response, compare it (isolated by scan_id)
        scan_id = packet.config.session_id or "default_scan"
        ctx = self.bus.get_or_create_context(scan_id)
        if "gamma_baselines" not in ctx.baseline_cache:
            ctx.baseline_cache["gamma_baselines"] = {}
        baseline = ctx.baseline_cache["gamma_baselines"].get(packet.target.url)
        
        print(f"[{self.name}] Delegating {packet.config.module_id} to SIGMA Orchestrator on {packet.target.url}")
        
        sigma_job = JobPacket(
            priority=packet.priority,
            target=packet.target,
            config=ModuleConfig(
                module_id=packet.config.module_id, 
                agent_id=AgentID.SIGMA, 
                params=packet.config.params,
                aggression=packet.config.aggression,
                session_id=scan_id
            )
        )
        await self.bus.publish(HiveEvent(
            type=EventType.JOB_ASSIGNED,
            source=self.name,
            payload=sigma_job.model_dump()
        ))
