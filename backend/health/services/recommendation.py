from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .decision import HealthAgent
from health.model import get_model

llm = get_model()

def build_recommendation_chain():

    prompt_template = """
You are a healthcare lifestyle assistant.

Convert the following clinical decision into:

- Short bullet points
- Maximum 6 bullets
- Clear and simple language
- Focus on diet, exercise, sleep, stress, monitoring

Clinical Decision:
{decision_output}
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_template),
            ("human", "{decision_output}"),
        ]
    )

    return prompt | llm | StrOutputParser()


def get_recommendations(decision_output):
    chain = build_recommendation_chain()

    return chain.invoke({
        "decision_output": decision_output
    })