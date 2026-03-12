# prompt for llm

import os 
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY was not found in .env!")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

language='English'

def generate_exercises(context_chunks, level, topic, type):
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
    return response.text

  