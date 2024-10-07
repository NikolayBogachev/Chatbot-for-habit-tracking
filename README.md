![v](https://img.shields.io/badge/build-3.10-brightgreen?style=plastic&logo=Python&label=Python&color=orange&cacheSeconds=10000)
![](https://img.shields.io/badge/build-0.111.1-brightgreen?style=plastic&logo=FastAPI&label=FastAPI&color=orange&cacheSeconds=10000)
![v](https://img.shields.io/badge/build-%E2%80%8E3.12.0-brightgreen?style=plastic&logo=Aiogram&label=Aiogram&color=orange&cacheSeconds=1000000)
![v](https://img.shields.io/badge/build-2.0.31-brightgreen?style=plastic&logo=Sqlalchemy&label=Sqlalchemy&color=orange)
![v](https://img.shields.io/badge/build-17-brightgreen?style=plastic&logo=Postgresql&label=Postgresql&color=orange)
![v](https://img.shields.io/badge/build-%E2%80%8E2.29.2-brightgreen?style=plastic&logo=Docker&label=Docker&color=orange&cacheSeconds=1000000)
![v](https://img.shields.io/badge/build-%E2%80%8E5.3.5-brightgreen?style=plastic&logo=Celery&label=Celery&color=orange&cacheSeconds=1000000)
# *Чат-бот для трекинга привычек*


## Описание

*Этот проект представляет собой сервис для управления привычками через Telegram-бота. Сервис позволяет пользователям добавлять,
редактировать, удалять привычки, отмечать их выполнение, получать напоминания и переносить невыполненные задачи на следующий день:*

## Основные функции
### Telegram-бот (Frontend):
- Добавление, удаление и редактирование привычек: Пользователи могут управлять своими привычками через удобный интерфейс Telegram-бота.
- Отметка выполнения привычек: Возможность фиксировать, выполнена привычка или нет.
- Напоминания: Регулярные напоминания пользователям о необходимости выполнения привычек в установленное время.
### Backend (FastAPI):
- Аутентификация и авторизация: Телеграм-бот интегрирован с системой аутентификации на FastAPI. Пользователи авторизуются с использованием токенов.
- CRUD для привычек: Сервис реализует полный набор операций по созданию, редактированию, удалению и просмотр привычек.
- Перенос привычек: Невыполненные привычки дублируются на следующий день до тех пор, пока не будут выполнены указанное количество дней (например, 21 день).
### Сервис уведомлений:
- Фоновый сервис, который уведомляет пользователей в заданное время о необходимости выполнения привычек.


___



## Автор

Этот проект был разработан **Богачевым Николаем Константиновичем** [Email me](mailto:Bogachev.pro@gmail.com)
.
