import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.store.memory import InMemoryStore

from helpers import extract_key_information, clean_response

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model='gpt-4o-mini',
    temperature=0.2,
)

# Create memory store (in-memory)
# Note: when quit the program, the memory will be lost
store = InMemoryStore()

SYSTEM_PROMPT = '''You are a personal health coach with access to memory tools.
Your goal is to help users achieve their fitness goals by providing personalized advice and tracking their progress over time.

You have two special abilities:
1. You can search past memories about the user to provide personalized advice
2. You can store new information about the user for future reference

When appropriate, you will:
- Search memory for user context (diet, fitness level, goals, etc.)
- Store important new information (changes in weight, new goals, etc.)
- Reference past context to provide continuity

Always be supportive, encouraging, and provide actionable advice.
'''

# User ID (simple simulation)
user_id = 'user123'

# Create tools
manage_memory = create_manage_memory_tool(
    namespace=('health_coach', user_id, 'memories'),
    store=store
)
search_memory = create_search_memory_tool(
    namespace=('health_coach', user_id, 'memories'),
    store=store
)

def extract_key_information(user_message: str) -> str:
    '''
    Automatically extract key health/fitness information from user messages
    when no explicit memory instruction is found
    '''
    # Simple extraction for demonstration - in a real system, use NLP for better extraction
    memory = f'User shared: {user_message}'
    return memory

def clean_response(response: str) -> str:
    '''Clean up the response to remove any system artifacts'''
    # Remove common formatting markers
    for marker in ['RESPONSE:', 'USER RESPONSE:', 'COACH:']:
        if response.startswith(marker):
            response = response[len(marker):].strip()

    # Remove any remaining memory markers and their content
    for marker in ['MEMORY:', 'STORE IN MEMORY:', 'REMEMBER:']:
        if marker in response:
            parts = response.split(marker, 1)
            if len(parts) > 1:
                second_part = parts[1].split('\n\n', 1)
                if len(second_part) > 1:
                    response = parts[0] + second_part[1]
                else:
                    response = parts[0]

    return response.strip()

def run_interactive_health_coach():
    print('''I am your AI health coach with memory. I can provide personalized fitness advice.
I can also remember details about your fitness journey between conversations.
Type 'exit', 'quit', or 'bye' to end our conversation.''')
    
    # Init conversation history
    conversation_history = []
    
    # Start the conversation loop
    while True:
        user_message = input('\nYou: ')

        # Check if user wants to exit
        if user_message.lower() in ['exit', 'quit', 'bye']:
            print('\nThank you for chatting with your health coach! Stay healthy and keep moving!')
            break
        
        # Search memory for relevant context
        memory_results = '[]'
        try:
            # Create a search query based on user input and conversation history
            print('\n\tSearching memory for relevant context...')
            memory_results = search_memory.invoke({'query': user_message})
            # Parse and pretty-print memory results
            if memory_results and memory_results != '[]':
                try:
                    memory_items = json.loads(memory_results)
                    if memory_items:
                        print(f'\tFound {len(memory_items)} relevant memories:')
                        for i, item in enumerate(memory_items):
                            if 'value' in item and 'content' in item['value']:
                                print(f'\t\t• Memory {i+1}: {item["value"]["content"][:100]}...')
                    else:
                        print('\tNo relevant memories found.')
                except:
                    print(f"⚠️ Memory format: {memory_results[:100]}...")
            else:
                print('\tNo relevant memories found.')
        except Exception as e:
            print(f'\tError searching memory: {e}')

        # Add to conversation history
        conversation_history.append(user_message)
        
        # Create context for LLM
        context = (
            '\n'.join(conversation_history[-5:])
            if len(conversation_history) > 5
            else '\n'.join(conversation_history)
        )
        
        # Generate response with context
        message = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f'''User message: {user_message}

Previous conversation context: {context}

Memory search results: {memory_results}

Respond to the user with personalized health coaching advice based on their message and any relevant information from memory.

Also, identify if there's new important information about the user that should be stored in memory.
Don't mention the memory system directly to the user - they should just experience personalized advice.'''
            )
        ]
        
        # Get response from LLM
        print('\n⏳ Thinking...')
        response = llm.invoke(message)
        
        # Process response to extract potential memory updates
        response_text = response.content
        memory_to_store = None
        
        # Check if the response contains a clear indication of memory content
        if (
            'MEMORY:' in response_text
            or 'STORE IN MEMORY:' in response_text
            or 'REMEMBER:' in response_text
        ):
            try:
                # Try to extract memory section - assumes model might format its response with a designated memory section
                for marker in ['MEMORY:', 'STORE IN MEMORY:', 'REMEMBER:']:
                    if marker in response_text:
                        parts = response_text.split(marker, 1)
                        if len(parts) > 1:
                            memory_section = parts[1].split('\n\n', 1)[0].strip()
                            response_text = response_text.replace(
                                marker + memory_section,
                                ''
                            ).strip()
                            memory_to_store = memory_section
                            break

            except Exception as e:
                # If extraction fails, create a general memory
                memory_to_store = f"User message: {user_message}"
        else:
            # Create an automatic memory from this interaction
            memory_to_store = extract_key_information(user_message)
        
        # Store memory if we have something to store
        if memory_to_store:
            try:
                print('\n💾 Storing new information in memory...')
                manage_memory.invoke({'content': memory_to_store})
                print(f"Stored memory: {memory_to_store}")
            except Exception as e:
                print(f"Error storing memory: {e}")
        
        # Clean up response
        response_text = clean_response(response_text)
        
        # Print response
        print('\nCoach:', response_text)
        
if __name__ == '__main__':
    run_interactive_health_coach()