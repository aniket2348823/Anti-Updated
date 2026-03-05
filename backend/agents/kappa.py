import asyncio
import json
import os
from backend.core.hive import BaseAgent, EventType, HiveEvent
from backend.core.protocol import JobPacket, ResultPacket, AgentID

class KappaAgent(BaseAgent):
    """
    AGENT KAPPA: THE LIBRARIAN
    Role: Knowledge & Memory.
    Capabilities:
    - Persistent Memory (JSON Store).
    - Auto-Report Generation (Stub for PDF).
    - Collaborative Filtering (Recommendation).
    """
    def __init__(self, bus):
        super().__init__("agent_kappa", bus)
        # GAP FIX: Correct Path inside project
        # GAP FIX: Correct Path inside project
        base_dir = os.getcwd()
        self.memory_file = os.path.join(base_dir, "brain", "memory.json")
        
        # Initialize Cortex AI (Local Ollama)
        try:
            from backend.ai.cortex import CortexEngine
            self.truth_kernel = CortexEngine()
        except:
            self.truth_kernel = None
            
        self._ensure_memory()

    def _ensure_memory(self):
        # Create directory if needed
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, "w") as f:
                json.dump([], f)

    async def setup(self):
        # Listen for success stories to archive
        self.bus.subscribe(EventType.VULN_CONFIRMED, self.archive_victory)
        # GAP FIX: Listen for raw recon data to audit
        self.bus.subscribe(EventType.VULN_CANDIDATE, self.audit_candidate)

    async def audit_candidate(self, event: HiveEvent):
        """
        Antigravity V12: The Forensic Truth Kernel Audit
        """
        payload = event.payload
        # print(f"[{self.name}] [AUDIT] Auditing Candidate: {payload.get('description', 'Unknown')}")
        
        # Archive verified finding or just the candidate
        self._save_record(payload)

        # CORTEX AI: Assess candidate validity
        if self.truth_kernel and self.truth_kernel.enabled:
            try:
                verdict = self.truth_kernel.audit_candidate(payload)
                confidence = verdict.get('confidence', 0.5)
                is_real = verdict.get('is_real', True)
                reason = verdict.get('reasoning', 'N/A')
                print(f"[{self.name}] [AI AUDIT] Real={is_real} Confidence={confidence:.1f} Reason={reason}")
                
                if not is_real and confidence > 0.7:
                    print(f"[{self.name}] [AI AUDIT] FALSE POSITIVE suppressed. Will not escalate.")
                    return  # Don't escalate false positives
            except Exception as e:
                print(f"[{self.name}] [AI AUDIT] CortexEngine error: {e}")

    async def archive_victory(self, event: HiveEvent):
        payload = event.payload
        print(f"[{self.name}] [ARCHIVE] Vulnerability found by {event.source}")
        self._save_record(payload)
        
        # Emit Archive Log for Report
        await self.bus.publish(HiveEvent(
            type=EventType.LOG,
            source=self.name,
            payload={"message": f"Vector {payload.get('type', 'logic_overflow')} stored in Hive Memory."}
        ))

    def _save_record(self, record):
        try:
            with open(self.memory_file, "r+") as f:
                data = json.load(f)
                data.append(record)
                f.seek(0)
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[{self.name}] Memory Write Error: {e}")

    async def recall_tactics(self, query: str):
        # Simulating Semantic Search
        print(f"[{self.name}] Searching archives for: {query}")
        with open(self.memory_file, "r") as f:
            data = json.load(f)
        # Simple filter
        return [r for r in data if query in str(r)]
