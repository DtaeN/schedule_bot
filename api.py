import requests
import datetime
import re

from settings import (rasp_group_list,
                      schedule_group,
                      rasp_teacher_list,
                      schedule_teacher)


class Lesson:
    def __init__(
        self,
        _id: int,
        name: str,
        aud: str,
        teacher: str,
        date: datetime,
        start: str,
        end: str,
        type_week: int,
        group: str
    ):
        self.id = id
        self.name = name
        self.aud = aud
        self.type = type
        self.teacher = teacher
        self.date = date
        self.start = start
        self.end = end
        self.type_week = type_week
        self.group = group


class Group:
    def __init__(self, _id, name, course):
        self.id = _id
        self.name = name
        self.course = course
        self.lessons = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
        }

    def add_schedule(self, date, lessons: Lesson):
        self.lessons[date.strftime("%A")].append(lessons)

    def lessons_clear(self):
        self.lessons = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
        }


class Teacher:
    def __init__(self, _id, name):
        self.id = _id
        self.name = name
        self.lessons = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
        }

    def add_schedule(self, date, lessons: Lesson):
        self.lessons[date.strftime("%A")].append(lessons)

    def lessons_clear(self):
        self.lessons = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
        }


class Dispatcher_DSTU:
    _groups = []
    _teachers = []

    def __init__(self) -> None:
        self._get_groups()
        self._get_teacher()

# -----------------------------------------
# group
    def find_groups_by_course(self, course):
        select_groups = []
        for group in self._groups:
            if group.course == int(course):
                select_groups.append(group)
        return select_groups

    def find_group_schedule_by_day(self, group_id: int, _weekday: str, weekday: str, type_week: int):
        group = self.find_group(group_id)
        self._get_schedule_group(group)
        return self._schedule_to_str_group(group, _weekday, weekday, type_week)

    def find_group(self, group_id: int):
        for group in self._groups:
            if group.id == group_id:
                return group

# -----------------------------------------
# teacher
    def find_teachers_all(self):
        return self._teachers

    def search_teacher(self, teacher_name):
        teachers = self.find_teachers_all()
        res = {}
        for teacher in teachers:
            if re.search(teacher_name, teacher.name, re.IGNORECASE):
                res[teacher.id] = teacher.name
        return res

    def find_teacher_schedule_by_day(self, teacher_id: int, _weekday: str, weekday: str, type_week: int):
        teacher = self.find_teacher(teacher_id)
        self._get_schedule_teacher(teacher)
        return self._schedule_to_str_teacher(teacher, _weekday, weekday, type_week)

    def find_teacher_by_id(self, teacher_id: int):
        select_teachers = []
        for teacher in self._teachers:
            if teacher.id == teacher_id:
                select_teachers.append(teacher)
        return select_teachers

    def find_teacher(self, teacher_id):
        for teacher in self._teachers:
            if teacher.id == teacher_id:
                return teacher
# -----------------------------------------

    def _get_groups(self):
        params = {"year": "2023-2024"}
        response = requests.get(rasp_group_list, params=params)

        if response.status_code == 200:
            self._collect_groups(response.json())
            return [group.name for group in self._groups]
        else:
            print("Произошла ошибка при выполнении запроса.")

    def _get_teacher(self):
        params = {"year": "2023-2024"}
        response = requests.get(rasp_teacher_list, params=params)

        if response.status_code == 200:
            self._collect_teachers(response.json())
            return [teacher.name for teacher in self._teachers]
        else:
            print("Произошла ошибка при выполнении запроса.")

    def _get_schedule_group(self, group: Group):
        params = {"idGroup": group.id, "sdate": datetime.datetime.now()}
        response = requests.get(schedule_group, params=params)

        if response.status_code == 200:
            return self._collect_schedule_group(response, group)
        else:
            print("Произошла ошибка при выполнении запроса edu donstu.")

    def _get_schedule_teacher(self, teacher: Teacher):
        params = {"idTeacher": teacher.id, "sdate": datetime.datetime.now()}
        response = requests.get(schedule_teacher, params=params)

        if response.status_code == 200:
            return self._collect_schedule_teacher(response, teacher)
        else:
            print("Произошла ошибка при выполнении запроса edu donstu.")

    def _collect_groups(self, raspGroupList: dict):
        for item in raspGroupList["data"]:
            if item["facul"] == "АТК":
                self._groups.append(Group(item["id"], item["name"], item["kurs"]))

    def _collect_teachers(self, raspGroupList: dict):
        for item in raspGroupList["data"]:
            self._teachers.append(Teacher(item["id"], item["name"]))

    def _collect_schedule_group(self, _schedule_group, group: Group):
        group.lessons_clear()
        for discipline in _schedule_group.json()["data"]["rasp"]:
            group.add_schedule(
                datetime.datetime.strptime(discipline["дата"][0:len(discipline['дата'])-6], "%Y-%m-%dT%H:%M:%S"),
                Lesson(
                    discipline["код"],
                    discipline["дисциплина"],
                    discipline["аудитория"],
                    discipline["преподаватель"],
                    discipline["дата"],
                    discipline["начало"],
                    discipline["конец"],
                    discipline["типНедели"],
                    discipline["группа"]
                ),
            )
        return self._schedule_to_str_group(group, "all", "", 0)

    def _collect_schedule_teacher(self, _schedule_teacher, teacher: Teacher):
        teacher.lessons_clear()
        for discipline in _schedule_teacher.json()["data"]["rasp"]:
            teacher.add_schedule(
                datetime.datetime.strptime(discipline["дата"][0:len(discipline['дата'])-6], "%Y-%m-%dT%H:%M:%S"),
                Lesson(
                    discipline["код"],
                    discipline["дисциплина"],
                    discipline["аудитория"],
                    discipline["преподаватель"],
                    discipline["дата"],
                    discipline["начало"],
                    discipline["конец"],
                    discipline["типНедели"],
                    discipline["группа"]
                ),
            )
        return self._schedule_to_str_teacher(teacher, "all", "", 0)

    def _schedule_to_str_group(self, group: Group, _weekday, weekday, type_week):
        # Получение данных из переменной schedule

        stroke = (f"День: {_weekday if _weekday == 'all' else weekday} \n"
                  f"Неделя: {'Верхняя' if type_week == 1 else 'Нижняя'} \n\n")
        for day, lessons in group.lessons.items():
            if lessons is not None:
                if _weekday == day or _weekday == 'all':
                    for lesson in lessons:
                        if lesson.type_week == type_week or type_week == 0:
                            stroke += (f"{'_' * 40}\n"
                                       f"{lesson.start} - {lesson.end} | {lesson.name}\n"
                                       f"{lesson.teacher}       Аудитория:{lesson.aud}\n")
        return stroke

    def _schedule_to_str_teacher(self, teacher: Teacher, _weekday, weekday, type_week):
        # Получение данных из переменной schedule

        stroke = (f"День: {_weekday if _weekday == 'all' else weekday} \n"
                  f"Неделя: {'Верхняя' if type_week == 1 else 'Нижняя'} \n\n")
        for day, lessons in teacher.lessons.items():
            if lessons is not None:
                if _weekday == day or _weekday == 'all':
                    for lesson in lessons:
                        if lesson.type_week == type_week or type_week == 0:
                            stroke += (f"{'_' * 40}\n"
                                       f"{lesson.start} - {lesson.end} | {lesson.name}\n"
                                       f"Аудитория:{lesson.aud}       Группа:{lesson.group}\n")
        return stroke