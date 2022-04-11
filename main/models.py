from django.contrib.auth.models import User
from django.db import models
from datetime import datetime, timedelta
import subprocess
from random import randint, choice
from PIL import Image
from django.core.files import File

# Možnosti zpětné vazby
feedback_subject_choices = (
    ("Návrh na vylepšení", "Návrh na vylepšení"),
    ("Problém", "Problém"),
    ("Něco jiného", "Něco jiného")
)
# Možnosti typu úkolu
task_or_question_choices = (
    ("t", "task"), # Úkol
    ("q", "question"), # Otázka
    ("c", "abc") # Výběr správné možnosti
)


# Modely ukládané do databáze
class Feedback(models.Model):  # Zpětná vazba
    e_mail = models.EmailField()
    subject = models.CharField(max_length=18, choices=feedback_subject_choices, default="Návrh na vylepšení")
    text = models.TextField()
    date_time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


class Teacher(models.Model):  # Učitel
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    info = models.TextField(blank=True)


class Correct_Choices(models.Model):  # Správná možnost odpovědi v úkolu
    text = models.TextField()


class ABC_choices(models.Model):  # Možnost ABC úkolu
    text = models.TextField()


class Page_in_course(models.Model):  # Stránka v kurzu
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    date_time_creations = models.DateTimeField(auto_now=True)

    description = models.TextField(blank=True)
    task = models.TextField()  # Zadání
    solution = models.FileField(upload_to='media/solutions/', blank=True)
    solution_text = models.TextField(blank=True)
    correct = models.ManyToManyField(Correct_Choices)
    show_correct = models.BooleanField(default=True)

    inputs = models.TextField(blank=True)

    task_or_question = models.CharField(max_length=1, choices=task_or_question_choices, default="t")
    abc_values = models.ManyToManyField(ABC_choices, blank=True)

    def print_solution(self):
        file = open(self.solution.path, "r")
        return file.read()




class Course(models.Model):  # Kurz (lekce)
    title = models.TextField()
    descrpition = models.TextField(blank=True)
    date_time_creations = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='media/images/')
    author = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    pages = models.ManyToManyField(Page_in_course, blank=True)
    page_order = models.TextField()

    filled_count = models.IntegerField(default=0)

    def resize_image(self):# Změna velikosti obrázku
        if self.image.width > 500 and self.image.height > 414:
            with Image.open(self.image.path) as img:
                i = img.resize((500, 414))
                i.save(self.image.path)


    def splitted_orders_list(self):  # Stránky v kurzu ve správném poradí
        if self.page_order:
            order = []
            for i in self.page_order.split(" "):
                p = Page_in_course.objects.get(id=i)
                if p.correct.all() and ((p.task_or_question == "c" and p.abc_values.all()) or p.task_or_question != "c"):
                    order.append(p)
            return order
        return None

    def splitted_orders_list_with_no_correct(self):  # Stránky v kurzu ve správném poradí
        if self.page_order:
            order = []
            for i in self.page_order.split(" "):
                p = Page_in_course.objects.get(id=i)
                order.append(p)
            return order
        return None

    def description_print(self):  # V případě dlouhého popisku napsat jen část
        if len(self.descrpition) > 75:
            return self.descrpition[0:75] + " ..."
        return self.descrpition



class Filled_Pages(models.Model):  # Vyplněná stránka studentem
    date_time_filled = models.DateTimeField(auto_now=True)
    page = models.ForeignKey(Page_in_course, on_delete=models.CASCADE)

    file = models.FileField(upload_to=f'media/py_files/', blank=True)
    solution_text = models.TextField(blank=True, default="")

    is_correct = models.BooleanField(default=False)

    def print_choice(self):
        if self.page.task_or_question == "c":
            return self.page.abc_values.get(id=self.solution_text).text

    def print_file(self):
        if not self.file:
            return None
        text = open(self.file.path, "r", encoding="utf-8")
        return text.read()

    def check_task(self):  # Zkontolovat, pokud typ objektu je úkol
        p1 = subprocess.Popen(['python', self.file.path], cwd="temporary_files/",
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False,
                              encoding="utf-8")
        try:
            stdout, error = p1.communicate(input="\n".join(self.page.inputs.splitlines()), timeout=5)

            if error != "":
                return error  # vrácení chyby

            stdout = stdout[0:-1].lower()

            for i in self.page.correct.all():
                text = i.text.lower()
                text = "\n".join(text.splitlines())

                if stdout == text:
                    self.is_correct = True
                    self.save()
                    return True
            self.is_correct = False
            self.save()
            return False

        except:
            p1.kill()
            self.is_correct = False
            self.save()
            return "Infinite loop"

    def check_question(self):  # Zkontrolovat, pokud typ objektu je otázka
        if self.solution_text.lower() in [i.text.lower() for i in self.page.correct.all()]:
            self.is_correct = True
            self.save()
            return True
        self.is_correct = False
        self.save()
        return False

    def check_abc(self):  # Zkontrolovat, pokud typ objektu je výběr abc
        if ABC_choices.objects.get(id=self.solution_text).text.lower() in [i.text.lower() for i in self.page.correct.all()]:
            self.is_correct = True
            self.save()
            return True
        self.is_correct = False
        self.save()
        return False

    def is_right(self):  # Kontrola správnosti
        try:
            if self.page.task_or_question == "t":
                return self.check_task()
            elif self.page.task_or_question == "q":
                return self.check_question()
            elif self.page.task_or_question == "c":
                return self.check_abc()
            else:
                raise Exception
        except:
            return "Not filled"


class Filled_Course(models.Model):  # Vyplněný kurz
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_time_filled = models.DateTimeField(auto_now=True)

    pages = models.ManyToManyField(Filled_Pages)

    def filled_pages_in_percents(self):
        try:
            return round(len(self.pages.filter(is_correct=True)) / len(self.course.pages.all().exclude(correct__isnull=True)) * 100)
        except:
            return 0


class Student(models.Model):  # Objekt studenta
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    info = models.TextField(blank=True)

    courses = models.ManyToManyField(Filled_Course)

    def name(self):
        return f'{self.user.first_name} {self.user.last_name}'


class Recovery_Password(models.Model):  # Žádosti o obnovení hesla
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_time_creations = models.DateTimeField(auto_now=True)
    valid_thru = models.DateTimeField(default=datetime.now() + timedelta(days=30))
    secret_key_1 = models.TextField()
    secret_key_2 = models.TextField()

    def is_valid(self, secret_key_1, secret_key_2):
        if self.valid_thru > datetime.now() and (
                self.secret_key_1 == secret_key_1 and self.secret_key_2 == secret_key_2):
            return True
        return False

    def set_secret_key(self):
        chars = [i for i in range(65, 91)] + [i for i in range(97, 123)]
        key = ""
        for i in range(randint(5, 10)):
            key += chr(choice(chars))
        return key


class Report(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    reason = models.TextField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date_time_creations = models.DateTimeField(auto_now=True)
