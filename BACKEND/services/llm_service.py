# prompt for llm

import os 
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
  print("Error: GEMINI_API_KEY was not found in .env!")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_exercises(context_chunks, topic, level, type, language=None): # callied in exercise_service
  whole_context_text = "\n---\n".join([c.payload['text'] for c in context_chunks])

  prompt = f"""
    You are an {language} professor. Generate an exercise of this type '{type}' for {level} level about '{topic}'.
    Context from textbook: {whole_context_text}
    Use the vocabulary and grammar from the context above. 
    You have to response only in JSON format:
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
  