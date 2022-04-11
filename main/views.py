from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import login, logout
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from os import remove
from django.urls import reverse

from .models import *


# Funkce vracející HTML soubory, nebo jiné odpovědi na požadavky uživatelů

def index(request):  # Titulní stránka
    if request.user.is_authenticated:  # Kontrola, jestli je přihlášený uživatel
        try:  # Zjišťování, jestli je uživatel student, nebo učitel
            student = Student.objects.get(user=request.user)
            last_courses = student.courses.all().order_by('-date_time_filled')
            if len(last_courses) > 3:
                last_courses = last_courses[0:3]
            units = Course.objects.exclude(id__in=[i.course.id for i in last_courses]).order_by('-filled_count')
            if len(units) > 6:
                units = units[0:6]
            # Vrácení HTML stránky index.html a dalších parametrů k vypsání všech důležitých indormací na stránce
            return render(request, "index.html", {"status": "s", "last_courses": last_courses,
                                                  "units": units})
        except:
            teacher = Teacher.objects.get(user=request.user)
            my_courses = Course.objects.filter(author=teacher)
            if len(my_courses) > 3:
                my_courses = my_courses[0:3]
            units = Course.objects.exclude(id__in=[i.id for i in my_courses]).order_by('-filled_count')
            if len(units) > 6:
                units = units[0:6]
            return render(request, "index.html",
                          {"status": "t", "my_courses": my_courses,
                           "units": units})
    units = Course.objects.all().order_by('-filled_count')
    if len(units) > 6:
        units = units[0:6]
    return render(request, "index.html", {"units": units})


def coureses_list(request):  # Stránka se všemi kurzy (lekcemi)
    try:
        student = Student.objects.get(user=request.user)
        last_courses = student.courses.all().order_by('-date_time_filled')
        return render(request, "units.html", {"user_type": "student", "student": student, "last_courses": last_courses,
                                              "units": Course.objects.filter(pages__isnull=False).exclude(
                                                  id__in=[i.course.id for i in last_courses]).order_by(
                                                  '-filled_count').distinct()})
    except:
        try:
            teacher = Teacher.objects.get(user=request.user)
            last_courses = Course.objects.filter(author=teacher).all().order_by('-date_time_creations')
            return render(request, "units.html",
                          {"user_type": "teacher", "teacher": teacher, "last_courses": last_courses})
        except:
            return render(request, "units.html",
                          {"units": Course.objects.filter(pages__isnull=False).order_by('-filled_count').distinct()})


def search_unit(request):
    text = request.GET['item']
    units = Course.objects.filter(title__icontains=text, pages__isnull=False).distinct()
    return render(request, "search.html", {"units": units, "search": text})


def contact(request):  # Kontakt na autora webu
    return render(request, "contact.html")


def profile(request):  # Profil uživatele
    if not request.user.is_authenticated:
        return redirect('index')
    try:
        student = Student.objects.get(user=request.user)
        note = student.info
    except:
        teacher = Teacher.objects.get(user=request.user)
        note = teacher.info
    return render(request, "profile.html", {"info": note})


def feedback(request):  # Uložení zpětné vazby
    if request.user.is_authenticated:
        f = Feedback(e_mail=request.POST['email'], subject=request.POST['subject'], text=request.POST['message'],
                     user=request.user)  # Vytvoření modelu Feedback
    else:
        f = Feedback(e_mail=request.POST['email'], subject=request.POST['subject'],
                     text=request.POST['message'])  # Vytvoření modelu Feedback
    f.save()  # Uložení modelu
    return HttpResponse()


def edit_course(request):  # Upravit kurz
    if request.user.is_authenticated:  # Kurz může upravovat jen přihlášený uživatel
        try:
            t = Teacher.objects.get(user=request.user)  # Přihlášený uživatel musí být učitel
        except:
            return redirect("courses_list")  # Ostatní uživatele budou přesměrováni na seznam kurzů
        if "item" in request.GET:
            course = Course.objects.get(id=request.GET['item'])  # Který kutz se má upravit
        else:
            return render(request, "edit_unit.html",
                          {"status": "new"})  # Poukd žádný takový neexistuje, uživatel vytvoří nový
        if course.author == t:  # Učitel může upravit jen svůj kurz
            return render(request, "edit_unit.html", {"status": "course", "course": course})
        return render(request, "edit_unit.html", {"status": "not_your"})
    return redirect("courses_list")  # Nepřihlášení uživatelé nemohou měnit


def save_new_course(request):  # Uložit nový kurz
    try:
        author = Teacher.objects.get(user=request.user)
        unit = Course(title=request.POST['title'], descrpition=request.POST['description'], image=request.FILES['file'],
                      author=author)  # Vytvoření objektu kurzu
        unit.save()  # Uložení kurzu
        unit.resize_image()
        # Načtení stránky znovu s editorem kurzu
        base_url = reverse('edit_course')
        query_string = urlencode({'item': unit.id})
        url = '{}?{}'.format(base_url, query_string)
        return redirect(url)
    except:
        return redirect("courses_list")


def change_image(request):  # Změna obrázku kurzu
    if request.user.is_authenticated:
        course = Course.objects.get(id=request.POST['course_id'])  # Kurz, který je upravován
        remove(course.image.path)  # Odstranění souboru obrázku
        course.image = request.FILES['file']  # Vložení nového obrázku
        course.save()  # Uložení změn
        course.resize_image()
        # Načtení stránky znovu s novým obrázkem kurzu
        base_url = reverse('edit_course')
        query_string = urlencode({'item': request.POST['course_id']})
        url = '{}?{}'.format(base_url, query_string)
        return redirect(url)


def save_edited_course(request):  # Uložení upraveného kurzu
    rank = request.POST['rank']  # Pořadí stránek

    course = Course.objects.get(id=request.POST['course_id'])
    course.title = request.POST['title']
    course.descrpition = request.POST['description']

    if rank.split(" ") != ['', '']:  # Kontrola pořadí stránek, do svého kurzu může přidat jen svoje stránky
        my_rank = ""
        for i in rank.split(" "):
            if i and i.isdigit():
                try:
                    page = Page_in_course.objects.get(id=i)
                except:
                    continue
                if page.author == request.user and page in course.pages.all():
                    my_rank += i + " "

        if my_rank.split(" ")[-1] == '':
            my_rank = my_rank[:-1]

        course.page_order = my_rank
    course.save()
    return HttpResponse()


def delete_course(request):  # Vymazat kurz, titulní obrázek kurzu, všechny stránky kurzu a jejich soubory
    if request.user.is_authenticated:
        course = Course.objects.get(id=request.GET['course'])
        remove(course.image.path)
        # Odstranit také kurzy, které jsou vyplněné
        filled_courses = Filled_Course.objects.filter(course=course)
        for i in filled_courses:
            for x in i.pages.all():
                if x.file:
                    remove(x.file.path)
                x.delete()
            i.delete()
        for i in course.pages.all():
            if i.solution:
                remove(i.solution.path)
            for correct in i.correct.all():
                correct.delete()
            i.delete()
        course.delete()
        return redirect('courses_list')


def edit_page(request):  # Upravení stráky v kurzu
    try:
        if Teacher.objects.get(user=request.user):
            if "course" in request.GET:
                course = Course.objects.get(id=request.GET['course'])  # Kurz, ke kterému bude stránka přidána
                if "page" in request.GET:  # Pokud učitel neupravujue existující stránku, může vytvořit novou
                    page = Page_in_course.objects.get(id=request.GET['page'])
                    if course.author == Teacher.objects.get(
                            user=request.user):  # Učitel může upravovat jen svoje stránky
                        try:  # Odkazy na předchozí stránky
                            if str(page.id) == course.page_order.split(" ")[0]:
                                previous = None
                                n = course.page_order.split(str(page.id) + ' ')[1].split(" ")[0]
                                next = course.pages.get(id=n)
                            else:
                                if str(page.id) == course.page_order.split(" ")[-1]:
                                    next = None
                                    p = course.page_order.split(' ' + str(page.id))
                                    p = p[0].split(" ")[-1]
                                    previous = course.pages.get(id=p)
                                else:
                                    n = course.page_order.split(' ' + str(page.id) + ' ')[1].split(" ")[0]
                                    next = course.pages.get(id=n)
                                    p = course.page_order.split(' ' + str(page.id) + ' ')[0].split(" ")[-1]
                                    previous = course.pages.get(id=p)
                            return render(request, "edit_page.html",
                                          {"status": "page", "course": course, "page": page, "next": next,
                                           "previous": previous})
                        except:
                            return render(request, "edit_page.html",
                                          {"status": "page", "course": course, "page": page})
                    else:
                        return render(request, "edit_page.html", {"status": "not_your"})
                else:
                    return render(request, "edit_page.html", {"status": "new", "course": course})
            else:
                return redirect('courses_list')
    except:
        return redirect('courses_list')


def save_new_correct(request):  # Uložit novou správnou možnost jako objekt Correct_Choices
    if request.user.is_authenticated:
        text = request.POST['text']
        correct = Correct_Choices(text=text)
        correct.save()
        return JsonResponse({"status_id": correct.id})  # Do stránky se ukládají id správných možností


def delete_unsaved_correct(request):  # V případě neuložení kurzu, vymazat všechny nepřiřazené správné možnosti
    if request.user.is_authenticated:
        if request.POST['ids']:
            ids = request.POST['ids'].split(",")
            for a in ids:
                Correct_Choices.objects.get(id=a).delete()
        if request.POST['abc_ids']:
            abc_ids = request.POST['abc_ids'].split(",")
            for x in abc_ids:
                ABC_choices.objects.get(id=x).delete()
        return JsonResponse({"status": True})


def delete_unsaved_edit_correct(
        request):  # V případě neuložení editovaného kurzu, vymazat všechny nepřiřazené správné možnosti
    if request.user.is_authenticated:
        page = Page_in_course.objects.get(id=request.POST['page'])
        id_in_page = [i.id for i in page.correct.all()]
        ids = request.POST['ids'][0:-1].split(" ")
        if len(ids) > 1:
            for a in ids:
                if int(a) not in id_in_page:
                    x = Correct_Choices.objects.get(id=a)
                    page.correct.remove(x)
                    x.delete()
        abc_in_page = [i.id for i in page.abc_values.all()]
        abc = request.POST['abc_ids'][0:-1].split(" ")
        if len(abc) > 1:
            for i in abc:
                if int(i) not in abc_in_page:
                    x = ABC_choices.objects.get(id=i)
                    page.abc_values.remove(x)
                    x.delete()
        page.save()
        return JsonResponse({"status": True})


# Vymazat stránku z kurzu, její hodnoty, popřípadně soubor správného řešení a všchny její správné možnosti
def delete_page(request):
    if request.user.is_authenticated:
        page_id = request.POST['page']
        course = Course.objects.get(id=request.POST['course'])
        page = Page_in_course.objects.get(id=page_id)
        course.pages.remove(page)
        if page.solution:
            remove(page.solution.path)
        for i in page.correct.all():
            i.delete()
        for i in page.abc_values.all():
            i.delete()
        for i in Filled_Pages.objects.filter(page=page):
            if i.file:
                remove(i.file.path)
            i.delete()

        page.delete()
        if len(course.page_order.split(" ")) > 1:
            if page_id == course.page_order.split(" ")[0]:
                course.page_order = course.page_order.replace(str(page_id) + ' ', '')
            elif page_id == course.page_order.split(" ")[-1]:
                course.page_order = course.page_order.replace(' ' + str(page_id), '')
            else:
                course.page_order = course.page_order.replace(f' {page_id} ', ' ')
        else:
            course.page_order = ""
        course.save()
        return HttpResponse()


def delete_correct(request):  # Vymazání konkrétní správné odpovědi uživatelem
    if request.user.is_authenticated:
        correct = Correct_Choices.objects.get(id=request.POST['correct_id'])
        correct.delete()
        return HttpResponse()


def save_new_abc(request):  # Uložit novou správnou možnost jako objekt ABC_choices
    if request.user.is_authenticated:
        text = request.POST['text']
        abc = ABC_choices(text=text)
        abc.save()
        return JsonResponse({"status_id": abc.id})  # Do stránky se ukládají id správných možností


def save_new_page(request):  # Uložit novou stránku
    if request.user.is_authenticated:
        type_of_task = request.POST['task_or_question']
        page = Page_in_course(author=request.user, title=request.POST['title'], description=request.POST['description'],
                              task_or_question=type_of_task,
                              task=request.POST['task'], inputs=request.POST['inputs'])

        if 'show_solution' in request.POST:
            page.show_correct = True
        else:
            page.show_correct = False
        page.save()
        correct = request.POST['correct_solutions'][0:-1].split(
            " ")  # Správné možnosti odpovědí se uloží jako id odkazující na jiný objekt
        if correct[0] == '':
            correct.pop(0)
        if correct:
            for i in correct:
                c = Correct_Choices.objects.get(id=int(i))
                page.correct.add(c)
        # Jaký typ úlohy je použit
        if type_of_task == "t":
            example = request.FILES['solution']
            page.solution = example
        elif type_of_task == "q" or type_of_task == "c":
            example = request.POST['solution']
            page.solution_text = example
        if type_of_task == "c":
            abc = request.POST['abc_solutions'][0:-1].split(
                " ")  # Abc možnosti odpovědí se uloží jako id odkazující na jiný objekt
            if abc[0] == '':
                abc.pop(0)
            if abc:
                for i in abc:
                    c = ABC_choices.objects.get(id=i)
                    page.abc_values.add(c)
        page.save()

        course = Course.objects.get(id=request.POST['course'])
        course.pages.add(page)
        if len(course.page_order) > 1:
            course.page_order += " " + str(page.id)
        else:
            course.page_order += str(page.id)
        course.save()

        # Načtení stránky v režimu editování
        base_url = reverse('edit_page')
        query_string = urlencode({'course': course.id, 'page': page.id})
        url = '{}?{}'.format(base_url, query_string)
        return redirect(url)


def replace_solution_file(
        request):  # Nahrazní souboru se správným řešením, popřípadně změna typu úkolu a načtení stránky znovu
    if request.user.is_authenticated:
        course = Course.objects.get(id=request.POST['course_id'])
        page = Page_in_course.objects.get(id=request.POST['page_id'])

        if page in course.pages.all() and page.author == request.user:
            for i in page.abc_values.all():
                page.abc_values.remove(i)
                i.delete()
            if page.task_or_question == "t":
                remove(page.solution.path)

            page.task_or_question = "t"
            page.solution_text = ""
            for i in page.abc_values.all():
                page.abc_values.remove(i)
                i.delete()
            page.solution = request.FILES['file']

            page.save()

            base_url = reverse('edit_page')
            query_string = urlencode({'course': course.id, 'page': request.POST['page_id']})
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)

def delete_abc_choice(request):
    if request.user.is_authenticated:
        page = Page_in_course.objects.get(id=request.POST['page'])
        abc = ABC_choices.objects.get(id=request.POST['id'])
        page.abc_values.remove(abc)
        page.save()
        abc.delete()
        return HttpResponse()

def save_edited_page(request):  # Uložení upravené stránky s novými hodnotami
    type_of_task = request.POST['task_or_question']
    corrects = request.POST['correct'][0:-1].split(" ")

    if corrects[0] == '':
        corrects.pop(0)

    abc_values = request.POST['solutions'][0:-1].split(" ")
    if abc_values[0] == '':
        abc_values.pop(0)

    course = Course.objects.get(id=request.POST['course_id'])
    page = Page_in_course.objects.get(id=request.POST['page_id'])

    if page in course.pages.all() and page.author == request.user:
        page.title = request.POST['title']
        page.description = request.POST['description']
        page.task = request.POST['task']
        page.inputs = request.POST['inputs']
        page.task_or_question = type_of_task
        if request.POST['show_solution'] == "true":
            page.show_correct = True
        else:
            page.show_correct = False
        if "solution_text" in request.POST:
            solution_text = request.POST['solution_text']
            if page.solution:
                remove(page.solution.path)
                page.solution = None
            page.solution_text = solution_text
        if type_of_task == "q":
            page.inputs = ""
            for i in page.abc_values.all():
                page.abc_values.remove(i)
                i.delete()
        elif type_of_task == "c":
            page.inputs = ""
            for i in abc_values:
                if int(i) not in page.abc_values.all():
                    x = ABC_choices.objects.get(id=i)
                    x.save()
                    page.abc_values.add(x)
        if page.correct:
            for i in page.correct.all():
                page.correct.remove(i)
        for i in corrects:
            page.correct.add(Correct_Choices.objects.get(id=i))

        page.save()

        filled = Filled_Pages.objects.filter(page=page)
        for i in filled:
            i.delete()  # Vymazání již vyplněných stránek v vyplněné případě změny
        return HttpResponse()
    else:
        return JsonResponse({"status": "wrong_page"})


def fill_course(request):  # Stránk s vyplněním kurzu
    if not "course" in request.GET:
        return redirect('courses_list')
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            course = Course.objects.get(id=request.GET['course'])
            try:  # Pokud daný kurz ješte nebyl vyplňován, vytvoří se pro vyplnění nový objekt
                filled = student.courses.get(course=course)
            except:
                filled = Filled_Course(course=course)
                filled.save()
                student.courses.add(filled)
                student.save()
                course.filled_count += 1
                course.save()
            return render(request, "fill_course.html", {"course": course, "filled": filled,
                                                        "title": Course.objects.get(id=request.GET['course']).title})
        except:
            base_url = reverse('edit_course')
            query_string = urlencode({'item': request.GET['course']})
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)
    return render(request, "fill_course.html",
                  {"course": None, "title": Course.objects.get(id=request.GET['course']).title})


def fill_page(request):  # Stránka s vyplněním stránky
    if not "course" in request.GET or not "page" in request.GET:
        return redirect("courses_list")
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
        except:
            return redirect('courses_list')
        page_id = request.GET['page']
        try:
            course = Course.objects.get(id=request.GET['course'])
            try:
                filled_course = student.courses.get(course=course)
            except:
                filled_course = Filled_Course(course=course)
                filled_course.save()
                student.courses.add(filled_course)
                student.save()
                course.filled_count += 1
                course.save()
            page = Page_in_course.objects.get(id=page_id)
            try:
                filled_page = filled_course.pages.get(page=page)
            except:
                filled_page = Filled_Pages(page=page)
                filled_page.save()
                filled_course.pages.add(filled_page)
                filled_course.save()


            if len(course.page_order.split(" ")) > 1:  # Odkaz na předchozí a další stránku, pokud existují
                if page_id == course.page_order.split(" ")[0]:
                    previous = None
                    n = course.page_order.split(page_id + ' ')[1].split(" ")[0]
                    next = course.pages.get(id=n)
                    if not next.correct.all():
                        next = None

                else:
                    if page_id == course.page_order.split(" ")[-1]:
                        next = None
                        p = course.page_order.split(' ' + page_id)
                        p = p[0].split(" ")[-1]
                        previous = course.pages.get(id=p)
                        if not previous.correct.all() and ((previous.task_or_question == "c" and previous.abc_values.all()) or previous.task_or_question != "c"):
                            previous = None

                    else:
                        n = course.page_order.split(' ' + page_id + ' ')[1].split(" ")[0]
                        next = course.pages.get(id=n)
                        if not (next.correct.all() and ((next.task_or_question == "c" and next.abc_values.all()) or next.task_or_question != "c")):
                            next = None
                        p = course.page_order.split(' ' + page_id + ' ')[0].split(" ")[-1]
                        previous = course.pages.get(id=p)
                        if not (previous.correct.all() and ((previous.task_or_question == "c" and previous.abc_values.all()) or previous.task_or_question != "c")):
                            previous = None

                return render(request, "fill_page.html",
                              {"course": course, "page": page, "filled_course": filled_course,
                               "filled_page": filled_page,
                               "next": next, "previous": previous})
            else:
                return render(request, "fill_page.html",
                              {"course": course, "page": page, "filled_course": filled_course,
                               "filled_page": filled_page})
        except:
            return redirect('courses_list')
    return redirect('courses_list')


def check_page(request):  # Kontrola správnosti vyplněné stránky
    solution = request.POST['solution']
    course = Course.objects.get(id=request.POST['course'])
    page = course.pages.get(id=request.POST['page'])

    student = Student.objects.get(user=request.user)
    filled_course = student.courses.get(course=course)
    filled_page = filled_course.pages.get(page=page)
    # Uložení odpovědí
    if page.task_or_question == "t":
        if filled_page.file:
            remove(filled_page.file.path)
        filled_page.file.save(f'{filled_page.id}.py', ContentFile(solution.encode('utf-8')))
        filled_page.save()
    else:
        filled_page.solution_text = solution
        filled_page.save()
    return JsonResponse({"error_code": filled_page.is_right()})  # Návrat chyby


def show_success(request):  # Zobrazit úspěšnost řešení úkolů v kurzu
    course = Course.objects.get(id=request.GET['course'])
    try:  # Sledování úspšnosti je k dospozici jen pro učitele daného kurzu
        author = Teacher.objects.get(user=request.user)
    except:
        return redirect('courses_list')
    if course.author == author:
        try:
            filled_courses = Filled_Course.objects.filter(course=course)
        except Filled_Course.DoesNotExist:
            filled_courses = None
        return render(request, "success.html", {"course": course, "filled_courses": filled_courses})
    return render(request, "success.html")


def delete_filled_course(request):  # Vymazání vyplněného kurzu se všemi stránkami i sobory
    if "student" in request.POST:  # Vyplněný kurz maže učitel
        student = Student.objects.get(id=request.POST["student"])
        course = Filled_Course.objects.get(id=request.POST['course'])
        if course in student.courses.all():
            for p in course.pages.all():
                if p.file:
                    remove(p.file.path)
                p.delete()
            course.delete()
            return HttpResponse()
    else:  # Vyplněný kurz maže student
        student = Student.objects.get(user=request.user)
        course = Filled_Course.objects.get(id=request.GET['course'])
        if course in student.courses.all():
            for p in course.pages.all():
                if p.file:
                    remove(p.file.path)
                p.delete()
            course.delete()
            return redirect('courses_list')


def show_answers_by_pages(request):
    if request.user.is_authenticated:
        page = Page_in_course.objects.get(id=request.GET['page'])
        if page.author == request.user:
            filled_pages = Filled_Pages.objects.filter(page=page)
            chart_data = {}
            for i in filled_pages:
                if i.solution_text:
                    if i.page.task_or_question == "c":
                        if i.print_choice().lower() in chart_data:
                            chart_data[i.print_choice().lower()] += 1
                        else:
                            chart_data[i.print_choice().lower()] = 1
                    else:
                        if i.solution_text.lower() in chart_data:
                            chart_data[i.solution_text.lower()] += 1
                        else:
                            chart_data[i.solution_text.lower()] = 1
                elif i.file:
                    if i.print_file() in chart_data:
                        chart_data[i.print_file()] += 1
                    else:
                        chart_data[i.print_file()] = 1
            return render(request, "show_answers_by_page.html",
                          {"page": page, "filled_pages": filled_pages, "chart_data": chart_data})
        return redirect('courses_list')
    return redirect('index')


def register(request):  # Registrace uživatele
    mail = request.POST['email']
    for n in User.objects.all():
        if mail == n.email:
            return JsonResponse({"status": "email"})

    User.objects.create_user(username=mail, email=mail,
                             password=str(request.POST['password']),
                             first_name=request.POST['name'],
                             last_name=request.POST['surname'])
    typ = request.POST['type']
    user = User.objects.get(email=mail)
    if typ == "student":  # Vytvoření profilu pro studenta nebo pro učitele
        student = Student(user=user)
        student.save()
    elif typ == "teacher":
        teacher = Teacher(user=user)
        teacher.save()
    '''send_mail('Připojil se nový uživatel!',
              f'Zaregistroval se uživatel {username} (email: {str(request.POST["email"])})',
              settings.EMAIL_HOST_USER,
              [settings.EMAIL_HOST_USER],
              fail_silently=False, )'''  # Administrátorovi by mohl přijít email, že se zaregistroval nový uživatel
    return JsonResponse({"status": "ok"})


def authenticate_by_email(email, password):  # Přilášení probíhá pomocí emailu a hesla
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        return None
    else:
        if user.check_password(password):
            return user
    return None


def sign_in(request):  # Přihlášení uživatele
    user = authenticate_by_email(email=request.POST['email'], password=request.POST['password'])
    if user is not None:
        login(request, user)
        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "error"})


def log_out(request):  # Odhlášení uživatele
    if request.user.is_authenticated:
        logout(request)
        return redirect('index')
    else:
        return redirect('index')


def change_username(request):  # Změna jména, přijmení, nebo emailu uživatele
    user = request.user
    email = request.POST['email']
    for n in User.objects.all():
        if email == n.email and email != user.email:
            return JsonResponse({"status": "email"})
    user.first_name = request.POST['name']
    user.last_name = request.POST['surname']
    user.email = email
    user.save()
    return HttpResponse()


def change_password(request):  # Změna hesla uživatele
    user = request.user
    if user.check_password(request.POST['old_password']):  # Kontrola starého hesla
        user.set_password(request.POST['password'])  # Nastavení nového hesla
        user.save()  # Uložení objektu
        return HttpResponse()
    return JsonResponse({"status": "not_same"})


def send_password_recover_send_email(email,
                                     user):  # Vytvoření objektu se žádostí pro kontrolu a odeslání emailu s odkazem na obnovení, žádost o změnu hesla bude uložena do Recovery_Password
    try:  # Pokud již uživatel chtěl měnit heslo dříve, v databázi bude jen ta novější žádost
        r = Recovery_Password.objects.get(user=user)
        r.delete()
    except:
        pass
    recovery = Recovery_Password(user=user)
    recovery.secret_key_1 = recovery.set_secret_key()
    recovery.secret_key_2 = recovery.set_secret_key()
    recovery.save()
    link = f'https://pythoncvicebnice.eu.pythonanywhere.com/recover_forgotten_password?secret_key_1={recovery.secret_key_1}&secret_key_2={recovery.secret_key_2}&email={email}'  # Odkaz na stránku.
    send_mail('Obnovení zapomenutého hesla',
              f'Svoje heslo můžete obnovit na adrese: {link}\nPlatnost odkazu je 30 dní.',
              settings.EMAIL_HOST_USER,
              [email],
              fail_silently=False, )  # Odeslání emailu


def send_password_recover(request):  # Obnovení hesla
    email = request.POST['email']
    try:
        user = User.objects.get(email=email)
        send_password_recover_send_email(email, user)
        return JsonResponse({"status": "sent"})
    except:
        return JsonResponse({"status": "email_not_found"})


def recover_forgotten_password(request):  # Ověření obnovení hesla a změna hesla
    try:
        secret_key_1 = request.GET['secret_key_1']
        secret_key_2 = request.GET['secret_key_2']
        email = request.GET['email']
        user = User.objects.get(email=email)
        recovery = Recovery_Password.objects.get(user=user)
        if recovery.is_valid(secret_key_1, secret_key_2):
            return render(request, "recover_forgotten_password.html",
                          {"status": "recovery", "user": user, "secret_key_1": secret_key_1,
                           "secret_key_2": secret_key_2})
        else:
            return render(request, "recover_forgotten_password.html", {"status": "wrong_key"})
    except:
        return render(request, "recover_forgotten_password.html", {"status": "key_error"})


def recover_password(request):
    try:
        secret_key_1 = request.POST['secret_key_1']
        secret_key_2 = request.POST['secret_key_2']
        email = request.POST['email']
        user = User.objects.get(email=email)
        recovery = Recovery_Password.objects.get(user=user)
        if recovery.is_valid(secret_key_1, secret_key_2):
            password = request.POST['password']
            user.set_password(password)
            user.save()
            recovery.delete()
            return HttpResponse()
    except:
        return JsonResponse({"status": "key_error"})


def save_user_note(request):  # Uložení informací u uživatelovi
    try:
        student = Student.objects.get(user=request.user)
        student.info = request.POST['info']
        student.save()
    except:
        teacher = Teacher.objects.get(user=request.user)
        teacher.info = request.POST['info']
        teacher.save()
    return HttpResponse()


def remove_account(request):  # Odstranění účtu a všech dat
    try:  # Odstranění účtu studenta
        student = Student.objects.get(user=request.user)
        courses = student.courses.all()
        for c in courses.all():
            for p in c.pages.all():
                if p.file:
                    remove(p.file.path)
                p.delete()
            c.delete()
    except:
        try:  # Odstranění účtu učitele
            teacher = Teacher.objects.get(user=request.user)
            courses = Course.objects.filter(author=teacher)
            for c in courses.all():
                remove(c.image.path)
                for p in c.pages.all():
                    for fp in Filled_Pages.objects.filter(page=p):
                        remove(fp.file.path)
                        fp.delete()
                    if p.solution:
                        remove(p.solution.path)
                    for correct in p.correct.all():
                        correct.delete()
                    for i in p.abc_values.all():
                        i.delete()
                    p.delete()
                for fc in Filled_Course.objects.filter(course=c):
                    fc.delete()
                c.delete()
        except:
            pass
    request.user.delete()
    return redirect('index')


def show_feedbacks(request):  # Zobrazení všech zpětných vazeb
    if request.user.is_superuser:
        return render(request, "feedbacks.html", {"feedbacks": Feedback.objects.all()})
    return redirect('index')


def delete_feedback(request):  # Odstranění zpětné vazby
    if request.user.is_superuser:
        feedback_item = Feedback.objects.get(id=request.POST['feedback_id'])
        feedback_item.delete()
        return HttpResponse()


def create_report(request):
    try:
        student = Student.objects.get(user=request.user)
        course = Course.objects.get(id=request.POST['course'])
        report = Report(course=course, reason=request.POST['reason'], student=student)
        report.save()
        return JsonResponse({"status": True})
    except:
        return JsonResponse({"status": False})


def reports(request):
    if request.user.is_superuser:
        return render(request, "reports.html", {"reports": reversed(Report.objects.all())})
    return redirect('index')


# Chyby stránky
def handler404(request, *args, **argv):  # Stránka nenalezena
    return render(request, "error.html", {'code': 404})


def handler500(request, *args, **argv):  # Jiná chyba
    return render(request, "error.html", {'code': 500})
