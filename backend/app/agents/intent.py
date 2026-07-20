class IntentClassifier:
    """
    Classifies customer support requests into specialized agents.
    """

    BILLING_KEYWORDS = {
        "billing",
        "payment",
        "pay",
        "invoice",
        "refund",
        "subscription",
        "plan",
        "renew",
        "cancel",
        "charged",
        "charge",
        "receipt",
    }

    TECHNICAL_KEYWORDS = {
        "login",
        "log in",
        "password",
        "reset password",
        "installation",
        "install",
        "setup",
        "configure",
        "configuration",
        "error",
        "errors",
        "bug",
        "bugs",
        "crash",
        "exception",
        "failed",
        "failure",
        "cannot connect",
        "not working",
    }

    PRODUCT_KEYWORDS = {
        "product",
        "feature",
        "features",
        "pricing",
        "price",
        "compare",
        "comparison",
        "availability",
        "available",
        "edition",
        "version",
    }

    COMPLAINT_KEYWORDS = {
        "complaint",
        "complain",
        "angry",
        "frustrated",
        "dissatisfied",
        "terrible",
        "awful",
        "poor service",
        "bad service",
        "escalate",
        "manager",
        "supervisor",
    }

    FAQ_KEYWORDS = {
        "policy",
        "policies",
        "contact",
        "phone",
        "email",
        "address",
        "hours",
        "working hours",
        "company",
        "about",
    }

    def classify(
        self,
        question: str,
    ) -> str:

        question = question.lower()

        if any(keyword in question for keyword in self.BILLING_KEYWORDS):
            return "billing"

        if any(keyword in question for keyword in self.TECHNICAL_KEYWORDS):
            return "technical"

        if any(keyword in question for keyword in self.PRODUCT_KEYWORDS):
            return "product"

        if any(keyword in question for keyword in self.COMPLAINT_KEYWORDS):
            return "complaint"

        if any(keyword in question for keyword in self.FAQ_KEYWORDS):
            return "faq"

        return "faq"


intent_classifier = IntentClassifier()
