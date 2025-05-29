from agent import MemoryAgent

def main():
    agent = MemoryAgent()

    # Add some initial knowledge
    agent.learn_fact(
        'Python is a high-level programming language known for its readability.',
        'Programming',
    )
    agent.learn_fact(
        'Memory systems in AI agents are crucial for continuity and personalization.',
        'AI',
    )

    agent.learn_procedure(
        'Create a simple AI agent with memory',
        [
            'Initialize memory storage (files, database, etc.)',
            'Create functions to add facts to semantic memory',
            'Create functions to store conversation history in episodic memory',
            'Create functions to retrieve relevant memory based on context',
            'Connect memory system to an LLM like GPT-4o-mini',
            'Implement a query function that includes memory context in prompts',
            'Add memory updating after each interaction',
        ],
        'Steps to create a basic AI agent with memory capabilities',
    )

    print('''
    AI Assistant with Memory initialized!
    1. If you want to remember a fact, use the format: "remember that <fact>"
    2. If you want to remember a procedure, use the format: "remember the steps for <procedure_name>: <step1>, <step2>, ..."
    3. Type "exit" to quit.
    ''')
    print('-' * 70)

    # Simple conversation loop
    while True:
        user_input = input('\nYou: ')
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print('\nAssistant: Goodbye! It was nice talking with you.')
            break

        # Process the user's message
        response = agent.query(user_input)
        print(f'\nAssistant: {response}')


if __name__ == "__main__":
    main()