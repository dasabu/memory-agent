from pydantic import BaseModel, Field
from typing import Literal
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages

# Define Inquiry
class Inquiry(TypedDict):
    author: str
    to: str
    subject: str
    message_thread: str

# Define State
class State(TypedDict):
    inquiry_input: Inquiry
    messages: Annotated[list, add_messages]

# Define Router for message classification
class Router(BaseModel):
    '''Analyze the customer inquiry and route it according to its content'''
    reasoning: str = Field(
        description='Step-by-step reasoning behind the classification'
    )
    classification: Literal['ignore', 'notify', 'respond'] = Field(
        description='''The classification of a message: 
'ignore' for irrelevant messages, 
'notify' for important information that doesn't need an immediate response, 
'respond' for inquiries that need a reply''',
    )