from django.contrib import admin
from .models import Feedback, Teacher, Correct_Choices, Page_in_course, Course, Filled_Pages, Filled_Course, Student, ABC_choices, Recovery_Password, Report

admin.site.site_header = 'Správce stránky pythoncvicebnice.eu.pythonanywhere.com'

# Přidání modelů na stránku admin
admin.site.register(Feedback)

admin.site.register(Teacher)
admin.site.register(Student)

admin.site.register(Course)
admin.site.register(Page_in_course)
admin.site.register(Correct_Choices)
admin.site.register(ABC_choices)

admin.site.register(Filled_Course)
admin.site.register(Filled_Pages)

admin.site.register(Recovery_Password)
admin.site.register(Report)