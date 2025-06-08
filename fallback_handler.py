import logging
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionFallback(Action):
    """Handle fallback when no intent is recognized"""

    def name(self) -> Text:
        return "action_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Send a fallback message"""
        
        message = tracker.latest_message.get('text', '')
        logger.info(f"Fallback triggered for message: {message}")
        
        dispatcher.utter_message(text="I'm sorry, I didn't understand that. I can help you with information about students, faculty, and subjects. Could you please rephrase your question?")
        
        # Provide examples of what the user can ask
        dispatcher.utter_message(text="Here are some examples of what you can ask me:")
        dispatcher.utter_message(text="- Who is Aamir Khan?")
        dispatcher.utter_message(text="- Tell me about student 21CS1001")
        dispatcher.utter_message(text="- Show all students in year 3")
        dispatcher.utter_message(text="- List students in section A")
        dispatcher.utter_message(text="- Who teaches Computer Networks?")
        dispatcher.utter_message(text="- What subjects does Dr. Sreenath teach?")
        
        return [] 