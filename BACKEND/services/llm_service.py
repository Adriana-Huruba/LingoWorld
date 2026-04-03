# prompt for llm

import os 
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
  print("Error: GEMINI_API_KEY was not found in .env!")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_exercises(context_chunks, topic, level, type, language): # callied in exercise_service
  whole_context_text = "\n---\n".join([c.payload['text'] for c in context_chunks])

  prompt = f"""
    You are an {language} professor. Generate an exercise of this type '{type}' for {level} level about '{topic}' in {language}.
    Use this context from textbook: {whole_context_text} to create the exercise focused only on vocabulary or grammar that appears in the context.
    Rules: 
    1. If the context doesn't have enough information, you can use it as inspiration but you should not make up content that is not related to the context.
    2. Do not ask comprehension questions. Ensure the questions are standalone and don't require reading the source text to be answered or listening to audio.
    3. The exercise should be in JSON format, with the following structure:
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

  model = genai.GenerativeModel('gemini-2.5-flash')
  response = model.generate_content(prompt)

  clean_response = response.text.strip() #nu merge
  if clean_response.startswith("```json"):
    clean_response = clean_response.replace("```json", "", 1).replace("```", "", 1).strip()
  elif clean_response.startswith("```"):
    clean_response = clean_response.replace("```", "", 1).replace("```", "", 1).strip()

  return clean_response
  