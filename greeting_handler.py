import logging
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionGreeting(Action):
    """Handle greeting messages"""

    def name(self) -> Text:
        return "action_greeting"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Send a greeting message"""
        
        dispatcher.utter_message(text="Hello! I'm AuraAI™, an intelligent assistant for Outcome-Based Education (OBE). I can help you with information about students, faculty, and more. How can I assist you today?")
        return []

class ActionGoodbye(Action):
    """Handle goodbye messages"""

    def name(self) -> Text:
        return "action_goodbye"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Send a goodbye message"""
        
        dispatcher.utter_message(text="Goodbye! Feel free to come back if you have more questions. Have a great day!")
        return [] 