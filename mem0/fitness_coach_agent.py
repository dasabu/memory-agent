import os
from dotenv import load_dotenv

import streamlit as st
from openai import OpenAI
from mem0 import Memory
import supabase

load_dotenv()

# Init supabase client
supabase_client = supabase.create_client(
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_API_KEY')
)

# Streamlit page config
st.set_page_config(
    page_title='Mem0 Fitness Coach Assistant',
    page_icon='💪',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Cache OpenAI client and Memory instance
@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@st.cache_resource
def get_memory():
    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
            },
        },
        "vector_store": {
            "provider": "supabase",
            "config": {
                "connection_string": os.getenv("DATABASE_URL"),
                "collection_name": "memories",
            },
        },
    }

    
    return Memory.from_config(config)

# Get cached resources
openai_client = get_openai_client()
memory = get_memory()

# Authentication functions
def sign_up(email, password, full_name):
    try:
        response = supabase_client.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': {
                    'full_name': full_name
                }
            }
        })
        
        if response and response.user:
            print(response)
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Error signing up: {str(e)}")
        return None
        
def sign_in(email, password):
    try:
        response = supabase_client.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        if response and response.user:
            # Store user info in session state
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Error signing in: {str(e)}")
        return None
            
def sign_out():
    try:
        supabase_client.auth.sign_out()
        # Clear authentication info from session state
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.login_requested = True
    except Exception as e:
        st.error(f"Error signing out: {str(e)}")

# Fitness Coach chat function with memory
def get_response(message, user_id):
    # Retrieve relavant memories
    relevant_memories = memory.search(
        query=message,
        user_id=user_id,
        limit=5
    )
    
    # Format memories for inclusion in prompt
    formatted_memories = ''
    if relevant_memories and len(relevant_memories['results']) > 0:
        for entry in relevant_memories['results']:
            formatted_memories += f"- {entry['memory']}\n"
    
    system_prompt = f'''You are a personal fitness coach with the ability to access memory. 
Your goal is to help users achieve their fitness goals by providing personalized advice and tracking their progress over time.

You have information about the user's past interactions that you can use to provide personalized advice.

User's Relevant Memories:
{formatted_memories}
    
Always be supportive, encouraging, and provide actionable advice. Don't mention the memory system directly to the user - they should just experience personalized advice.'''
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': message}
    ]
    
    with st.spinner('Thinking...'):
        response = openai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
        )
        response_text = response.choices[0].message.content
        
    # Create new memories from the conversation
    messages.append(
        {'role': 'assistant', 'content': response_text}
    )
    memory.add(messages=messages, user_id=user_id)
    
    return response_text

# Init session state
if not st.session_state.get('messages', None):
    st.session_state.messages = []

if not st.session_state.get('authenticated', None):
    st.session_state.authenticated = False

if not st.session_state.get('user', None):
    st.session_state.user = None

if not st.session_state.get('health_profile', None):
    st.session_state.health_profile = {
        'goals': '',
        'fitness_level': '',
        'dietary_preferences': '',
        'medical_conditions': '',
    }
    
# Check for logout flag and clear it after processing
if st.session_state.get('logout_requested', False):
    st.session_state.logout_requested = False
    st.rerun()

# Sidebar for authentication and health profile
with st.sidebar:
    st.title('🏋️‍♀️ Fitness Coach Assistant with Memory')
    
    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(['Sign In', 'Sign Up'])
        with tab1:
            st.subheader('Sign In')
            signin_email = st.text_input(
                'Email', key='signin_email'
            )
            signin_password = st.text_input(
                'Password', type='password', key='signin_password'
            )
            signin_button = st.button('Sign In')

            if signin_button:
                if signin_email and signin_password:
                    sign_in(signin_email, signin_password)
                else:
                    st.warning('Please enter both email and password')

        with tab2:
            st.subheader('Sign Up')
            signup_email = st.text_input(
                'Email', key='signup_email'
            )
            signup_password = st.text_input(
                'Password', type='password', key='signup_password'
            )
            signup_name = st.text_input(
                'Full Name', key='signup_name'
            )
            signup_button = st.button('Sign Up')

            if signup_button:
                if signup_email and signup_password and signup_name:
                    response = sign_up(signup_email, signup_password, signup_name)
                    if response and response.user:
                        st.success('Sign up successful! Please check your email to confirm your account')
                    else:
                        st.error('Sign up failed. Please try again')
                else:
                    st.warning('Please fill in all fields')
    
    else:
        user = st.session_state.user
        if user:
            st.success(f'Signed in as {user.email}')
            st.button('Sign out', on_click=sign_out)
        
            # Display and edit health profile
            st.subheader('Your Health Profile')
            
            with st.expander('Update your health profile', expanded=False):
                st.session_state.health_profile['goals'] = st.text_area(
                    'Your Fitness Goals',
                    value=st.session_state.health_profile['goals'],
                    placeholder='e.g., Lose weight, Build muscle, Improve endurance...',
                )

                st.session_state.health_profile['fitness_level'] = st.selectbox(
                    'Current Fitness Level',
                    options=['Beginner', 'Intermediate', 'Advanced'],
                    index=(
                        0 
                        if not st.session_state.health_profile['fitness_level']
                        else ['Beginner', 'Intermediate', 'Advanced'].index(
                            st.session_state.health_profile['fitness_level']
                        )
                    ),
                )

                st.session_state.health_profile['dietary_preferences'] = st.text_area(
                    'Dietary Preferences/Restrictions',
                    value=st.session_state.health_profile['dietary_preferences'],
                    placeholder='e.g., Vegetarian, Low carb, No dairy...',
                )

                st.session_state.health_profile['medical_conditions'] = st.text_area(
                    'Medical Conditions (if any)',
                    value=st.session_state.health_profile['medical_conditions'],
                    placeholder='e.g., Asthma, Knee injury, Heart condition...',
                )

                if st.button('Save Profile'):
                    # Create a memory entry for the health profile
                    profile_message = f'''User updated their health profile:
- Goals: {st.session_state.health_profile["goals"]}
- Fitness Level: {st.session_state.health_profile["fitness_level"]}
- Dietary Preferences: {st.session_state.health_profile["dietary_preferences"]}
- Medical Conditions: {st.session_state.health_profile["medical_conditions"]}'''
                    
                    # Add the profile message to memory
                    memory.add(
                        messages=[
                            {'role': 'system', 'content': 'Health profile updated'},
                            {'role': 'user', 'content': profile_message}
                        ],
                        user_id=user.id
                    )
                    
                    st.success('Health profile saved successfully!')
            
            # Memory management options
            st.subheader('Memory Management')
            if st.button('Clear All Memories'):
                try:
                    # Check if the memory object has a clear method
                    if hasattr(memory, 'clear'):
                        memory.clear(user_id=user.id)
                    else:
                        # Alternative approach if memory.clear() is not available.
                        # Use the search and delete approach
                        memories = memory.search(
                            query='*',
                            user_id=user.id,
                            limit=1000
                        )
                        
                        if memories and 'results' in memories:
                            # Log information for debugging
                            st.write(f'Found {len(memories["results"])} memories for user {user.id}')
                            
                            # We can't delete directly as we don't have a direct deletion API in memory object
                            # Instead, we'll clear the session and inform the user
                            st.info('Memory system does not support direct clearing. Session has been reset instead')
                        
                    # Clear the session state
                    st.session_state.messages = []
                    st.success('Chat history cleared successfully!')
                    st.rerun()
                except Exception as e:
                    st.error(f'Failed to clear memories: {str(e)}')

# Main chat interface
st.title('Fitness Coach with Memory')
if st.session_state.authenticated and st.session_state.user:
    user_id = st.session_state.user.id
    
    st.write('I am your AI fitness coach with memory. I can provide personalized fitness advice')
    
    # Quick action buttons
    st.subheader('Quick Actions')
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button('📝 Today Workout'):
            quick_prompt = 'Can you suggest a workout for me today based on my fitness level and goals?'
            st.session_state.messages.append({'role': 'user', 'content': quick_prompt})
            response = get_response(quick_prompt, user_id)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()

    with col2:
        if st.button('🍎 Nutrition Advice'):
            quick_prompt = 'Can you give me some nutrition tips based on my dietary preferences and fitness goals?'
            st.session_state.messages.append({'role': 'user', 'content': quick_prompt})
            response = get_response(quick_prompt, user_id)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()

    with col3:
        if st.button('📊 Track Progress'):
            quick_prompt = 'I want to track my fitness progress. What metrics should I be monitoring and how?'
            st.session_state.messages.append({'role': 'user', 'content': quick_prompt})
            response = get_response(quick_prompt, user_id)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()

    with col4:
        if st.button('🧘 Recovery Tips'):
            quick_prompt = 'What are some good recovery practices I should incorporate into my fitness routine?'
            st.session_state.messages.append({'role': 'user', 'content': quick_prompt})
            response = get_response(quick_prompt, user_id)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()

    st.divider()
    
    # Display chat messages:
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.write(message['content'])

    # Chat input
    user_input = st.chat_input('Ask your fitness coach...')
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({'role': 'user', 'content': user_input})
        
        # Display user message
        with st.chat_message('user'):
            st.write(user_input)
        
        # Get response 
        response = get_response(user_input, user_id)
        
        # Add model response to chat history
        st.session_state.messages.append({'role': 'assistant', 'content': response})
        
        # Display model response
        with st.chat_message('assistant'):
            st.write(response)

else:
    st.write('Please sign in to start chatting with your personal AI fitness coach')

    # Feature highlights
    st.subheader('Features')
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('### 🏋️ Personalized Coaching')
        st.write(
            'Get custom fitness advice based on your goals, preferences, and progress.'
        )

    with col2:
        st.markdown('### 🧠 Remembers Your Journey')
        st.write(
            'Your coach remembers your fitness history and adapts advice accordingly.'
        )

    with col3:
        st.markdown('### 📊 Progress Tracking')
        st.write('Keep track of your fitness journey with tailored recommendations.')