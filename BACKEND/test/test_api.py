"""
Integration tests for the FastAPI endpoints. The database layer and services are fully mocked

Run
    pytest test/test_api.py -v -p no:cacheprovider
"""

import sys, os
from unittest.mock import MagicMock, patch

for _mod in [
    'spylls', 'spylls.hunspell',
    'langgraph', 'langgraph.graph', 'langgraph.graph.state',
    'google.generativeai', 'google',
    'langchain_text_splitters',
    'langchain_community', 'langchain_community.document_loaders',
    'qdrant_client', 'qdrant_client.models',
    'psycopg2', 'psycopg2.extras',
    'dotenv',
    'services.agent_service',
    'services.vector_service',
    'services.llm_service',
    'services.classroom_service',
    'services.teacher_service',
    'services.teacher_collections_service',
    'services.didactic_agent',
    'services.user_service',
    'core.embeddings',
    'core.ingest_pdf',
    'core.ingest_pdf_teacher',
    'core.security',
    'repository.teacher_repository',
    'repository.user_repository',
    'dao.user_dao', 'dao.teacher_dao',
    'dao.student_dao', 'dao.classroom_dao',
]:
    sys.modules.setdefault(_mod, MagicMock())

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── Build a minimal app with only the routers under test ─────────
from api.exercises_routes import exercises_router
from api.user_routes import user_router, classroom_router

app = FastAPI()
app.include_router(exercises_router, prefix='/api')
app.include_router(user_router, prefix='/api')
app.include_router(classroom_router, prefix='/api/classrooms')

@app.get('/')
def root():
    return {'message': 'ok'}

client = TestClient(app)


def _mock_exercise():
    return {
        'exercise_id': 1, 'language': 'english', 'level': 'B1',
        'type': 'multiple-choice', 'category': 'grammar',
        'topic': 'verb_tenses',
        'content': {
            'exercise_title': 'Choose the correct form',
            'questions': 
                [{'question': 'She ___ to school.',
                'answer': 'goes',
                'options': ['go', 'goes', 'going', 'gone']}],
        },
        'correct_answer': 'goes', 'elo_difficulty': 700,
        'source_manual': 'test_manual', 'points': 10, 'reason': 'new_exercise',
    }

def _record_answer_result(correct: bool):
    delta = 16 if correct else -16
    return {
        'old_elo': 700, 'new_elo': 700 + delta, 'delta_elo': delta,
        'new_cefr': 'B1', 'level_changed': False,
        'next_review': '2026-06-01T00:00:00+00:00',
        'new_interval': 1, 'quality': 4 if correct else 1,
        'xp_gained': 10 if correct else 0,
    }


class TestRoot:
    def test_returns_200(self):
        assert client.get('/').status_code == 200

    def test_returns_message_key(self):
        assert 'message' in client.get('/').json()


class TestNextExercise:
    def test_valid_user_returns_200_and_exercise(self):
        with patch('api.exercises_routes.get_next_exercise', return_value=_mock_exercise()):
            res = client.post('/api/next-exercise', json={'user_id': 1, 'target_language': 'english'})

        assert res.status_code == 200
        assert res.json()['exercise_id'] == 1
        assert res.json()['level'] == 'B1'

    def test_no_exercise_available_returns_404(self):
        with patch('api.exercises_routes.get_next_exercise', return_value=None):
            res = client.post('/api/next-exercise', json={'user_id': 1, 'target_language': 'english'})
        assert res.status_code == 404

    def test_optional_skill_type_forwarded(self):
        captured = {}
        def mock_fn(user_id, target_language, conn, skill_type=None, topic=None):
            captured['skill_type'] = skill_type
            return _mock_exercise()

        with patch('api.exercises_routes.get_next_exercise', side_effect=mock_fn):
            client.post('/api/next-exercise', json={'user_id': 1, 'target_language': 'english', 'skill_type': 'grammar'})
        assert captured['skill_type'] == 'grammar'

    def test_optional_topic_forwarded(self):
        captured = {}
        def mock_fn(user_id, target_language, conn, skill_type=None, topic=None):
            captured['topic'] = topic
            return _mock_exercise()

        with patch('api.exercises_routes.get_next_exercise', side_effect=mock_fn):
            client.post('/api/next-exercise', json={'user_id': 1, 'target_language': 'english', 'topic': 'verb_tenses'})
        assert captured['topic'] == 'verb_tenses'

    def test_missing_user_id_returns_422(self):
        res = client.post('/api/next-exercise', json={'target_language': 'english'})
        assert res.status_code == 422


class TestSubmitAnswer:
    def _submit(self, is_correct: bool):
        with patch('api.exercises_routes.record_answer', return_value=_record_answer_result(is_correct)):
            return client.post('/api/submit-answer', json={
                'user_id': 1, 'exercise_id': 1,
                'is_correct': is_correct,
                'response_time_seconds': 10,
                'exercise_type': 'multiple-choice',
                'used_hint': False,
            })

    def test_correct_answer_returns_200(self):
        assert self._submit(True).status_code == 200

    def test_correct_answer_increases_elo(self):
        data = self._submit(True).json()
        assert data['new_elo'] > data['old_elo']

    def test_incorrect_answer_decreases_elo(self):
        data = self._submit(False).json()
        assert data['new_elo'] < data['old_elo']

    def test_correct_answer_gives_xp(self):
        assert self._submit(True).json()['xp_gained'] > 0

    def test_incorrect_answer_gives_no_xp(self):
        assert self._submit(False).json()['xp_gained'] == 0

    def test_level_change_flagged_in_response(self):
        result = {**_record_answer_result(True), 'level_changed': True, 'new_cefr': 'B2'}
        with patch('api.exercises_routes.record_answer', return_value=result):
            res = client.post('/api/submit-answer', json={
                'user_id': 1, 'exercise_id': 1, 'is_correct': True,
                'response_time_seconds': 5, 'exercise_type': 'multiple-choice',
                'used_hint': False,
            })
        assert res.json()['level_changed'] is True
        assert res.json()['new_cefr'] == 'B2'

    def test_missing_required_fields_returns_422(self):
        res = client.post('/api/submit-answer', json={'user_id': 1})
        assert res.status_code == 422


class TestInitialQuiz:
    def test_valid_language_returns_exercises(self):
        mock_exs = [MagicMock(to_dict=lambda: _mock_exercise()) for _ in range(6)]
        with patch('api.exercises_routes.get_quiz_exercises', return_value=mock_exs):
            res = client.get('/api/initial-quiz/english')

        assert res.status_code == 200
        assert res.json()['total'] == 6
        assert 'exercises' in res.json()

    def test_invalid_language_returns_404(self):
        with patch('api.exercises_routes.get_quiz_exercises', side_effect=ValueError("No content for 'klingon'")):
            res = client.get('/api/initial-quiz/klingon')
        assert res.status_code == 404


class TestInitialQuizSubmit:
    _payload = {
        'user_id': 1, 'language': 'english',
        'responses': [
            {'exercise_id': 1, 'level': 'A1', 'is_correct': True,
             'response_time_seconds': 8, 'exercise_type': 'multiple-choice',
             'used_hint': False},
        ],
    }
    _result = {'estimated_level': 'B1', 'starting_elo': 700, 'score_percent': 60.0, 'correct': 3, 'total': 5}

    def test_first_submission_succeeds(self):
        with patch('api.exercises_routes.has_completed_quiz', return_value=False), \
             patch('api.exercises_routes.submit_quiz_results', return_value=self._result):
            res = client.post('/api/initial-quiz/submit', json=self._payload)
        assert res.status_code == 200
        assert res.json()['estimated_level'] == 'B1'
        assert res.json()['starting_elo'] == 700

    def test_second_submission_returns_409(self):
        with patch('api.exercises_routes.has_completed_quiz', return_value=True):
            res = client.post('/api/initial-quiz/submit', json=self._payload)
        assert res.status_code == 409

    def test_empty_responses_returns_400(self):
        with patch('api.exercises_routes.has_completed_quiz', return_value=False), \
             patch('api.exercises_routes.submit_quiz_results',
                   side_effect=ValueError('No responses')):
            res = client.post('/api/initial-quiz/submit',
                              json={**self._payload, 'responses': []})
        assert res.status_code == 400


class TestAuth:
    def test_register_success_returns_200(self):
        with patch('api.user_routes.UserService.register_user', return_value=True):
            res = client.post('/api/register', json={
                'name': 'Test', 'email': 'test@test.com',
                'password': 'secret', 'role': 'student',
            })
        assert res.status_code == 200
        assert 'registered' in res.json()['message'].lower()

    def test_register_duplicate_email_returns_400(self):
        with patch('api.user_routes.UserService.register_user', return_value=False):
            res = client.post('/api/register', json={
                'name': 'Test', 'email': 'dup@test.com',
                'password': 'secret', 'role': 'student',
            })
        assert res.status_code == 400

    def test_login_valid_credentials_returns_200(self):
        mock_user = {'user_id': 1, 'name': 'Test', 'role': 'student', 'token': 'abc', 'language': 'english'}
        with patch('api.user_routes.UserService.login_user', return_value=mock_user):
            res = client.post('/api/login', json={'email': 'test@test.com', 'password': 'pass'})

        assert res.status_code == 200
        assert 'user' in res.json()

    def test_login_wrong_password_returns_401(self):
        with patch('api.user_routes.UserService.login_user', return_value=None):
            res = client.post('/api/login', json={'email': 'examplex@gmail.com', 'password': 'wrong'})
        assert res.status_code == 401

    def test_login_missing_email_returns_422(self):
        res = client.post('/api/login', json={'password': 'pass'})
        assert res.status_code == 422
