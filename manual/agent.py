import os
from dotenv import load_dotenv
from typing import List, Optional
from openai import OpenAI

from memory import Memory

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class MemoryAgent:
    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        model_name: str = 'gpt-4o-mini',
        memory_dir: str = './agent_memory'
    ):
        self.memory = Memory(storage_dir=memory_dir)
        # Add some initial facts about the agent
        self.memory.add_fact('I am an AI assistant with memory capabilities.')
        self.memory.add_fact('I can remmeber user interactions and recall them later.')
        self.memory.add_fact('I can store and retrieve factual information.')
        self.memory.add_fact('I can rememeber and execute procedures and workflows.')
        
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.system_prompt = '''You are a helpful AI assistant with memory capabilities. You can remember past interactions, 
facts you've learned, and procedures you know. Use the provided context to give personalized, 
contextually relevant responses. If you don't have relevant memory information, you can draw on 
your general knowledge. Always be helpful, accurate, and conversational.'''

    def query(self, user_message: str) -> str:
        # Check if the message is a command to remember a fact
        if user_message.lower().startswith('remember that'):
            fact = user_message[len('remember that'):].strip()
            return self.learn_fact(fact)
        
        # Check if the message is a command to learn a procedure
        if user_message.lower().startswith('remember the steps for'):
            # <procedure_name>: <step1>, <step2>, ...
            try:
                procedure_name_part, steps_part = user_message.split(':', 1)
                procedure_name = procedure_name_part[len('remember the steps for'):].strip()
                steps = [step.strip() for step in steps_part.split(',')]
                return self.learn_procedure(procedure_name, steps)
            except ValueError:
                return 'Please provide a procedure name and steps in the format: "remember the steps for <procedure_name>: <step1>, <step2>, ..."'
        
        # Get context from memory
        memory_context = self.memory.generate_context(user_message)
        
        # Create the message for the LLM
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'system', 'content': f'Context from memory:\n{memory_context}'},
            {'role': 'user', 'content': user_message}
        ]
        
        try: 
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )
            
            response_text = completion.choices[0].message.content
            
            # Store the interaction in memory
            self.memory.add_conversation(
                user_message=user_message,
                agent_response=response_text,
            )
            
            return response_text
        except Exception as e:
            error_msg = f'Error requesting LLM response: {str(e)}'
            print(error_msg)
            return error_msg
    
    def learn_fact(self, fact: str, category: Optional[str] = None) -> str:
        self.memory.add_fact(fact, category)
        return f'I have learned the fact: {fact}'

    def learn_procedure(
        self, name: str, steps: List[str], description: Optional[str] = None
    ) -> str:
        self.memory.add_procedure(name, steps, description)
        return f'I have learned the procedure: {name}'