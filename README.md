# Проект продуктовый помощник Foodgram
![example workflow](https://github.com/KhitK0101/foodgram-project-react/workflows/foodgram_workflow/badge.svg)  
  
[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)

## Описание проекта Foodgram
Дипломный проект — сайт Foodgram, «Продуктовый помощник». Онлайн-сервис и API для него. На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Установка и запуск проекта на локальном компьютере :computer:
Клонируйте репозиторий на локальную машину.
```
git clone <адрес репозитария>
```
Установите виртуальное окружение.
```
python -m venv venv
```
Активируйте виртуальное окружение.
```
source venv\Scripts\activate
```
Перейти в директорию /infra и создать файл .env:
```
cd infra
touch .env
```
Заполните файл содержанием из файла в примере [infra/.env.example](https://github.com/KhitK0101/foodgram-project-react/blob/master/infra/.env.example):
```
DB_ENGINE='django.db.backends.postgresql' # указываем, что работаем с postgresql
DB_NAME='postgres' # имя базы данных
POSTGRES_USER='postgres' # логин для подключения к базе данных
POSTGRES_PASSWORD='postgres' # пароль для подключения к БД (установите свой)
DB_HOST='127.0.0.1' # адрес и доменное имя (контейнера)
DB_PORT='5432' # порт для подключения к БД
SECRET_KEY = <секретный ключ>
```
Перейдите в каталог `backend`. Установите зависимости.
```
cd ../backend
pip install -r requirements.txt
```
Создайте миграции: 
```
docker-compose exec backend python manage.py migrate --noinput
```
Соберите статику проекта командой:
```
sudo docker-compose exec web python manage.py collectstatic --no-input
```
Создайте суперпользователя Django:
```
sudo docker-compose exec web python manage.py createsuperuser
```
Загрузите тестовые данные в базу данных командой: 
```
sudo docker -compose exec backend python manage.py loaddata dump.json
```

## Запуск проекта на удаленном сервере :milky_way:
Запуск проекта на удаленном сервере выполняется средствами контейнеров Docker. :whale:
Перейдите на удаленный сервер.
Установите Docker и Docker-compose.
Создайте или скопируйте на сервер конфигурационные файлы `docker-compose.yml` и `nginx.conf` из каталога `infra/`
Запустите docker compose:
```
sudo docker-compose up
```
После сборки docker-compose создадутся три контейнера:
- контейнер базы данных db
- контейнер приложения backend
- контейнер веб-сервера nginx
Создайте миграции в контейнере приложения `backend`
```
sudo docker-compose exec backend python manage.py makemigrations users
sudo docker-compose exec backend python manage.py migrate
sudo docker-compose exec backend python manage.py makemigrations recipes
sudo docker-compose exec backend python manage.py migrate
```
### Над проектом работали: 
- Frontend - https://github.com/yandex-praktikum/foodgram-project-react
- Backend - https://github.com/KhitK0101