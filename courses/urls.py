from django.urls import path
from . import views

urlpatterns = [
    # Catégories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Cours
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<slug:slug>/enroll/', views.CourseEnrollView.as_view(), name='course_enroll'),
    path('<slug:slug>/reviews/', views.CourseReviewListView.as_view(), name='course_reviews'),
    
    # Inscriptions
    path('enrollments/', views.StudentEnrollmentsView.as_view(), name='student_enrollments'),
    
    # Cours des formateurs
    path('instructor/courses/', views.InstructorCoursesView.as_view(), name='instructor_courses'),
    
    # Leçons
    path('lessons/<int:lesson_id>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('lessons/<int:lesson_id>/progress/', views.update_lesson_progress, name='lesson_progress'),
    
    # Quiz
    path('quiz/<int:quiz_id>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('quiz/<int:quiz_id>/attempt/', views.submit_quiz_attempt, name='quiz_attempt'),
    path('quiz/attempts/', views.StudentQuizAttemptsView.as_view(), name='student_quiz_attempts'),
]
