import json
from datetime import datetime
from langchain_core.tools import tool

# Tools for handling customer support tasks
@tool
def send_response(to: str, subject: str, content: str) -> str:
    '''Send a response to a customer inquiry.'''
    # Placeholder response - in real app would send actual message
    return f'Response sent to {to} with subject "{subject}"'

@tool
def create_support_ticket(
    customer_name: str, issue_type: str, description: str, priority: str
) -> str:
    '''Create a support ticket in the system.'''
    # Placeholder response - in real app would create ticket in support system
    return f'Support ticket created for {customer_name} with priority {priority}'

MEMORY_DB = {}

# Create simplified memory tools
@tool
def manage_memory(
    content: str = None, action: str = 'create', id: str = None
) -> str:
    '''Create, update, or delete persistent MEMORIES for this customer.'''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f'\n\t🧠 [MEMORY OPERATION - {action.upper()}]')

    if action == 'create' and content:
        memory_id = f'mem_{abs(hash(content))}'[:12]
        MEMORY_DB[memory_id] = {
            'content': content,
            'created_at': timestamp,
            'updated_at': timestamp,
        }
        print(f'\t✅ Created memory: {memory_id}')
        return f'created memory {memory_id}'

    elif action == 'update' and id and content:
        if id in MEMORY_DB:
            MEMORY_DB[id]['content'] = content
            MEMORY_DB[id]['updated_at'] = timestamp
            print(f'\t✅ Updated memory: {id}')
            return f'updated memory {id}'
        else:
            print(f'\t❌ Failed to update: Memory {id} not found')
            return f'Error: Memory {id} not found'

    elif action == 'delete' and id:
        if id in MEMORY_DB:
            del MEMORY_DB[id]
            print(f'\t✅ Deleted memory: {id}')
            return f'deleted memory {id}'
        else:
            print(f'\t❌ Failed to delete: Memory {id} not found')
            return f'Error: Memory {id} not found'

    return 'Memory operation failed. Check parameters.'


@tool
def search_memory(
    query: str, limit: int = 10, offset: int = 0, filter: dict = None
) -> str:
    '''Search memories for information relevant to the current context.'''
    print(f'\n\t🔍 [MEMORY SEARCH]')
    print(f'\t🔎 Query: {query}')

    # Simplified memory search based on basic text matching
    results = []
    query_lower = query.lower()

    for mem_id, data in MEMORY_DB.items():
        content = data['content'].lower()
        # Simple relevance score based on word matching
        if any(term in content for term in query_lower.split()):
            score = sum(term in content for term in query_lower.split()) / len(
                query_lower.split()
            )
            results.append(
                {
                    'id': mem_id,
                    'value': {'content': data['content']},
                    'created_at': data['created_at'],
                    'updated_at': data['updated_at'],
                    'score': score,
                }
            )

    # Sort by relevance score
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:limit]

    print(f'\t📊 Found {len(results)} relevant memories')
    for r in results:
        print(f'\t  • [{r["id"]}] - Score: {r["score"]:.4f}')
        print(
            f'\t    {r["value"]["content"][:100]}{"..." if len(r["value"]["content"]) > 100 else ""}'
        )

    return json.dumps(results)
