import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ClassroomService } from './classroom.service';
import { AuthService } from './auth.service';

const API = 'http://localhost:8000/api/classrooms';

describe('ClassroomService', () => {
  let service: ClassroomService;
  let httpMock: HttpTestingController;
  let authService: AuthService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ClassroomService, AuthService],
    });
    service = TestBed.inject(ClassroomService);
    httpMock = TestBed.inject(HttpTestingController);
    authService = TestBed.inject(AuthService);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });


  it('createClassroom() sends POST tp /api/classrooms/create with teacher_id', () => {
    authService.setSession({ user_id: 2, token: 't', role: 'teacher', name: 'Maria', email: '' });
    let inviteCode = '';
    service.createClassroom('Clasa 9A').subscribe(r => inviteCode = r.invite_code);

    const req = httpMock.expectOne(`${API}/create`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Clasa 9A', teacher_id: 2 });
    req.flush({ invite_code: 'ABC123' });
    expect(inviteCode).toBe('ABC123');
  });

  it('createClassroom() returns 400 for invalid name', () => {
    authService.setSession({ user_id: 2, token: 't', role: 'teacher', name: 'Maria', email: '' });
    let errorReceived = false;
    service.createClassroom('').subscribe({ error: () => errorReceived = true });

    const req = httpMock.expectOne(`${API}/create`);
    req.flush({ detail: 'Classroom name is required' }, { status: 400, statusText: 'Bad Request' });
    expect(errorReceived).toBeTrue();
  });


  it('enrollStudent() sends POST at /api/classrooms/enroll cu student_id și invite_code', () => {
    let message = '';
    service.enrollStudent(5, 'XYZ789').subscribe(r => message = r.message);

    const req = httpMock.expectOne(`${API}/enroll`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ student_id: 5, invite_code: 'XYZ789' });
    req.flush({ message: 'Enrolled successfully' });
    expect(message).toBe('Enrolled successfully');
  });

  it('enrollStudent() returns 404 for invalid invitation code', () => {
    let statusCode = 0;
    service.enrollStudent(5, 'INVALID').subscribe({ error: err => statusCode = err.status });

    const req = httpMock.expectOne(`${API}/enroll`);
    req.flush({ detail: 'Invalid invite code' }, { status: 404, statusText: 'Not Found' });
    expect(statusCode).toBe(404);
  });



  it('getClassroomsOfTeacher() sends GET to /api/classrooms/all/:teacherId', () => {
    authService.setSession({ user_id: 2, token: 't', role: 'teacher', name: 'Maria', email: '' });
    let classrooms: any[] = [];
    service.getClassroomsOfTeacher().subscribe(r => classrooms = r.classrooms);

    const req = httpMock.expectOne(`${API}/all/2`);
    expect(req.request.method).toBe('GET');
    req.flush({ classrooms: [{ id: 1, name: 'Clasa 9A', invite_code: 'ABC123', student_count: 20 }] });
    expect(classrooms.length).toBe(1);
    expect(classrooms[0].name).toBe('Clasa 9A');
  });


  it('getClassroomStudents() sends GET to /api/classrooms/:id/students', () => {
    let students: any[] = [];
    service.getClassroomStudents(3).subscribe(r => students = r.students);

    const req = httpMock.expectOne(`${API}/3/students`);
    expect(req.request.method).toBe('GET');
    req.flush({ students: [{ id: 10, name: 'Ion', email: 'ion@test.ro' }] });
    expect(students[0].name).toBe('Ion');
  });


  it('getStudentClassrooms() sends GET to /api/classrooms/student-classes/:studentId', () => {
    service.getStudentClassrooms(10).subscribe();

    const req = httpMock.expectOne(`${API}/student-classes/10`);
    expect(req.request.method).toBe('GET');
    req.flush({ classrooms: [] });
  });


  it('getClassroomAssignments() sends GET to /api/classrooms/:id/assignments', () => {
    let assignments: any[] = [];
    service.getClassroomAssignments(1).subscribe(r => assignments = r.assignments);

    const req = httpMock.expectOne(`${API}/1/assignments`);
    expect(req.request.method).toBe('GET');
    req.flush({ assignments: [{ id: 5, title: 'Fisa gramatica', classroom_id: 1 }] });
    expect(assignments[0].title).toBe('Fișa gramatica');
  });


  it('getAssignmentById() sends GET to /api/classrooms/assignments/:id', () => {
    service.getAssignmentById(5).subscribe();

    const req = httpMock.expectOne(`${API}/assignments/5`);
    expect(req.request.method).toBe('GET');
    req.flush({ id: 5, title: 'Worksheet', exercises: [] });
  });


  it('getStudentProgress() sends GET to /api/classrooms/:id/student-progress', () => {
    service.getStudentProgress(1).subscribe();

    const req = httpMock.expectOne(`${API}/1/student-progress`);
    expect(req.request.method).toBe('GET');
    req.flush({ students: [{ id: 10, name: 'Ion', elo: 700, level: 'B1' }] });
  });


  it('completeWorksheet() sends POST with studentId, worksheetId, score, total', () => {
    let success = false;
    service.completeWorksheet(10, 5, 8, 10).subscribe(r => success = r.success);

    const req = httpMock.expectOne(`${API}/complete-worksheet`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ student_id: 10, worksheet_id: 5, score: 8, total: 10 });
    req.flush({ success: true });
    expect(success).toBeTrue();
  });
});
