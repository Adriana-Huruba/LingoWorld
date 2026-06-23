import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TeacherService } from './teacher.service';

const API = 'http://localhost:8000/api';

describe('TeacherService', () => {
  let service: TeacherService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [TeacherService],
    });
    service = TestBed.inject(TeacherService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('getTeacherManuals() trimite GET la /api/manuals cu teacher_id ca param', () => {
    let manuals: any[] = [];
    service.getTeacherManuals(2).subscribe(r => manuals = r);

    const req = httpMock.expectOne(r => r.url === `${API}/manuals`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('teacher_id')).toBe('2');
    req.flush([
      { id: 4, title: 'englezaCl6a.pdf', language: 'english', level: 'B2', is_processed: true },
    ]);
    expect(manuals.length).toBe(1);
    expect(manuals[0].language).toBe('english');
  });

  it('getTeacherManuals() returneaza array gol daca profesorul nu are manuale', () => {
    let manuals: any[] = [{ id: 1 }];
    service.getTeacherManuals(99).subscribe(r => manuals = r);

    const req = httpMock.expectOne(r => r.url === `${API}/manuals`);
    req.flush([]);
    expect(manuals.length).toBe(0);
  });


  it('uploadManual() trimite POST la /api/manuals/upload cu FormData', () => {
    const file = new File(['continut pdf'], 'manual.pdf', { type: 'application/pdf' });
    let result: any;
    service.uploadManual(file, 2, 'Manual clasa 9', 'english', 'B2').subscribe(r => result = r);

    const req = httpMock.expectOne(`${API}/manuals/upload`);
    expect(req.request.method).toBe('POST');

    const body: FormData = req.request.body;
    expect(body.get('teacher_id')).toBe('2');
    expect(body.get('title')).toBe('Manual clasa 9');
    expect(body.get('language')).toBe('english');
    expect(body.get('level')).toBe('B2');

    req.flush({ manual_id: 4, message: 'Processing started' });
    expect(result.manual_id).toBe(4);
  });

  it('uploadManual() returneaza eroare 413 pentru fisier prea mare', () => {
    const file = new File(['x'.repeat(1000)], 'mare.pdf', { type: 'application/pdf' });
    let statusCode = 0;
    service.uploadManual(file, 2, 'Test', 'english', 'B1').subscribe({
      error: err => statusCode = err.status,
    });

    const req = httpMock.expectOne(`${API}/manuals/upload`);
    req.flush({ detail: 'File too large' }, { status: 413, statusText: 'Payload Too Large' });
    expect(statusCode).toBe(413);
  });

  it('deleteManual() trimite DELETE la /api/manuals/:id cu teacher_id ca param', () => {
    service.deleteManual(4, 2).subscribe();

    const req = httpMock.expectOne(r => r.url === `${API}/manuals/4`);
    expect(req.request.method).toBe('DELETE');
    expect(req.request.params.get('teacher_id')).toBe('2');
    req.flush({ message: 'Deleted' });
  });

  it('deleteManual() returneaza eroare 403 cand profesorul nu detine manualul', () => {
    let statusCode = 0;
    service.deleteManual(4, 99).subscribe({ error: err => statusCode = err.status });

    const req = httpMock.expectOne(r => r.url === `${API}/manuals/4`);
    req.flush({ detail: 'Forbidden' }, { status: 403, statusText: 'Forbidden' });
    expect(statusCode).toBe(403);
  });

  it('previewWorksheet() trimite POST la /api/worksheets/preview cu configuratia fisei', () => {
    const payload = {
      manual_id: 4, teacher_id: 2, topic: 'grammar', level: 'B2',
      language: 'english', native_language: 'romanian',
      exercise_counts: { 'multiple-choice': 2, 'fill-in-the-blank': 2, translation: 1 },
    };
    let preview: any;
    service.previewWorksheet(payload).subscribe(r => preview = r);

    const req = httpMock.expectOne(`${API}/worksheets/preview`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.manual_id).toBe(4);
    req.flush({
      items: [
        { exercise_type: 'multiple-choice', correct_answer: 'has', warnings: [] },
        { exercise_type: 'translation', correct_answer: 'Trebuie sa ai 18 ani.', warnings: [] },
      ],
      total_requested: 5, generated_count: 5, failed_count: 0,
    });
    expect(preview.items.length).toBe(2);
    expect(preview.failed_count).toBe(0);
  });

  it('previewWorksheet() expune avertismentele din exercitiile generate', () => {
    const payload = { manual_id: 4, teacher_id: 2 };
    let preview: any;
    service.previewWorksheet(payload).subscribe(r => preview = r);

    const req = httpMock.expectOne(`${API}/worksheets/preview`);
    req.flush({
      items: [
        { exercise_type: 'multiple-choice', correct_answer: 'go', warnings: ['answer not in options'] },
      ],
      total_requested: 1, generated_count: 1, failed_count: 0,
    });
    expect(preview.items[0].warnings).toContain('answer not in options');
  });


  it('regenerateItem() trimite POST la /api/worksheets/regenerate-item', () => {
    const payload = { manual_id: 4, teacher_id: 2, exercise_type: 'translation', index: 2 };
    service.regenerateItem(payload).subscribe();

    const req = httpMock.expectOne(`${API}/worksheets/regenerate-item`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.exercise_type).toBe('translation');
    req.flush({ exercise_type: 'translation', correct_answer: 'Buna ziua.', warnings: [] });
  });


  it('publishWorksheet() trimite POST la /api/worksheets/publish', () => {
    const payload = { teacher_id: 2, classroom_id: 1, title: 'Gramatica B2', items: [] };
    let result: any;
    service.publishWorksheet(payload).subscribe(r => result = r);

    const req = httpMock.expectOne(`${API}/worksheets/publish`);
    expect(req.request.method).toBe('POST');
    req.flush({ worksheet_id: 7, message: 'Published successfully' });
    expect(result.worksheet_id).toBe(7);
  });

  it('getWorksheetsByClassroom() trimite GET la /api/worksheets/classroom/:id', () => {
    let worksheets: any[] = [];
    service.getWorksheetsByClassroom(1).subscribe(r => worksheets = r);

    const req = httpMock.expectOne(`${API}/worksheets/classroom/1`);
    expect(req.request.method).toBe('GET');
    req.flush([
      { id: 7, title: 'Gramatica B2', classroom_id: 1, exercise_count: 5 },
    ]);
    expect(worksheets[0].title).toBe('Gramatica B2');
  });
});
