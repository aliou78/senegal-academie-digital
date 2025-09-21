import django_filters
from .models import Course


class CourseFilter(django_filters.FilterSet):
    """
    Filtres pour les cours
    """
    category = django_filters.CharFilter(field_name='category__slug')
    level = django_filters.ChoiceFilter(choices=Course.LEVEL_CHOICES)
    language = django_filters.ChoiceFilter(choices=Course.LANGUAGE_CHOICES)
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    duration_min = django_filters.NumberFilter(field_name='duration_hours', lookup_expr='gte')
    duration_max = django_filters.NumberFilter(field_name='duration_hours', lookup_expr='lte')
    is_featured = django_filters.BooleanFilter()
    is_certified = django_filters.BooleanFilter()
    instructor = django_filters.CharFilter(field_name='instructor__username')
    
    class Meta:
        model = Course
        fields = ['category', 'level', 'language', 'price_min', 'price_max', 
                 'duration_min', 'duration_max', 'is_featured', 'is_certified', 'instructor']
