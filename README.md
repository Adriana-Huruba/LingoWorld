# LingoWorld
LingoWorld is an educational web platform designed to make language learning highly personalized. Improve your grammar, vocabulary and orthography through AI-driven exercises, adapted to your skill level. 


This app is designed for:
* adult learners
* language teachers
* students

## What features does LingoWorld offer?
* An agent that generates exercises based on RAG (Retrieval Augmented-Generation) technique and validate the outputs of LLMs.
* A recommendation system that gives exercises based on user's current level of knowledge. Using ELO, the level is adjusted after every response, SM2(SuperMemo-2) helps memorizing concepts through spaced-repetition and ZPD (Zone of Proximal Development) always keeps the user in the optimal state of learning. 
* An agent that allows teachers to create worksheets for their classes based on uploaded textbooks. The worksheets are automatically posted on the classroom so that the children can solve them. The teacher can easily track their progress.

## Technologies
- **Frontend:** Angular 19
- **Backend:** Python, FastAPI
- **Relational database:** PostgreSQL
- **Vector database:** Qdrant
- **Embeddings model:** `paraphrase-multilingual-MiniLM-L12-v2`
- **LLM APIs:** Google Gemini and Groq.

## Available languages
Romanian, English, French and Spanish


## Get a view
- Adult learner mode
  
It offers multiple exercises: single choice, translate, fill in the blank, match

| Single choice exercise | Translate exercise |
| :---: | :---: |
| <img width="100%" alt="exercise 1" src="https://github.com/user-attachments/assets/0bc8ad6b-7321-4cd6-b741-258f8963a924" /> | <img width="100%" alt="exercise 2" src="https://github.com/user-attachments/assets/659b9158-351a-44f4-ab42-3caa06480a3f" /> |


### Student mode
<img width="100%" alt="modstudent" src="https://github.com/user-attachments/assets/e7e4b8e1-4a14-433a-9fcc-40c0d92af1b5" />



### Teacher mode
<img width="1896" height="985" alt="modprofesor" src="https://github.com/user-attachments/assets/86da90a7-aa59-4a1e-9213-9176b6b62888" />



## Running locally

### Backend

1. Configure the backend environment in `BACKEND/.env`.
   
It needs PostgreSQL connection settings (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`), Qdrant settings (`QDRANT_URL` and `QDRANT_API_KEY`), LLM API keys (`GEMINI_API_KEY` and `GROQ_API_KEY`) and a `JWT_SECRET_KEY`. `ADMIN_API_KEY` can optionally be configured for trusted admin requests.

2. Install the Python dependencies listed in `BACKEND/requirements.txt` in your Python environment.
   ```bash
    pip install -r requirements.txt
   ```
3. From the `BACKEND` directory, start the API:

   ```bash
   python main.py
   ```

   The API listens on `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

### Frontend

1. Install the Node.js dependencies from the `FRONTEND` directory:

   ```bash
   npm install
   ```

2. Start the Angular development server:

   ```bash
   npm start
   ```

   The frontend is available at `http://localhost:4200`.
