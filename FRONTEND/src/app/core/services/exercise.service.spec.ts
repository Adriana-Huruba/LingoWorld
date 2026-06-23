import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ExerciseService } from './exercise.service';
import { AuthService } from './auth.service';

const API = 'http://localhost:8000/api';

const mockExercise = {
  exercise_id: 1, language: 'english', level: 'B2', type: 'multiple-choice',
  skill_type: 'grammar', topic: 'verb_tenses',
  content: {
    exercise_title: 'Choose the correct form',
    questions: [{ question: 'She ___ to school.', answer: 'goes', options: ['go', 'goes', 'going', 'gone'] }],
  },
  correct_answer: 'goes', elo_difficulty: 900, source_manual: 'manual.pdf', points: 10, reason: 'new',
};

describe('ExerciseService', () => {
  let service: ExerciseService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ExerciseService, AuthService],
    });
    service = TestBed.inject(ExerciseService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('getNextExercise() sends POST to /api/next-exercise with right payload', () => {
    const payload = { user_id: 1, target_language: 'english', topic: 'grammar' };
    let result: any;
    service.getNextExercise(payload).subscribe(r => result = r);

    const req = httpMock.expectOne(`${API}/next-exercise`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(mockExercise);
    expect(result.exercise_id).toBe(1);
    expect(result.correct_answer).toBe('goes');
  });

  it('getNextExercise() without topic sends payload with topic', () => {
    const payload = { user_id: 2, target_language: 'french' };
    service.getNextExercise(payload).subscribe();

    const req = httpMock.expectOne(`${API}/next-exercise`);
    expect(req.request.body.topic).toBeUndefined();
    req.flush(mockExercise);
  });


  it('submitAnswer() sends POST to /api/submit-answer', () => {
    const payload = {
      user_id: 1, exercise_id: 5, is_correct: true,
      response_time_seconds: 12, exercise_type: 'multiple-choice', used_hint: false,
    };
    let result: any;
    service.submitAnswer(payload).subscribe(r => result = r);

    const req = httpMock.expectOne(`${API}/submit-answer`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.is_correct).toBeTrue();
    req.flush({ old_elo: 900, new_elo: 916, delta_elo: 16, new_cefr: 'B2', level_changed: false });
    expect(result.delta_elo).toBe(16);
  });

  it('submitAnswer() for an incorrect exercise sends is_correct: false', () => {
    const payload = {
      user_id: 1, exercise_id: 5, is_correct: false,
      response_time_seconds: 30, exercise_type: 'translation', used_hint: true,
    };
    service.submitAnswer(payload).subscribe();

    const req = httpMock.expectOne(`${API}/submit-answer`);
    expect(req.request.body.is_correct).toBeFalse();
    expect(req.request.body.used_hint).toBeTrue();
    req.flush({ old_elo: 900, new_elo: 884, delta_elo: -16, new_cefr: 'B2', level_changed: false });
  });


  it('getHint() sends POST to /api/hint și returneaza hint-ul', () => {
    const payload = { exercise_id: 3, exercise_type: 'multiple-choice', language: 'english', level: 'B2' };
    let hint = '';
    service.getHint(payload).subscribe(r => hint = r.hint);

    const req = httpMock.expectOne(`${API}/hint`);
    expect(req.request.method).toBe('POST');
    req.flush({ hint: 'Think about subject-verb agreement.' });
    expect(hint).toBe('Think about subject-verb agreement.');
  });


  it('getTopics() sends GET to /api/alltopics cu parametri de limba si nivel', () => {
    let topics: string[] = [];
    service.getTopics('english', 'B2').subscribe(r => topics = r);

    const req = httpMock.expectOne(r => r.url === `${API}/alltopics`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('language')).toBe('english');
    expect(req.request.params.get('level')).toBe('B2');
    req.flush(['grammar', 'vocabulary', 'communication']);
    expect(topics).toContain('grammar');
  });


  it('getUserProgress() sends GET to /api/progress/:userId cu limba ca param', () => {
    service.getUserProgress(1, 'english').subscribe();

    const req = httpMock.expectOne(r => r.url === `${API}/progress/1`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('language')).toBe('english');
    req.flush({ elo: 900, cefr: 'B2', exercises_done: 42 });
  });


  it('getInitialQuiz() sends GET to /api/initial-quiz/:language', () => {
    service.getInitialQuiz('french').subscribe();

    const req = httpMock.expectOne(`${API}/initial-quiz/french`);
    expect(req.request.method).toBe('GET');
    req.flush([{ question: 'Quelle est votre profession?', options: ['médecin', 'ingénieur'] }]);
  });


  it('submitInitialQuiz() sends POST with user responses', () => {
    const payload = { user_id: 1, language: 'french', responses: [{ exercise_id: 10, is_correct: true }] };
    service.submitInitialQuiz(payload).subscribe();

    const req = httpMock.expectOne(`${API}/initial-quiz/submit`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.language).toBe('french');
    req.flush({ level: 'B1', elo: 700 });
  });


  it('hasCompletedQuiz() sends GET to /api/initial-quiz/completed/:userId', () => {
    let completed = false;
    service.hasCompletedQuiz(3).subscribe(r => completed = r.completed);

    const req = httpMock.expectOne(`${API}/initial-quiz/completed/3`);
    expect(req.request.method).toBe('GET');
    req.flush({ completed: true });
    expect(completed).toBeTrue();
  });

  it('hasCompletedQuiz() return false for new user', () => {
    let completed = true;
    service.hasCompletedQuiz(99).subscribe(r => completed = r.completed);

    const req = httpMock.expectOne(`${API}/initial-quiz/completed/99`);
    req.flush({ completed: false });
    expect(completed).toBeFalse();
  });

  it('generateExercise() sends POST to /api/generate-exercise', () => {
    const data = { user_id: 1, topic: 'grammar', level: 'B2', type: 'fill-in-the-blank', language: 'english' };
    service.generateExercise(data).subscribe();

    const req = httpMock.expectOne(`${API}/generate-exercise`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.level).toBe('B2');
    req.flush(mockExercise);
  });
});
