from schemas import Inquiry
from tools import search_memory, manage_memory, MEMORY_DB
from datetime import datetime
import json

# Simplified triage and response functions for the memory test
def handle_inquiry(inquiry: Inquiry, history=None):
    '''
    Process a customer inquiry and demonstrate memory operations.
    This is a simplified version of what would normally be handled by the agent graph.
    '''
    if history is None:
        history = []

    customer_email = inquiry['author']
    subject = inquiry['subject']
    message = inquiry['message_thread']

    print(f'\n📩 PROCESSING INQUIRY: {subject}')
    print(f'From:\t{customer_email}')
    print(f'Message:\t{message}')

    # Step 1: Search for customer context
    print('\n📚 STEP 1: Retrieving customer context from memory')
    search_result = search_memory.invoke({'query': customer_email})

    # Step 2: Process the inquiry with context
    print('\n📝 STEP 2: Processing the inquiry with available context')
    # In a real implementation, this would be where the agent generates a response

    # Step 3: Update memory with new information
    print('\n💾 STEP 3: Updating memory with new information')
    if 'login issue' in message.lower() or 'login issues' in message.lower():
        manage_memory.invoke(
            {
                'content': f'Customer {customer_email} reported login issues with the mobile app: {message[:100]}...'
            }
        )
    elif 'payment' in message.lower() or 'billing' in message.lower():
        manage_memory.invoke(
            {
                'content': f'Customer {customer_email} had billing/payment question: {message[:100]}...'
            }
        )
    elif 'feature' in message.lower() or 'suggestion' in message.lower():
        manage_memory.invoke(
            {
                'content': f'Customer {customer_email} suggested new feature: {message[:100]}...'
            }
        )
    else:
        manage_memory.invoke(
            {
                'content': f'Interaction with {customer_email} about {subject}: {message[:100]}...'
            }
        )

    # Record this interaction in history
    history.append(
        {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'inquiry': inquiry
        }
    )

    return history

def display_memory_contents():
    '''Display all memories stored in the system.'''
    print('\n📚 CURRENT MEMORY CONTENTS')

    if not MEMORY_DB:
        print('No memories stored yet.')
        return

    for mem_id, data in MEMORY_DB.items():
        print(f'\tID: {mem_id}')
        print(f'\tContent: {data["content"]}')
        print(f'\tCreated: {data["created_at"]}')
        print(f'\tUpdated: {data["updated_at"]}')
        print('-' * 50)


def run_customer_journey_simulation():
    '''Simulate a complete customer journey with multiple interactions to demonstrate how memory enhances the agent's capabilities.'''
    print('\n🔄 CUSTOMER JOURNEY SIMULATION WITH MEMORY')

    # Customer history will track all interactions
    customer_history = []

    # Day 1: Initial inquiry about login issues
    day1_inquiry = {
        'author': 'john.smith@example.com',
        'to': 'support@yourcompany.com',
        'subject': 'Cannot login to mobile app',
        'message_thread': '''Hello Support,

I've been trying to login to your mobile app since yesterday but keep getting an "Authentication Failed" error. 
I can login to the website just fine with the same credentials.

Thanks,
John Smith''',
    }

    print('\n\n' + '=' * 80)
    print('📅 DAY 1: Initial Contact')
    customer_history = handle_inquiry(day1_inquiry, customer_history)

    # Show memory after first interaction
    display_memory_contents()

    # Day 3: Follow-up about the same issue
    day3_inquiry = {
        'author': 'john.smith@example.com',
        'to': 'support@yourcompany.com',
        'subject': 'Re: Cannot login to mobile app',
        'message_thread': '''Hi again,

I tried the app reinstall you suggested but I'm still having the login issue.
Could this be related to the fact that I recently changed my password?

John''',
    }

    print('\n\n📅 DAY 3: Follow-up on Same Issue')
    customer_history = handle_inquiry(day3_inquiry, customer_history)

    # Show memory after second interaction
    display_memory_contents()

    # Day 10: New issue about billing
    day10_inquiry = {
        'author': 'john.smith@example.com',
        'to': 'support@yourcompany.com',
        'subject': 'Question about my recent bill',
        'message_thread': '''Hello Support Team,

I just noticed I was charged twice for my subscription this month.
Can you please look into this and process a refund for the duplicate charge?

Best regards,
John Smith''',
    }

    print('\n\n📅 DAY 10: New Issue (Billing)')
    customer_history = handle_inquiry(day10_inquiry, customer_history)

    # Show memory after third interaction
    display_memory_contents()

    # Day 45: Feature suggestion
    day45_inquiry = {
        'author': 'john.smith@example.com',
        'to': 'support@yourcompany.com',
        'subject': 'Feature suggestion',
        'message_thread': '''Hi there,

Now that my login and billing issues are resolved, I've been using the app regularly. 
I'd love to see a dark mode option added in a future update.

Thanks for all your help,
John''',
    }

    print('\n\n📅 DAY 45: Feature Suggestion')
    customer_history = handle_inquiry(day45_inquiry, customer_history)

    # Show final memory state
    display_memory_contents()

    # Search for this customer's login issues
    print('\n\n🔍 SEARCHING FOR CUSTOMER\'S LOGIN ISSUES')
    search_memory.invoke({'query': 'john.smith@example.com login'})

    # Search for this customer's billing issues
    print('\n\n🔍 SEARCHING FOR CUSTOMER\'S BILLING ISSUES')
    search_memory.invoke({'query': 'john.smith@example.com billing'})

    # Search for feature suggestions
    print('\n\n🔍 SEARCHING FOR FEATURE SUGGESTIONS')
    search_memory.invoke({'query': 'feature dark mode'})


def hot_path_vs_background_demo():
    '''Demonstrate the difference between hot path and background memory updates.'''
    print('\n\n' + '=' * 80)
    print('🔥 HOT PATH VS BACKGROUND MEMORY UPDATES')

    # Hot path example (synchronous)
    print('\n📌 HOT PATH MEMORY UPDATE (Synchronous)')
    print('\t1. Customer inquiry received')
    print('\t2. Search memory for context')
    print('\t3. Process inquiry')
    print('\t4. Update memory ← This happens BEFORE sending response')
    print('\t5. Send response to customer')
    print('\t⏱️ Response time: 2.5 seconds (slower but with latest information)')

    # Background example (asynchronous)
    print('\n📌 BACKGROUND MEMORY UPDATE (Asynchronous)')
    print('\t1. Customer inquiry received')
    print('\t2. Search memory for context')
    print('\t3. Process inquiry')
    print('\t4. Send response to customer')
    print('\t5. Update memory ← This happens AFTER sending response')
    print('\t⏱️ Response time: 1.2 seconds (faster but might use slightly outdated information)')

    # Tradeoffs
    print('\n📊 TRADEOFFS:')
    print('\t• Hot Path: Higher latency, most up-to-date information')
    print('\t• Background: Lower latency, potentially slightly outdated information')


if __name__ == '__main__':
    print('🚀 MEMORY SYSTEM DEMONSTRATION FOR CUSTOMER SUPPORT AGENT')

    # Run the customer journey simulation
    run_customer_journey_simulation()

    # Demonstrate hot path vs background memory updates
    hot_path_vs_background_demo()

    print('\n✅ DEMONSTRATION COMPLETE')