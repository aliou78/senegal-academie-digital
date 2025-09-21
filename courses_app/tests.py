from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Course, Module, Lesson, Quiz, Question, Answer, Enrollment

User = get_user_model()

class CoursesTestCase(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(username='inst', password='pass')
        self.student = User.objects.create_user(username='stud', password='pass')
        self.course = Course.objects.create(instructor=self.instructor, title='Test Course', description='Desc')
        self.module = Module.objects.create(course=self.course, title='Module 1', order=1)
        self.lesson = Lesson.objects.create(module=self.module, title='Lesson 1', content='Content')
        self.quiz = Quiz.objects.create(module=self.module, title='Quiz 1')
        self.question = Question.objects.create(quiz=self.quiz, text='Q1', marks=1)
        self.answer1 = Answer.objects.create(question=self.question, text='A1', is_correct=True)
        self.answer2 = Answer.objects.create(question=self.question, text='A2', is_correct=False)

    def test_enrollment(self):
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.assertEqual(enrollment.student.username, 'stud')
        self.assertEqual(enrollment.course.title, 'Test Course')
