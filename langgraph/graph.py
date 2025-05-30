from langchain.chat_models import init_chat_model
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.prebuilt import create_react_agent

from schemas import State, Router
from tools import (
    send_response,
    create_support_ticket,
    manage_memory,
    search_memory
)
from prompts import (
    prompt_instructions,
    triage_system_prompt, 
    triage_user_prompt, 
    create_agent_prompt
)

# Init LLM
llm = init_chat_model('openai:gpt-4o-mini')

# Init LLM router with structured output
llm_router = llm.with_structured_output(Router)

# Memory store with embeddings
store = InMemoryStore(
    index={'embed': 'openai:text-embedding-3-small'}
)

# Create the response agent
response_agent = create_react_agent(
    'openai:gpt-4o-mini',
    tools=[
        send_response, create_support_ticket, manage_memory, search_memory
    ],
    prompt=create_agent_prompt,
    store=store # Pass the store to ensure memory function work
)

# Define the triage router function
def triage_router(state: State) -> Command[Literal['response_agent', '__end__']]:
    author = state['inquiry_input']['author']
    to = state['inquiry_input']['to']
    subject = state['inquiry_input']['subject']
    message_thread = state['inquiry_input']['message_thread']

    system_prompt = triage_system_prompt.format(
        triage_no=prompt_instructions['triage_rules']['ignore'],
        triage_notify=prompt_instructions['triage_rules']['notify'],
        triage_email=prompt_instructions['triage_rules']['respond'],
    )

    user_prompt = triage_user_prompt.format(
        author=author, to=to, subject=subject, message_thread=message_thread
    )

    result = llm_router.invoke(
        [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
    )

    if result.classification == 'respond':
        print('🔴 Classification: RESPOND - This inquiry requires a response')
        # This is the correct way to return a command with state update
        return Command(
            goto='response_agent',
            update={
                'messages': [
                    {
                        'role': 'user',
                        'content': f'Respond to the customer inquiry:\nFrom: {author}\nSubject: {subject}\nMessage: {message_thread}',
                    }
                ]
            },
        )
    else:
        print(
            f'⚪ Classification: {result.classification.upper()} - No response needed'
        )
        # For ignore/notify, just end without state update
        return Command(goto='__end__')

# Create the graph
customer_support_agent = StateGraph(State)
customer_support_agent.add_node('triage_router', triage_router)
customer_support_agent.add_node('response_agent', response_agent)
customer_support_agent.add_edge(START, 'triage_router')
customer_support_agent.add_edge('triage_router', 'response_agent')
customer_support_agent.add_edge('triage_router', END)
customer_support_agent.add_edge('response_agent', END)

# Compile the graph
customer_support_agent = customer_support_agent.compile()