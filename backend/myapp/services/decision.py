from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from myapp.model import get_embedding, get_model
from myapp.models import HealthProfile

import logging
import traceback

logger = logging.getLogger(__name__)


class HealthAgent:

    MAX_CONTEXT = 3000

    def __init__(
        self,
        knowledge_dir="health_knowledge/knowledge",
        evidence_dir="health_knowledge/evidence"
    ):
        try:
            embedding = get_embedding()

            # Load vector databases once
            self.knowledge_db = Chroma(
                collection_name="knowledge",
                persist_directory=knowledge_dir,
                embedding_function=embedding
            )

            self.evidence_db = Chroma(
                collection_name="evidence",
                persist_directory=evidence_dir,
                embedding_function=embedding
            )

        except Exception as e:
            logger.error("Vector DB init error: %s", str(e))
            traceback.print_exc()

    # ---------------- USER PROFILE ----------------

    @staticmethod
    def get_user_health_profile(user):

        try:
            profile = HealthProfile.objects.select_related("user").get(user=user)

            bmi = None
            if profile.height_cm and profile.weight_kg:
                bmi = round(
                    profile.weight_kg /
                    ((profile.height_cm / 100) ** 2),
                    2
                )

            return {
                "age": user.age,
                "gender": user.gender,
                "bmi": bmi,
                "smoking_status": profile.smoking_status,
                "alcohol_consumption": profile.alcohol_consumption,
                "exercise_frequency": profile.exercise_frequency,
                "sleep_hours": profile.sleep_hours,
                "diet_type": profile.diet_type,
            }

        except HealthProfile.DoesNotExist:
            return None

        except Exception as e:
            logger.error("Profile fetch error: %s", str(e))
            traceback.print_exc()
            return None

    # ---------------- RETRIEVE CONTEXT ----------------

    def retrieve_context(self, query):

        try:

            docs = []

            docs += self.knowledge_db.as_retriever(
                search_kwargs={"k": 2}
            ).invoke(query)

            docs += self.evidence_db.as_retriever(
                search_kwargs={"k": 2}
            ).invoke(query)

            combined = "\n\n".join(
                doc.page_content for doc in docs
            )

            return combined[:self.MAX_CONTEXT]

        except Exception as e:
            logger.error("RAG retrieval error: %s", str(e))
            traceback.print_exc()
            return ""

    # ---------------- BUILD PROMPT ----------------

    def build_prompt(self, profile, context):

        system_prompt = f"""
You are a healthcare recommendation engine.

IMPORTANT RULES:
1. Output EXACTLY two lines.
2. Each line must contain ONE actionable health recommendation.
3. No numbering.
4. No explanations.
5. No headings.
6. No extra words.

You are NOT diagnosing diseases.
Only provide general lifestyle advice.

User Profile:
Age: {profile['age']}
Gender: {profile['gender']}
BMI: {profile['bmi'] or "Unknown"}
Smoking: {profile['smoking_status']}
Alcohol: {profile['alcohol_consumption']}
Exercise: {profile['exercise_frequency']}
Diet: {profile['diet_type']}
Sleep: {profile['sleep_hours']}

Medical Knowledge:
{context}
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{question}")
            ]
        )

        return prompt

    # ---------------- OUTPUT CLEANING ----------------

    def clean_output(self, decision):

        decision = decision.strip()

        lines = decision.split("\n")

        cleaned = []

        for line in lines:
            line = line.strip()

            # Remove numbering if model adds it
            line = line.lstrip("0123456789.- ")

            if line:
                cleaned.append(line)

        return "\n".join(cleaned[:2])

    # ---------------- MAIN DECISION ----------------

    def make_decision(self, user, user_message):

        profile = self.get_user_health_profile(user)

        if not profile:
            return "Please complete your health profile first."

        try:

            safe_question = user_message[:500]

            context = self.retrieve_context(safe_question)

            prompt = self.build_prompt(profile, context)

            llm = get_model()

            chain = (
                prompt
                | llm
                | StrOutputParser()
            )

            decision = chain.invoke({
                "question": safe_question
            })

            logger.info(f"RAW DECISION OUTPUT: {decision}")

            return self.clean_output(decision)

        except Exception as e:
            logger.error("LLM decision error: %s", str(e))
            traceback.print_exc()

            return "Unable to generate recommendation. Please try again."