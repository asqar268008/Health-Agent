from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from health.model import get_embedding, get_model
from health.models import HealthProfile
import traceback


class HealthAgent:

    def __init__(self,
                 knowledge_dir="health_knowledge/knowledge",
                 evidence_dir="health_knowledge/evidence"):

        self.knowledge_dir = knowledge_dir
        self.evidence_dir = evidence_dir

    # ---------------- PROFILE ----------------
    @staticmethod
    def get_user_health_profile(user):
        try:
            profile = HealthProfile.objects.get(user=user)

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

    # ---------------- RETRIEVE CONTEXT ----------------
    def retrieve_context(self, query):

        try:
            embedding = get_embedding()

            knowledge_db = Chroma(
                collection_name="knowledge",
                persist_directory=self.knowledge_dir,
                embedding_function=embedding
            )

            evidence_db = Chroma(
                collection_name="evidence",
                persist_directory=self.evidence_dir,
                embedding_function=embedding
            )

            docs = []

            docs += knowledge_db.as_retriever(
                search_kwargs={"k": 2}
            ).invoke(query)

            docs += evidence_db.as_retriever(
                search_kwargs={"k": 2}
            ).invoke(query)

            combined = "\n\n".join(
                doc.page_content for doc in docs
            )

            # 🔥 Limit context to avoid token overflow
            return combined[:3000]

        except Exception as e:
            print("RAG RETRIEVE ERROR:", str(e))
            traceback.print_exc()
            return ""

    # ---------------- BUILD PROMPT ----------------
    def build_prompt(self, profile, context):

        system_prompt = f"""
You are a healthcare decision engine.

STRICT RULES:
- Output EXACTLY 2 lines.
- Each line must be a single actionable medical recommendation.
- No headings.
- No explanations.
- No extra words.

User Profile:
Age: {profile['age']}
Gender: {profile['gender']}
BMI: {profile['bmi']}
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

    # ---------------- MAIN DECISION ----------------
    def make_decision(self, user, user_message):

        profile = self.get_user_health_profile(user)

        if not profile:
            return "Please complete your health profile first."

        try:
            context = self.retrieve_context(user_message)

            prompt = self.build_prompt(profile, context)

            llm = get_model()  # fresh LLM every request

            chain = (
                prompt
                | llm
                | StrOutputParser()
            )

            decision = chain.invoke({
                "question": user_message
            })
            print("RAW DECISION OUTPUT:", decision)
            return decision.strip()

        except Exception as e:
            print("LLM ERROR:", str(e))
            traceback.print_exc()
            return "Unable to generate recommendation. Please try again."