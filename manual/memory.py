import json
import os
import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class Memory:
    def __init__(self, 
        storage_dir: str = './agent_memory',
        facts_file: str = 'facts_semantic.json',
        conversations_file: str = 'conversations_episodic.json',
        procedures_file: str = 'procedures.json',
    ):
        # Create storage directory
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Memory components
        self.facts_file = os.path.join(self.storage_dir, facts_file)
        self.conversations_file = os.path.join(self.storage_dir, conversations_file)
        self.procedures_file = os.path.join(self.storage_dir, procedures_file)
        
        # Init memory stores
        self.facts = self._load_json(self.facts_file, default=[])
        self.conversations = self._load_json(self.conversations_file, default=[])
        self.procedures = self._load_json(self.procedures_file, default={})
        
        # Working memory (stays in RAM)
        self.working_memory = []
        self.working_memory_capacity = 10
    
    def _load_json(self, file_path: str, default: Any = None):
        '''Load a JSON file from the given path. If the file does not exist, return the default value.'''
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            return default
    
    def _save_json(self, data: Any, file_path: str):
        '''Save a JSON object to the given file path.'''
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_fact(
        self, content: str, category: Optional[str] = None
    ):
        '''Add a fact to semantic memory.'''
        fact = {
            'content': content,
            'category': category,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.facts.append(fact)
        self._save_json(self.facts, self.facts_file)
    
    def add_procedure(
        self, name: str, steps: List[str], description: Optional[str] = None
    ):
        '''Add a procedure to procedual memory.'''
        procedure = {
            'name': name,
            'steps': steps,
            'description': description,
            'timestamp': datetime.datetime.now().isoformat(),
            'usage_count': 0
        }
        self.procedures[name] = procedure
        self._save_json(self.procedures, self.procedures_file)
    
    def add_conversation(
        self, user_message: str, agent_response: str, metadata: Optional[Dict[str, Any]] = None
    ):
        '''Add a conversation turn to episodic memory.'''
        conversation = {
            'user_message': user_message,
            'agent_response': agent_response,
            'metadata': metadata or {},
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.conversations.append(conversation)
        self._save_json(self.conversations, self.conversations_file)
        
        # Also update working memory
        self.add_to_working_memory(f'User: {user_message}', importance=1.0)
        self.add_to_working_memory(f'Agent: {agent_response}', importance=0.9)
    
    def add_to_working_memory(self, content: str, importance: float = 1.0):
        '''Add an item to working memory with importance score'''
        item = {
            'content': content,
            'importance': importance,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.working_memory.append(item)
        # If over capacity, remove least important item
        if len(self.working_memory) > self.working_memory_capacity:
            self.working_memory.sort(
                key=lambda x: (x['importance'], x['timestamp']),
            )
            self.working_memory = self.working_memory[1:]
    
    def search_facts(self, query: str, limit: int = 3):
        '''Keyword search for facts'''
        query_terms = query.lower().split()
        results = []
        
        for fact in self.facts:
            content = fact['content'].lower()
            # Score based on number of matching terms
            score = sum(1 for term in query_terms if term in content)
            if score > 0:
                results.append((fact, score))
        
        # Sort by score and return top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in results[:limit]]
        
    def search_conversations(self, query: str, limit: int = 3):
        '''Keyword search for past conversations'''
        query_terms = query.lower().split()
        results = []
        
        for conversation in self.conversations:
            text = f'{conversation["user_message"]} {conversation["agent_response"]}'.lower()
            # Score based on number of matching terms
            score = sum(1 for term in query_terms if term in text)
            if score > 0:
                results.append((conversation, score))
        
        # Sort by score and return top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in results[:limit]]

    def search_procedures(self, query: str, limit: int = 3):
        '''Keyword search for procedures by keyword matching'''
        query_terms = query.lower().split()
        results = []
        
        for name, procedure in self.procedures.items():
            text = f'{name} {procedure.get("description", "")}'.lower()
            # Check if query terms appear in text
            if query in text:
                results.append((procedure, 1))
        
        # Sort by score and return top-k
        results.sort(key=lambda x: x.get('usage_count', 0), reverse=True)
        return results[:limit]

    def get_recent_conversations(self, count: int = 5) -> List[Dict[str, Any]]:
        '''Get the most recent conversations'''
        return self.conversations[-count:] if len(self.conversations) > count else self.conversations
    
    def generate_context(self, current_message: str) -> str:
        '''Generate context for LLM using relevant memory'''
        # Get working memory
        working_items = sorted(
            self.working_memory, 
            key=lambda x: (x['importance'], x['timestamp']),
            reverse=True
        )
        working_memory_text = '\n'.join(
            [f'- {item["content"]}' for item in working_items]
        )
        
        # Get recent conversations
        recent = self.get_recent_conversations(3)
        recent_text = '\n'.join(
            [
                f'User: {conversation["user_message"]}\nAgent: {conversation["agent_response"]}'
                for conversation in recent
            ]
        )
        
        # Get relavant facts
        relavant_facts = self.search_facts(current_message)
        facts_text = '\n'.join(
            [f'- {fact["content"]}' for fact in relavant_facts]
        )
        
        # Get relavant procedures
        relavant_procedures = self.search_procedures(current_message)
        procedures_text = ''
        for procedure in relavant_procedures:
            steps = '\n'.join(
                [f'{i+1}. {step}' for i, step in enumerate(procedure['steps'])]
            )
            procedures_text += f'Procedure: {procedure["name"]}\n{steps}\n\n'
            
        # Combine all context
        context = f'''### Current Context (Working memory):
{working_memory_text}

### Recent Conversation History:
{recent_text}

### Relevant Facts from Memory:
{facts_text}

### Relevant Procedures:
{procedures_text}
'''
        
        return context.strip()