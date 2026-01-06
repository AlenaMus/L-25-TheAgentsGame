# State Management Architecture

## Table of Contents
1. [Overview](#overview)
2. [State Machine Patterns](#state-machine-patterns)
3. [Game State Machine](#game-state-machine)
4. [Round State Machine](#round-state-machine)
5. [Player State Management](#player-state-management)
6. [State Persistence](#state-persistence)
7. [State Recovery](#state-recovery)
8. [Implementation Patterns](#implementation-patterns)

---

## Overview

### Purpose
This document defines the state management architecture for the Even/Odd Game League system, ensuring consistent state transitions, reliable persistence, and recovery from failures.

### Principles
- **Explicit State Machines**: All state transitions are explicit and validated
- **Immutable Transitions**: State transitions are atomic and logged
- **Recovery-Ready**: System can restore state after crashes
- **Audit Trail**: All state changes are logged for debugging
- **Type Safety**: Use enums for state values, not strings

### State Hierarchy

```
League State
    - Active leagues
    - League standings
    - Current round number
       |
       +-- Round State              +-- Player State
           - Round scheduling            - Registration status
           - Announcement tracking       - Match history
           - Completion status           - Connection state
              |
              +-- Game State
                  - Waiting for players
                  - Collecting choices
                  - Drawing number
                  - Evaluating result
                  - Finished
```

---

## State Machine Patterns

### Base State Machine Implementation

```python
from enum import Enum
from typing import TypeVar, Generic, Dict, Set, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

StateType = TypeVar('StateType', bound=Enum)

@dataclass
class StateTransition(Generic[StateType]):
    """Records a single state transition"""
    from_state: StateType
    to_state: StateType
    timestamp: datetime
    trigger: str
    metadata: Dict = field(default_factory=dict)

class StateMachine(Generic[StateType]):
    """
    Generic state machine with validation and audit trail.
    
    Usage:
        class MyState(Enum):
            INITIAL = "initial"
            PROCESSING = "processing"
            DONE = "done"
        
        sm = StateMachine(
            initial_state=MyState.INITIAL,
            valid_transitions={
                MyState.INITIAL: {MyState.PROCESSING},
                MyState.PROCESSING: {MyState.DONE}
            }
        )
        sm.transition(MyState.PROCESSING, trigger="start_processing")
    """
    
    def __init__(
        self,
        initial_state: StateType,
        valid_transitions: Dict[StateType, Set[StateType]],
        on_enter_callbacks: Optional[Dict[StateType, Callable]] = None,
        on_exit_callbacks: Optional[Dict[StateType, Callable]] = None
    ):
        self.current_state = initial_state
        self.valid_transitions = valid_transitions
        self.on_enter = on_enter_callbacks or {}
        self.on_exit = on_exit_callbacks or {}
        self.history: list[StateTransition] = []
        
    def can_transition(self, to_state: StateType) -> bool:
        """Check if transition is valid"""
        valid_next_states = self.valid_transitions.get(self.current_state, set())
        return to_state in valid_next_states
    
    def transition(
        self,
        to_state: StateType,
        trigger: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Attempt state transition.
        
        Returns:
            True if transition succeeded, False otherwise
        """
        if not self.can_transition(to_state):
            raise InvalidTransitionError(
                f"Invalid transition from {self.current_state} to {to_state}"
            )
        
        # Record transition
        transition = StateTransition(
            from_state=self.current_state,
            to_state=to_state,
            timestamp=datetime.utcnow(),
            trigger=trigger,
            metadata=metadata or {}
        )
        
        # Execute exit callback
        if self.current_state in self.on_exit:
            self.on_exit[self.current_state](transition)
        
        # Update state
        old_state = self.current_state
        self.current_state = to_state
        self.history.append(transition)
        
        # Execute enter callback
        if to_state in self.on_enter:
            self.on_enter[to_state](transition)
        
        return True
    
    def get_history(self) -> list[StateTransition]:
        """Get full transition history"""
        return self.history.copy()
    
    def to_dict(self) -> dict:
        """Serialize state for persistence"""
        return {
            "current_state": self.current_state.value,
            "history": [
                {
                    "from": t.from_state.value,
                    "to": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "trigger": t.trigger,
                    "metadata": t.metadata
                }
                for t in self.history
            ]
        }

class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition"""
    pass
```

