import json
import os
import re
import random
from typing import Optional, TypedDict
from spylls.hunspell import Dictionary
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

from core.embeddings import create_embedding
from services.vector_service import search_similar
from dao.exercise_dao import ExerciseDAO


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


DICT_PATH = os.path.join(os.path.dirname(__file__), "../data/dicts")
LANG_TO_DICT = {
    "english": "en_US",
    "french": "fr_FR",
    "spanish": "es_ES",
    "romanian": "ro_RO",
}
_dict_cache: dict[str, Dictionary] = {}


def _get_dict(language: str) -> Optional[Dictionary]:
    code = LANG_TO_DICT.get(language.lower())
    if not code:
        return None
    if code not in _dict_cache:
        base = os.path.join(DICT_PATH, code) 
        aff = base + ".aff"
        dic = base + ".dic"
        if os.path.exists(aff) and os.path.exists(dic):
            _dict_cache[code] = Dictionary.from_files(base)
    return _dict_cache.get(code)


class ExerciseAgentState(TypedDict):
    user_id: int
    topic: str
    level: str
    exercise_type: str
    language: str
    native_language: str
    skill_type: Optional[str]
    conn: object
    context_chunks: list
    raw_json: str
    exercise: dict
    retry_count: int
    validation_errors: list[str]
    saved_exercise_id: Optional[int]
    error: Optional[str]


MAX_RETRIES = 3


def _build_multiple_choice_prompt(state: ExerciseAgentState, whole_context: str) -> str:
    native = state.get("native_language", "romanian")

    return f"""
    The topic the student is learning about is: {state['topic']}.
    Context from textbook:
    {whole_context}
    
    Task: Create ONE standalone multiple-choice question testing the topic: '{state['topic']}'.
    
    GUARDRAILS (STRICT RULES):
    1. NO TRIVIA: Sentence **MUST** be standalone without the need of more context to be understood. No references to any text.
    2. THE DISTRACTOR RULE: The correct answer must fit perfectly in the blank (___). The 3 distractors **MUST** be unambiguously incorrect (grammatically wrong or logically absurd). 
    3. VOCABULARY FREEDOM AND REALITY: Distractors CAN be words outside the provided context, BUT they **MUST** be real, existing words in {state['language']} and appropriate for the {state['level']} level. DO NOT invent words.
    4. JSON FORMAT ONLY: Output ONLY a valid JSON object.
    5. The 'exercise_title' **MUST** be a requirement for the user to fill in the blank with a verb conjugation, preposition, noun or whatever part of speech is right for completing the sentence. It **MUST** be in {native}.
    6. The 'base_sentence' **MUST** be the complete sentence without any missing words. It has to be related to the {state['topic']}.
    7. The 'question' **MUST** be the sentence with a missing word that the user has to fill in using the options.
    8. The 'options' **MUST** be a **LIST** of *distractors(strings)* with a **SINGLE** right answer.
    9. The 'answer' **MUST** be the missing word that fits the sentence and it **MUST** be found in the list of options.
    
    *Here is an example of how the output structure and content should look like*:
    Output:
    {{
      "exercise_title": "Choose the correct word",
      "base_sentence": "Every morning, I brush my teeth.",
      "question": "Every morning, I ___ my teeth.",
      "options": ["brush", "brushes", "brushing", "brushed"],
      "answer": "brush"
    }}
    """


def _build_fill_in_the_blank_prompt(state: ExerciseAgentState, whole_context: str) -> str:
    native = state.get("native_language", "romanian")
    return f"""
    The topic the student is learning about is: {state['topic']}.
    Context from textbook:
    {whole_context}
    
    Task: Create ONE fill-in-the-blank question testing '{state['topic']}'.
    
    GUARDRAILS (STRICT RULES):
    1. NO TRIVIA: Sentence **MUST** be standalone without the need of more context to be understood. No references to any text.
    2. ONE CLEAR ANSWER: The blank (___) must have only **ONE** logical and grammatically correct answer based on the context. 
    Provide a context so the user understands what word he has to complete.
    3. The 'exercise_title' **MUST** be a requirement for the user to fill in the blank with a verb conjugation, preposition, noun or whatever part of speech is right for completing the sentence. It **MUST** be in {native}.
    4. The 'base_sentence' **MUST** be the complete sentence without any missing words. It has to be related to the {state['topic']}.
    5. The 'question' **MUST** be the sentence with a missing word that the user has to fill in.
    6. The 'answer' **MUST** be the missing word.
    
    *Here is are some examples of how the output structure and content should look like*:
    1. Output:
    {{
      "exercise_title": "Fill in the blank with the right verb conjugation",
      "base_sentence": "Nous allons au cinéma ce soir.",
      "question": "Nous ___ (aller) au cinéma ce soir.",
      "answer": "allons"
    }}
    2. Output:
    {{
      "exercise_title": "Fill in the blank with the right preposition",
      "base_sentence:": "I did not have time to catch up with the news. What happened?",
      "question": "I did not have time to catch __ with the news. What happened?",
      "answer": "up"
    }}
    """


def _build_translation_prompt(state: ExerciseAgentState, whole_context: str) -> str:
    native = state.get("native_language", "romanian")
    return f"""
    Context from textbook:
    {whole_context}
    
    Task: Extract one natural sentence from the context and create a translation exercise.
    
    GUARDRAILS (STRICT RULES):
    1. The 'base_sentence' **MUST** be a real, complete sentence extracted or slightly adapted from the context. It **MUST** be in {state['language']} language.
    2. The 'question' **MUST** instruct the student to translate the base_sentence into {native} language.
    3. The 'answer' **MUST** be in {native} language.
    
    *Here is an example of how the output structure and content should look like*:
    Output:
    {{
      "base_sentence": "Me gusta comer manzanas.",
      "question": "Translate to romanian.",
      "answer": "Îmi place să mănânc mere"
    }}
    """


def _build_match_prompt(state: ExerciseAgentState, whole_context: str) -> str:
    native = state.get("native_language", "romanian")
    return f"""
    The topic is {state['topic']}.
    Context from textbook:
    {whole_context}
    
    Task: Create **ONE** matching exercise with *exactly 5 pairs* based on the text and {state['topic']}.
    
    GUARDRAILS (STRICT RULES):
    1. For levels A1 and A2 the 'target' is a word in {state['language']}, the 'native' is the translation in {native}.
    2. For levels B1, B2, C1 and C2 the 'target' is a word/phrase in {state['language']}, the 'native' is a short definition or synonym in {native}.
    3. ALL 'target' words **MUST** appear in the provided context.
    4. Every word should be written in low case, unless it is a name or if the context allows it to be in upper case.
    5. JSON FORMAT ONLY: Output **ONLY** a valid JSON object.

    
    *Here is an example of how the output structure and content should look like*:
    Output for A1, A2 levels:
    {{
      "exercise_title": "Match the words",
      "pairs": [
        {{"target": "coche", "native": "mașină"}},
        {{"target": "perro", "native": "câine"}},
        {{"target": "manzana", "native": "măr"}},
        {{"target": "casa", "native": "casă"}},
        {{"target": "bolígrafo", "native": "stilou"}}
      ]
    }}
    Output for B1, B2, C1, C2 levels:
    {{
      "exercise_title": "Match the words",
      "pairs": [
        {{"target": "pasar desapercibido", "native": "a trece neobservat"}},
        {{"target": "tomar el pelo", "native": "a păcăli"}},
        {{"target": "efímero", "native": "efemer"}},
        {{"target": "paulatinamente", "native": "treptat"}},
        {{"target": "reacio", "native": "reticent"}}
      ]
    }}
    """


def fetch_context_node(state: ExerciseAgentState) -> ExerciseAgentState:
    """
    Retrieves relevant textbook context from the vector database using semantic search.

    Constructs a query based on the current state (language, level, skill, topic) and fetches similar chunks from Qdrant.
    It randomly selects a subset of retrieved chunks to ensure variety in exercise generation.

    Args:
        state (ExerciseAgentState): the current state of the LangGraph agent

    Returns:
        ExerciseAgentState: The updated state containing the retrieved context chunks/an error if context is insufficient 
    """

    query = f"{state['language']} {state['level']} {state['skill_type'] or ''} {state['topic'] or ''}".strip()
    
    vector = create_embedding(query)

    chunks = search_similar(vector=vector, language=state["language"].lower(), level=state["level"], skill_type=state["skill_type"],)

    if not chunks:
        return {**state, "error": "insufficient_context", "context_chunks": []}

    pool_size = min(len(chunks), 15) 
    random_pool = chunks[:pool_size]

    selected_chunks = random.sample(random_pool, min(len(random_pool), 4)) 

    anchor = selected_chunks[0]
    payload = anchor.payload

    if state["topic"] and state["topic"] != "general":
        actual_topic = state["topic"]
    else:
        actual_topic = payload.get("topic", "general")

    if state["skill_type"] and state["skill_type"] != "general":
        actual_skill = state["skill_type"]
    else:
        actual_skill = payload.get("skill_type", "general")

    print(f"[Agent] topic from textbook: '{actual_topic}', skill: '{actual_skill}'")
    return {**state, "context_chunks": selected_chunks, "topic": actual_topic, "skill_type": actual_skill, "error": None}


def generate_node(state: ExerciseAgentState) -> ExerciseAgentState:
    """
    Calls the Gemini LLM to generate an exercise based on the retrieved context.

    Builds a specialized prompt depending on the requested exercise type and incorporates any previous validation errors if this is a retry attempt.

    Args:
        state (ExerciseAgentState): The current state containing context chunks 
        and exercise configuration.

    Returns:
        ExerciseAgentState: The updated state containing the raw JSON string returned by the LLM/an error message if the API call fails
    """

    chunks = state["context_chunks"]
    whole_context = "\n---\n".join([c.payload["text"] for c in chunks])
    system_prompt=f" You are a language teacher creating materials for a {state['level']} level student learning {state['language']}."

    if state["exercise_type"] == "multiple-choice":
        prompt = _build_multiple_choice_prompt(state, whole_context)
    elif state["exercise_type"] == "fill-in-the-blank":
        prompt = _build_fill_in_the_blank_prompt(state, whole_context)
    elif state["exercise_type"] == "match":
        prompt = _build_match_prompt(state, whole_context)
    elif state["exercise_type"] == "translation":
        prompt = _build_translation_prompt(state, whole_context)
    else:
        prompt = _build_fill_in_the_blank_prompt(state, whole_context) # fallback

    if state["retry_count"] > 0 and state["validation_errors"]:
        prompt += "\n ATTENTION! You made mistakes in the previous generation. Please correct them:\n"
        for err in state["validation_errors"]:
            prompt += f"- {err}\n"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            )
        )
        raw_text = response.text
        if not raw_text:
            return {**state, "raw_json": "", "validation_errors": ["Gemini returned empty response (possible safety block)"]}
        return {**state, "raw_json": raw_text.strip()}
    except Exception as e:
        print(f"[Agent][generate] Gemini API error: {e}")
        return {**state, "raw_json": "", "validation_errors": [f"Gemini API error: {e}"]}


def validate_node(state: ExerciseAgentState) -> ExerciseAgentState:
    try:
        exercise = json.loads(state["raw_json"])
    except json.JSONDecodeError as e:
        print("[Agent][validate] JSON decode error:", e, "raw_json:", state.get("raw_json"))
        return {**state, "exercise": {}, "validation_errors": [f"JSON invalid: {e}"]}

    if "error" in exercise:
        return {**state, "exercise": {}, "error": "insufficient_context", "validation_errors": []}

    if state["exercise_type"] == "match":
        return _validate_match(state, exercise)
    return _validate_standard(state, exercise)


def _validate_match(state: ExerciseAgentState, exercise: dict) -> ExerciseAgentState:
    errors = []
    pairs = exercise.get("pairs", [])
    if not pairs or len(pairs) < 4:
        errors.append(f"Too few pairs: ({len(pairs)}). We need a minimum of 4")
    else:
        full_context = " ".join([c.payload["text"] for c in state["context_chunks"]]).lower()
        for i, p in enumerate(pairs):
            target = p.get("target", "").strip()
            if not target or not p.get("native", "").strip():
                errors.append(f"Pair {i+1} has uncomplete fields.")
            elif target.lower() not in full_context:
                errors.append(f"Pair {i+1}: '{target}' does not appear in the context!")

    print("[Agent][validate_match] errors:", errors)
    return {**state, "exercise": exercise, "validation_errors": errors}


def _validate_standard(state: ExerciseAgentState, exercise: dict) -> ExerciseAgentState:
    errors = []
    ex_type = state["exercise_type"]
    answer = exercise.get("answer", "").lower().strip()

    if not answer:
        errors.append("Exercise is missing 'answer' field.")

    if ex_type == "multiple-choice":
        options = exercise.get("options", [])
        options_lower = [o.lower() for o in options]
        if not options or len(options) != 4:
            errors.append("Multiple choice requires exactly 4 options.")
        elif answer and answer not in options_lower:
            errors.append(f"Correct answer '{answer}' is not in options.")
        elif len(set(options_lower)) != len(options_lower):
            errors.append("Options contain duplicates.")

    # hunspell validation
    dictionary = _get_dict(state["language"])
    if dictionary and ex_type != "translation":
        bad_words = []
        fields_to_check = [exercise.get("question", "")]
        if ex_type == "multiple-choice":
            fields_to_check.extend(exercise.get("options", []))
            
        for field in fields_to_check:
            words = re.findall(r"[a-zA-ZÀ-ÿăâîșțĂÂÎȘȚ''-]+", field)
            for word in words:
                if len(word) > 2 and not dictionary.lookup(word):
                    bad_words.append(word)
                    
        if len(bad_words) > 0:
            errors.append(f"Spell check failed for non-existent words: {list(set(bad_words))[:5]}")
    
    print("[Agent][validate_standard] errors:", errors)
    return {**state, "exercise": exercise, "validation_errors": errors}


def save_node(state: ExerciseAgentState) -> ExerciseAgentState:
    exercise = state["exercise"]
    chunks = state["context_chunks"]
    conn = state["conn"]
    chunk_payload = chunks[0].payload
    
    specific_level = chunk_payload.get("chunk_level", state["level"])
    elo = {"A1": 200, "A2": 450,"B1": 700, "B2": 900, "C1": 1100, "C2": 1300}.get(specific_level, 700)

    if state["exercise_type"] == "match":
        content = {"exercise_title": exercise.get("exercise_title", ""), "pairs": exercise.get("pairs", [])}
        correct_answer = json.dumps(exercise.get("pairs", []), ensure_ascii=False)
    else:
        content = {
            "exercise_title": exercise.get("exercise_title", "Practice"),
            "base_sentence": exercise.get("base_sentence", ""),
            "question": exercise.get("question", "")
        }
        if state["exercise_type"] == "multiple-choice":
            content["options"] = exercise.get("options", [])
        correct_answer = exercise.get("answer", "")

    # Skip DB insert when conn=None (e.g. during tests)
    if conn is None:
        result = {
            "type": state["exercise_type"],
            "language": state["language"],
            "level": specific_level,
            "content": content,
            "correct_answer": correct_answer,
        }
        return {**state, "exercise": {**exercise, **result}, "saved_exercise_id": None, "error": None}

    ex_id = ExerciseDAO.insert_exercise(
        language=state["language"].lower(),
        level=specific_level,
        exercise_type=state["exercise_type"].replace("_", "-"),
        category=chunk_payload.get("skill_type", state["skill_type"] or "general"),
        topic=chunk_payload.get("topic", state["topic"]),
        content=content,
        correct_answer=correct_answer,
        elo_difficulty=elo,
        source_manual=chunk_payload.get("source", ""),
        conn=conn,
    )

    if not ex_id:
        return {**state, "error": "save_failed"}

    saved = ExerciseDAO.find_by_id(ex_id, conn)
    if saved:
        return {**state, "exercise": saved, "saved_exercise_id": ex_id, "error": None}
    return {**state, "saved_exercise_id": ex_id, "error": None}


def after_fetch(state: ExerciseAgentState) -> str:
    return "end_error" if state.get("error") == "insufficient_context" else "generate"


def after_validate(state: ExerciseAgentState) -> str:
    if state.get("error") == "insufficient_context": 
        return "end_error"
    if state["validation_errors"]: return "end_error" if state["retry_count"] >= MAX_RETRIES else "retry"
    return "save"


def retry_node(state: ExerciseAgentState) -> ExerciseAgentState:
    print(f"[Agent] Retry {state['retry_count'] + 1}/{MAX_RETRIES}. Errors: {state['validation_errors']}")
    return {**state, "retry_count": state["retry_count"] + 1}


def build_exercise_agent() -> CompiledStateGraph:
    graph = StateGraph(ExerciseAgentState)
    graph.add_node("fetch_context", fetch_context_node)
    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)
    graph.add_node("retry", retry_node)
    graph.add_node("save", save_node)

    graph.set_entry_point("fetch_context")
    graph.add_conditional_edges("fetch_context", after_fetch, {"generate": "generate", "end_error": END})
    graph.add_edge("generate", "validate")
    graph.add_conditional_edges("validate", after_validate, {"save": "save", "retry": "retry", "end_error": END})
    graph.add_edge("retry", "generate")
    graph.add_edge("save", END)
    return graph.compile()


_agent = build_exercise_agent()


def run_exercise_agent(user_id: int, topic: str, level: str, exercise_type: str, language: str, skill_type: Optional[str], conn, native_language: str = "romanian") -> Optional[dict]:
    """
    Invokes the LangGraph exercise generation agent for independent learners.

    Initializes the agent's state with the user's request parameters and triggers the RAG pipeline

    Args:
        user_id (int): the ID of the user requesting the exercise
        topic (str): the specific topic to generate the exercise for
        level (str): the CEFR level of the user
        exercise_type (str): the type of exercise to generate (multiple-choice, fill-in-the=blank)
        language (str): the target language being learned
        skill_type (Optional[str]): the specific skill area (grammar, vocabulary)
        conn: the database connection object
        native_language (str, optional): the user's native language. Defaults to "romanian"

    Returns:
        Optional[dict]: The generated and validated exercise dictionary, 
        or None if generation fails.
    """

    initial_state: ExerciseAgentState = {
        "user_id": user_id,
        "topic": topic,
        "level": level,
        "exercise_type": exercise_type,
        "language": language,
        "native_language": native_language,
        "skill_type": skill_type,
        "conn": conn,
        "context_chunks": [],
        "raw_json": "",
        "exercise": {},
        "retry_count": 0,
        "validation_errors": [],
        "saved_exercise_id": None,
        "error": None,
    }
    final_state = _agent.invoke(initial_state)
    if final_state.get("error"):
        print(f"[Agent] Error: {final_state['error']}")
        return None
    return final_state.get("exercise") or None


def generate_hint(exercise_type: str, question: str, options: list, level: str, language: str, native_language: str = "romanian") -> str:
    """
    Generates a pedagogical hint for an exercise without revealing the correct answer.
    - multiple-choice: eliminates one wrong option and gives a grammatical/semantic clue
    - fill-in-the-blank: gives the first letter and grammatical category of the answer
    - translation: gives a key word translation hint
    """
    if exercise_type == "multiple-choice":
        options_str = ", ".join(f'"{o}"' for o in options) if options else "N/A"
        prompt = f"""
            You are a language teacher helping a {level} level student learning {language}.
            The student is working on this exercise:
            "{question}"
            Options: {options_str}

            Give a SHORT hint (1-2 sentences) that:
            1. Eliminates ONE obviously wrong option by briefly explaining why it's incorrect
            2. Gives a grammatical or semantic clue pointing toward the right answer
            DO NOT reveal the correct answer directly.
            Write the hint in {native_language}.
        """
    elif exercise_type == "fill-in-the-blank":
        prompt = f"""
            You are a language teacher helping a {level} level student learning {language}.
            The student is working on this fill-in-the-blank exercise:
            "{question}"

            Give a SHORT hint (1-2 sentences) that:
            1. States the grammatical category of the missing word (verb, noun, preposition, etc.)
            2. Gives the first letter of the correct answer
            DO NOT reveal the full answer.
            Write the hint in {native_language}.
        """
    elif exercise_type == "translation":
        prompt = f"""
            You are a language teacher helping a {level} level student learning {language}.
            The student needs to translate:
            "{question}"

            Give a SHORT hint (1-2 sentences) that:
            1. Translates one key word from the sentence
            2. Gives a structural clue about the sentence
            DO NOT give the full translation.
            Write the hint in {native_language}.
        """
    else:
        prompt = f"""
            You are a language teacher. Give a short 1-sentence hint for this exercise without revealing the answer:
            "{question}"
            Write in {native_language}.
        """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction="You are a helpful language teacher.",
        )
    )
    return response.text.strip()
