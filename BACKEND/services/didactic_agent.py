import asyncio
import json
import os
import re
from typing import Optional
from spylls.hunspell import Dictionary

from google import genai
from google.genai import types
from groq import Groq
from groq import AsyncGroq
from dotenv import load_dotenv

from core.embeddings import create_embedding
from services.vector_service import search_teacher_material
from dao.teacher_dao import TeacherDAO


load_dotenv()
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

DICT_PATH = os.path.join(os.path.dirname(__file__), "../data/dicts")
LANG_TO_DICT = {
    "english": "en_US", "french": "fr_FR",
    "spanish": "es_ES", "romanian": "ro_RO",
}
_dict_cache: dict[str, Dictionary] = {}


def _get_dict(language: str) -> Optional[Dictionary]:
    code = LANG_TO_DICT.get(language.lower())
    if not code:
        return None
    if code not in _dict_cache:
        base = os.path.join(DICT_PATH, code)
        if os.path.exists(base + ".aff") and os.path.exists(base + ".dic"):
            _dict_cache[code] = Dictionary.from_files(base)
    return _dict_cache.get(code)


LEVEL_TO_ELO = {"A1": 200, "A2": 450, "B1": 700, "B2": 900, "C1": 1100, "C2": 1300}


def _build_mutiple_choice_prompt(context, language, level, topic, native_language, extra, count=3):
    extra_block = f"\nADDITIONAL TEACHER INSTRUCTIONS: {extra}\n" if extra else ""
    if count==1:
        format_instruction = f"Output ONLY a valid JSON object"
    else:
        format_instruction = f"Output ONLY a valid JSON array containing exactly {count} objects"

    return f"""
        You are a language teacher creating materials for a {level} level student learning {language}.
        The topic is: {topic}.
        Context from {language} textbook: {context}
        {extra_block}

        Task: Create EXACTLY {count} distinct standalone multiple-choice questions testing the topic '{topic}'.
        Ensure that the difficulty aligns strictly with the {level} level requirements.

        GUARDRAILS (STRICT RULES):
        1. The 'exercise_title' **MUST** be a requirement for the student to fill in the blank with a verb conjugation, preposition, noun or whatever part of speech is right for completing the sentence. It *MUST* be in {native_language}.
        2. The 'base_sentence' **MUST** be a standalone sentence with no references to outside text. It *MUST* be a sentence without any missing words from the context. It has to be related to the {topic}.
        3. The 'question' **MUST** be the base_sentence with a missing word that the student has to fill in using the options.
        4. The 'options' **MUST** be a **LIST** of *distractors(strings)* with a **SINGLE** right answer. The 3 distractors must be wrong but REAL words in {language}.
        5. The 'answer' **MUST** be the missing word that fits the sentence and it **MUST** be found in the list of options.
        6. All {count} exercises **MUST** test different words or grammar rules from the context to ensure diversity.
        7. JSON FORMAT ONLY: {format_instruction}.

        Here are is an example:
        {{
            "exercise_title": "Choose the correct form of the verb",
            "base_sentence": "Lisa is watching TV with her parents at the moment.",
            "question": "Lisa ___ TV with her parents at the moment",
            "options": ["watches", "watch", "is watching", "watched"],
            "answer": "is watching"
        }}
        """


def _build_fill_in_the_blank_prompt(context, language, level, topic, native_language, extra, count=3):
    extra_block = f"\nADDITIONAL TEACHER INSTRUCTIONS: {extra}\n" if extra else ""
    format_instruction = f"Output ONLY a valid JSON object" if count == 1 else f"Output ONLY a valid JSON array containing exactly {count} objects"
    
    return f"""
        You are a language teacher creating materials for a {level} level student learning {language}.
        The topic is: {topic}.
        Context from {language} textbook: {context}
        {extra_block}
        Task: Create EXACTLY {count} distinct fill-in-the-blank questions testing '{topic}'.

        GUARDRAILS (STRICT RULES):
        1. The 'exercise_title' **MUST** be a requirement for the student to fill in the blank with a verb conjugation, preposition, noun or whatever part of speech is right for completing the sentence.
        2. The 'base_sentence' **MUST** be the complete sentence without any missing words. It has to be related to the '{topic}'.
        Provide a context so the student understands what word he has to complete.
        3. The 'question' **MUST** be the sentence with a missing word that the user has to fill in.
        4. The 'answer' **MUST** be the missing word.
        5. JSON FORMAT ONLY: {format_instruction}.

        Here are is an example:
        {{
            "exercise_title": "Fill in the blank with the right verb form of 'aller'",
            "base_sentence": "Vous allez au cinéma ce soir?",
            "question": "Vous ___ au cinéma ce soir?",
            "answer": "allez"
        }}
        """


def _build_match_prompt(context, language, level, topic, native_language, extra):
    extra_block = f"\nADDITIONAL TEACHER INSTRUCTIONS: {extra}\n" if extra else ""

    return f"""
        You are a language teacher creating materials for a {level} level student learning {language}.
        The topic is: {topic}.
        Context from {language} textbook: {context}
        {extra_block}
        Task: Create ONE matching exercise with EXACTLY 5 pairs.

        GUARDRAILS (STRICT RULES):
        1. For levels A1 and A2 the 'target' is a word in {language} and the 'native' is a translation in {native_language}.
        2. For levels B1, B2, C1 and C2 the 'target' is a word/phrase in {language}, the 'native' is a definition/synonym in {language}.
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


def _build_translation_prompt(context, language, level, topic, native_language, extra, count=3):
    extra_block = f"\nADDITIONAL TEACHER INSTRUCTIONS: {extra}\n" if extra else ""
    if count==1:
        format_instruction = f"Output ONLY a valid JSON object"
    else:
        format_instruction = f"Output ONLY a valid JSON array containing exactly {count} objects"
    
    return f"""
        You are a language teacher creating materials for a {level} level student learning {language}.
        Context from {language} textbook: {context}
        {extra_block}
        The topic is: {topic}.
        Task: Extract EXACTLY {count} distinct and natural sentences from the context and create EXACTLY {count} translation exercises.

        GUARDRAILS (STRICT RULES):
        1. The 'base_sentence' **MUST** be a real, complete sentence extracted or slightly adapted from the context. It **MUST** be in {language}.
        2. The 'question' **MUST** instruct the student to translate the base_sentence into {native_language} language.
        3. The 'answer' **MUST** be in {native_language} language.
        4. JSON FORMAT ONLY: {format_instruction}.
    
        *Here is an example of how the output structure and content should look like*:
        {{
            "base_sentence": "Me gusta comer manzanas.",
            "question": "Translate to romanian.",
            "answer": "Îmi place să mănânc mere"
        }}
        """


PROMPT_BUILDERS = {
    "multiple-choice": _build_mutiple_choice_prompt,
    "fill-in-the-blank": _build_fill_in_the_blank_prompt,
    "match": _build_match_prompt,
    "translation": _build_translation_prompt,
}


async def _generate_single_exercise(exercise_type, context, language, level, topic, native_lang, extra) -> Optional[dict]:
    builder = PROMPT_BUILDERS.get(exercise_type, _build_fill_in_the_blank_prompt)
    
    if exercise_type == "match":
        prompt = builder(context, language, level, topic, native_lang, extra)
    else:
        prompt = builder(context, language, level, topic, native_lang, extra, count=1)

    for attempt in range(3):
        try:
            response =await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            raw_text = response.choices[0].message.content
            parsed = json.loads(raw_text.strip())

            if isinstance(parsed, list):
                if len(parsed) > 0:
                    exercise = parsed[0]
                else:
                    return None
            else:
                exercise = parsed

            if not isinstance(exercise, dict):
                print(f"[Teacher agent]Unexpected type for {exercise_type}: {type(exercise)}, value: {exercise}")
                return None

            exercise["_exercise_type"] = exercise_type
            return exercise
        except Exception as e:
            err_str = str(e)
            print(f"[Teacher agent] Generating attempt {attempt+1} failed for {exercise_type}: {e}")
           
            if "429" in err_str and "retry_delay" in err_str:
                import re as _re
                match = _re.search(r"seconds:\s*(\d+)", err_str)
                wait = int(match.group(1)) + 2 if match else 30
                print(f"[Teacher agent] Rate limited, waiting {wait}s before retry...")
                await asyncio.sleep(wait)
            elif attempt < 2:
                await asyncio.sleep(3)
    return None


def _validate_exercise(exercise: dict, language: str) -> list[str]:
    warnings = []
    ex_type = exercise.get("_exercise_type", "")

    if ex_type == "match":
        pairs = exercise.get("pairs", [])
        if len(pairs) < 4:
            warnings.append(f"Few pairs: {len(pairs)} (recommended 5)")
        for i, p in enumerate(pairs):
            if not p.get("target") or not p.get("native"):
                warnings.append(f"Pair {i+1} incomplete")
    else:
        if not exercise.get("answer"):
            warnings.append("Missing answer")
        if ex_type == "multiple-choice":
            opts = exercise.get("options", [])
            if len(opts) != 4:
                warnings.append(f"Need 4 options, got {len(opts)}")
            elif exercise.get("answer", "").lower() not in [o.lower() for o in opts]:
                warnings.append("Answer not in options")

    if ex_type != "translation":
        dictionary = _get_dict(language)
        if dictionary:
            text_to_check = exercise.get("question", "")
            if ex_type == "multiple-choice":
                text_to_check += " " + " ".join(exercise.get("options", []))

            words = re.findall(r"[a-zA-ZÀ-ÿăâîșțĂÂÎȘȚ'-]+", text_to_check)
            bad = [w for w in words if len(w) > 2 and not dictionary.lookup(w)]
            if len(bad) > 3:
                warnings.append(f"Suspicious words: {list(set(bad))[:5]}")

    return warnings


async def _generate_all_async(requests, context, language, level, topic, native_lang, extra) -> list[Optional[dict]]:
    """
    Concurrently executes multiple exercise generation requests using Groq.

    Leverages asyncio.gather to process requests in parallel, reducing the total wait time when building a full worksheet. Introduces 
    a slight delay between requests to reduce API rate limits

    Args:
        requests (list[dict]): a list of dictionaries detailing the requested exercise types
        context (str): the concatenated text context retrieved from the teacher's manual
        language (str): the target language
        level (str): the target CEFR level
        topic (str): the specific topic for the exercises
        native_lang (str): The students' native language
        extra (str): additional instructions provided by the teacher

    Returns:
        list[Optional[dict]]: A list of generated exercise dictionaries
        Failed generations will appear as None.
    """

    results = []
    for i, r in enumerate(requests):
        if i > 0:
            await asyncio.sleep(1.5)
        result = await _generate_single_exercise(
            r["exercise_type"], context, language, level,
            topic, native_lang, extra,
        )
        results.append(result)
    return results


def _run_async_safely(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return asyncio.run(coro)
    except RuntimeError:
        return asyncio.run(coro)


def generate_worksheet_preview(teacher_id, manual_id, exercise_counts, level, language,
    topic = "general", native_language = "romanian", page_range: Optional[tuple[int, int]] = None,
    chapter: Optional[str] = None, extra_instructions = "", conn=None,) -> dict:
    
    manual = TeacherDAO.get_manual(manual_id, teacher_id, conn)
    if not manual:
        raise PermissionError("Manual not found or not owned by teacher")
    if not manual["is_processed"]:
        raise ValueError("Manual is still being processed")

    query = f"{topic} {level}".strip()
    query_vector = create_embedding(query)

    chunks = search_teacher_material(vector=query_vector, manual_id=manual_id, page_range=page_range, chapter=chapter, limit=20,)
    if not chunks:
        raise ValueError("No content found for the specified criteria")

    context = "\n---\n".join([c.payload["text"] for c in chunks[:8]])

    requests = []
    for ex_type, count in exercise_counts.items():
        requests.extend([{"exercise_type": ex_type}] * count)

    print(f"[TeacherAgent] Generating {len(requests)} exercises in parallel")

    results = _run_async_safely(_generate_all_async(requests, context, language, level, topic, native_language, extra_instructions ))

    elo = LEVEL_TO_ELO.get(level, 450)
    preview_items = []
    failed_count = 0

    for idx, exercise in enumerate(results):
        if exercise is None:
            failed_count += 1
            continue

        warnings = _validate_exercise(exercise, language)
        ex_type = exercise.pop("_exercise_type")

        if ex_type == "match":
            content = {
                "exercise_title": exercise.get("exercise_title", ""),
                "pairs": exercise.get("pairs", []),
            }
            correct_answer = json.dumps(exercise.get("pairs", []), ensure_ascii=False)
        else:
            content = {
                "exercise_title": exercise.get("exercise_title", ""),
                "base_sentence": exercise.get("base_sentence", ""),
                "question": exercise.get("question", ""),
            }
            if ex_type == "multiple-choice":
                content["options"] = exercise.get("options", [])
            correct_answer = exercise.get("answer", "")

        preview_items.append({
            "temp_id": f"item_{idx}",
            "exercise_type": ex_type,
            "content": content,
            "correct_answer": correct_answer,
            "elo_difficulty": elo,
            "warnings": warnings,
        })

    return {
        "items": preview_items,
        "total_requested": len(requests),
        "total_generated": len(preview_items),
        "total_failed": failed_count,
        "generation_config": {
            "manual_id": manual_id, "level": level, "language": language,
            "topic": topic, "native_language": native_language,
            "page_range": list(page_range) if page_range else None,
            "chapter": chapter, "extra_instructions": extra_instructions,
        },
    }


def regenerate_single_preview(teacher_id: int, exercise_type: str, generation_config: dict, conn=None,) -> Optional[dict]:
    manual = TeacherDAO.get_manual(generation_config["manual_id"], teacher_id, conn)
    if not manual:
        raise PermissionError("Manual not found")

    query = f"{generation_config['topic']} {generation_config['level']}".strip()
    query_vector = create_embedding(query)
    page_range = generation_config.get("page_range")
    chunks = search_teacher_material(
        vector=query_vector,
        manual_id=generation_config["manual_id"],
        page_range=tuple(page_range) if page_range else None,
        chapter=generation_config.get("chapter"),
        limit=20,
    )
    if not chunks:
        return None

    selected = chunks[4:12] if len(chunks) > 12 else chunks[:8]
    context = "\n---\n".join([c.payload["text"] for c in selected])

    result = _run_async_safely(_generate_single_exercise(
        exercise_type, context,
        generation_config["language"], generation_config["level"],
        generation_config["topic"], generation_config["native_language"],
        generation_config.get("extra_instructions", ""),
    ))

    if not result:
        return None

    warnings = _validate_exercise(result, generation_config["language"])
    ex_type = result.pop("_exercise_type")

    if ex_type == "match":
        content = {
            "exercise_title": result.get("exercise_title", ""),
            "pairs": result.get("pairs", []),
        }
        correct_answer = json.dumps(result.get("pairs", []), ensure_ascii=False)
    else:
        content = {
            "exercise_title": result.get("exercise_title", ""),
            "base_sentence": result.get("base_sentence", ""),
            "question": result.get("question", ""),
        }
        if ex_type == "multiple-choice":
            content["options"] = result.get("options", [])
        correct_answer = result.get("answer", "")

    return {
        "exercise_type": ex_type,
        "content": content,
        "correct_answer": correct_answer,
        "elo_difficulty": LEVEL_TO_ELO.get(generation_config["level"], 450),
        "warnings": warnings,
    }