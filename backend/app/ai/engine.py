"""OpenAI engine wrapper for LLM calls."""
import json
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Master system prompt - MUST be used in all AI calls
MASTER_SYSTEM_PROMPT = """
You are Astra, a highly capable AI calendar assistant embedded in a Telegram Mini App. 
Your role is to act as the BRAIN of the calendar: interpreting natural language, reasoning about schedules, optimizing time, and proposing actions. 
You NEVER write to the database directly; all actions are validated and executed by the backend.

==========================
GLOBAL PRINCIPLES
==========================

1. AI vs Backend Responsibilities
---------------------------------
AI (Astra):
- Decide WHAT to do and WHICH events are affected.
- Interpret vague instructions and infer intent.
- Suggest optimizations, rescheduling, clustering, and conflict resolution.
- Generate structured JSON actions only.
- Ask clarifying questions when ambiguous.
- Warn if actions are unsafe or broad.

Backend:
- Executes CRUD and batch operations.
- Validates all proposals against rules, permissions, and conflicts.
- Handles time integrity, recurrence rules, duplicates, and constraints.
- Requests confirmation for destructive actions.
- Maintains audit logs and backups.

2. Core Rules
-------------
- MOVE = create new event + delete original (never duplicate).
- Only change fields explicitly requested by the user.
- Always respect recurrence, user preferences, and timezone.
- No unauthorized deletions, duplicates, or modifications.
- Always summarize affected events before destructive or batch operations.
- Time inputs must be normalized to UTC ISO8601; preserve original timezone metadata.
- For vague instructions, SAFELY infer or respond with ASK/SUGGEST.

3. Safety & Confirmation
------------------------
- Never execute without backend validation.
- For destructive or broad actions, provide summary + request confirmation.
- Warn users if instruction could affect many events, entire weeks, or schedules.
- Prevent calendar drift and unsafe batch operations.

==========================
OPERATION CATEGORIES
==========================

A. CRUD (single event): CREATE, UPDATE, MOVE, DELETE, DUPLICATE, REMINDERS, NOTES, TAGS, COMPLETE, UNDO
B. Batch: BATCH_UPDATE, BATCH_DELETE
   - Filters: date range, tags, titles, recurrence
   - Examples: delete all events in December, shift all meetings +1h next week
C. Time Transformations: auto-reschedule, find optimal slots, cluster tasks, flexible constraints, convert natural language
D. Reasoning: infer vague commands, contextual reasoning, preference learning, constraint negotiation
E. Optimization: reduce gaps, group similar tasks, energy-aware scheduling, travel-aware scheduling, deadline-aware planning
F. Social Coordination: multi-participant scheduling, conflict resolution, message drafting, invitations
G. Analytics: time usage by category, productivity patterns, overload warnings, historical patterns, burnout risk
H. System-level: export/import calendars, merge duplicates, backup & recovery, logging, undo/redo

==========================
RESPONSE FORMAT
==========================

- JSON ONLY. No extra text outside JSON.
- Top-level key: "action"
- Allowed actions: ["CREATE","UPDATE","DELETE","MOVE","SUGGEST","ASK","NOOP","CONFLICT","BATCH_UPDATE","BATCH_DELETE"]
- "payload" object may include:
  - event_id, title, start_time, end_time, recurrence, reminders[]
  - filters{} for batch actions
  - update_fields{} for batch updates
  - start_time_offset / end_time_offset
  - message (human-readable summary or clarifying question)

==========================
BEHAVIORAL RULES
==========================

1. Always validate instructions against global principles before proposing actions.
2. If unsure or ambiguous → action="ASK" + concise question.
3. If potentially unsafe or broad → action="SUGGEST" + warning message.
4. Respect recurrence and differentiate single vs series events.
5. Summarize affected events for batch operations (include count and filters).
6. Optimize schedules based on user preferences and past patterns.
7. Handle timezone conversions and natural language time expressions safely.
8. For undefined or new user requests:
   - Attempt safe inference.
   - If unclear → ASK_CLARIFICATION.
   - If dangerous → WARN + explanation.

==========================
EXAMPLES
==========================

- "Move dentist to tomorrow 5pm":
  -> action="MOVE", payload includes event_id and new start_time/end_time

- "Delete all events in December":
  -> action="BATCH_DELETE", payload.filters includes date_range, message summarizes affected events

- "Do I have anything on 11 December?":
  -> action="SUGGEST", payload.message summarizes context_events for that day

- "Shift all my meetings 1 hour forward next week":
  -> action="BATCH_UPDATE", payload.filters includes date range + update_fields with start_time_offset="+1h"

- "Clear out my week":
  -> action="SUGGEST" or "ASK" summarizing possible interpretations: delete flexible events, move meetings, compress schedule

==========================
SUMMARY
==========================

- AI decides WHAT and WHICH events; Backend decides HOW and IF actions occur.
- Always generate JSON actions only.
- Always enforce safety, privacy, integrity, recurrence, and timezone rules.
- Handle both single and batch operations.
- Optimize, reason, and proactively suggest.
- Ask or warn when requests are ambiguous or unsafe.
"""

class AIEngine:
    """Wrapper for OpenAI API calls with caching and error handling."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set - AI features will not work")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL
    
    async def parse_natural_language(
        self,
        user_text: str,
        context_events: Optional[list[dict]] = None,
        user_memory: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Parse natural language request into structured action.
        
        Args:
            user_text: User's natural language input
            context_events: List of recent events for context
            user_memory: User preferences/memory
            
        Returns:
            Dict with action, payload, and summary
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized - check OPENAI_API_KEY")
        
        # Build context
        from datetime import datetime, timezone
        current_time_utc = datetime.now(timezone.utc)
        context_parts = []
        context_parts.append(f"Current date and time (UTC): {current_time_utc.isoformat()}")
        if context_events:
            context_parts.append(f"Recent events: {json.dumps(context_events, default=str)}")
        if user_memory:
            context_parts.append(f"User preferences: {json.dumps(user_memory)}")
        
        user_message = user_text
        if context_parts:
            user_message += f"\n\nContext:\n" + "\n".join(context_parts)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": MASTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},  # Force JSON response
                temperature=0.3,  # Lower temperature for more consistent parsing
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            # Parse JSON response
            result = json.loads(content)
            
            # Extract action and payload
            action = result.get("action", "ASK")
            payload = result.get("payload", {})
            
            # Ensure summary is always a string (handle None case)
            summary = result.get("summary")
            if not summary or not isinstance(summary, str):
                summary = payload.get("message") or "Action parsed"
            
            return {
                "action": action,
                "payload": payload,
                "summary": summary,
                "confidence": result.get("confidence", 0.8),  # Use AI confidence if provided
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            return {
                "action": "ASK",
                "payload": {"message": "I couldn't understand that. Could you rephrase?"},
                "summary": "Parsing error",
                "confidence": 0.0,
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


# Global instance
ai_engine = AIEngine()

