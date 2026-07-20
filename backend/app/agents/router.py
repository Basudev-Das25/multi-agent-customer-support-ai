from app.agents.billing import billing_agent
from app.agents.complaint import complaint_agent
from app.agents.faq import faq_agent
from app.agents.intent import intent_classifier
from app.agents.product import product_agent
from app.agents.technical import technical_agent


class AgentRouter:
    """
    Routes a question to the correct agent.
    """

    def __init__(self):

        self.agents = {
            "faq": faq_agent,
            "technical": technical_agent,
            "billing": billing_agent,
            "product": product_agent,
            "complaint": complaint_agent,
        }

    def route(
        self,
        question: str,
    ):

        intent = intent_classifier.classify(question)

        return self.agents[intent]


router = AgentRouter()
