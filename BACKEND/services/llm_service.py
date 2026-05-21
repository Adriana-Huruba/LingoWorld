# prompt for llm

import os 
from groq import Groq
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
  print("Error: GEMINI_API_KEY was not found in .env!")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# TODO:
generation_config = {
  "response_mime_type": "application/json",
}

def generate_exercises(context_chunks, topic, level, type, language): # callied in exercise_service
  whole_context_text = "\n---\n".join([c.payload['text'] for c in context_chunks])

  prompt = f"""
    You are an {language} professor. Generate an exercise of this type '{type}' for {level} level about '{topic}' in {language}.
    Use this context from textbook: {whole_context_text} to create the exercise focused only on vocabulary or grammar that appears in the context.
    Rules: 
    1. If the context doesn't have enough information, you can use it as inspiration but you should not make up content that is not related to the context.
    2. Do not ask comprehension questions. Ensure the questions are standalone and don't require reading the source text to be answered or listening to audio.
    3. Do not generate any conversational text or explanations, only the exercise in JSON format.
    4. The exercise should be in JSON format, with the following structure:
    {{
      "exercise_title": "...",
      "questions": [
      {{ "question": "...", 
          "answer": "...", 
          "options": ["...", "..."] 
      }}
      ]
    }}
    """
    
    # response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    # return response.choices[0].message.content
    # response = client.models.generate_content(
    #     model="models/gemini-1.5-pro",
    #     contents=prompt
    # )

  model = genai.GenerativeModel(model_name='gemini-2.5-flash', generation_config=generation_config)
  response = model.generate_content(prompt)
  return response

  # try:
  #   response = client.chat.completions.create(
  #     messages=[
  #               {
  #                   "role": "system",
  #                   "content": "You are a precise educational assistant that exclusively outputs valid JSON."
  #               },
  #               {
  #                   "role": "user",
  #                   "content": prompt
  #               }
  #           ],
  #           model="llama-3.1-70b-versatile",
  #           temperature=0.2,
  #           response_format={"type": "json_object"}
  #   )
  #   return response.choices[0].message.content
        
  # except Exception as e:
  #       print(f"[Groq LLM Service] Error generating exercises: {e}")
  #       return "{}"
    

  