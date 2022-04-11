from django.urls import path
from django.views.decorators.cache import never_cache

from . import views

urlpatterns = [
    # "odkazy" na funkce vracející HTML soubory
    path('', views.index, name='index'),
    path('profile', views.profile, name='profile'),
    path('contact', views.contact, name='contact'),
    path('courses_list', views.coureses_list, name='courses_list'),
    path('show_feedbacks', views.show_feedbacks, name='show_feedbacks'),
    path('search_unit', views.search_unit, name='search_unit'),
    # funkce týkající se uživatele
    path('log_out', views.log_out, name="log_out"),
    path('register', views.register, name='register'),
    path('sign_in', views.sign_in, name='sign_in'),
    path('change_username', views.change_username, name='change_username'),
    path('change_password', views.change_password, name='change_password'),
    path('remove_account', views.remove_account, name='remove_account'),
    path('recover_forgotten_password', views.recover_forgotten_password, name='recover_forgotten_password'),
    path('recover_password', views.recover_password, name='recover_password'),
    path('send_password_recover', views.send_password_recover, name='send_password_recover'),
    path('save_user_note', views.save_user_note, name='save_user_note'),
    # Funkce týkající se lekcí, stránek
    path('feedback', views.feedback, name="feedback"),
    path('edit_course', never_cache(views.edit_course), name="edit_course"),
    path('edit_page', views.edit_page, name="edit_page"),
    path('save_new_course', views.save_new_course, name="save_new_couse"),
    path('save_edited_course', views.save_edited_course, name="save_edited_couse"),
    path('change_image', views.change_image, name="change_image"),
    path('saved_mew_page', views.save_new_page, name="save_new_page"),
    path('saved_edited_page', views.save_edited_page, name="save_edited_page"),
    path('save_new_correct', views.save_new_correct, name="save_new_correct"),
    path('delete_unsaved_correct', views.delete_unsaved_correct, name="delete_unsaved_correct"),
    path('delete_unsaved_edit_correct', views.delete_unsaved_edit_correct, name="delete_unsaved_edit_correct"),
    path('delete_page', views.delete_page, name="delete_page"),
    path('replace_solution_file', views.replace_solution_file, name="replace_solution_file"),
    path('delete_correct', views.delete_correct, name="delete_correct"),
    path('delete_course', views.delete_course, name="delete_course"),
    path('delete_filled_course', views.delete_filled_course, name="delete_filled_course"),
    path('save_new_abc', views.save_new_abc, name="save_new_abc"),
    path('delete_abc_choice', views.delete_abc_choice, name="delete_abc_choice"),

    path('fill_course', views.fill_course, name="fill_course"),
    path('fill_page', views.fill_page, name="fill_page"),
    path('check_page', views.check_page, name="check_page"),

    path('show_success', views.show_success, name="show_success"),
    path('show_answers_by_pages', views.show_answers_by_pages, name="show_answers_by_pages"),
    path('delete_feedback', views.delete_feedback, name="delete_feedback"),

    path('reports', views.reports, name="reports"),
    path('create_report', views.create_report, name="create_report"),
    ]