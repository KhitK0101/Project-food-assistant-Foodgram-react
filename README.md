# Проект продуктовый помощник Foodgram
[![Foodgram](https://github.com/KhitK0101/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)](https://github.com/KhitK0101//foodgram-project-react/actions/workflows/foodgram_workflow.yml) 
[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)

## Описание

Foodgram - это сервис, позволяющий пользователям публиковать свои рецепты, подписываться на рецепты других пользователей, добавлять понравившиеся рецепты в список «Избранное», а также загружать сводный список продуктов, необходимых для приготовления выбранных блюд.

## Запуск проекта в dev-режиме :computer:

1. Склонируйте репозиторий на локальную машину:
```
git clone <адрес репозитария>
```

2. Установите виртуальное окружение:
```
python -m venv venv
```

3. Активируйте виртуальное окружение:
```
source venv\Scripts\activate
```

4. Перейдите в директорию `/infra` и создайте файл `.env`:
```
cd infra
touch .env
```
5. Заполните файл содержанием из файла [infra/.env.example](https://github.com/KhitK0101/foodgram-project-react/blob/master/infra/.env.example).
```
DB_ENGINE='django.db.backends.postgresql' # указываем, что работаем с postgresql
DB_NAME='postgres' # имя базы данных
POSTGRES_USER='postgres' # логин для подключения к базе данных
POSTGRES_PASSWORD='postgres' # пароль для подключения к БД (установите свой)
DB_HOST='127.0.0.1' # адрес и доменное имя (контейнера)
DB_PORT='5432' # порт для подключения к БД
SECRET_KEY = <секретный ключ>
```
6. Перейдите в каталог `backend` и установите зависимости:
```
cd ../backend
pip install -r requirements.txt
```
7. Настройте базу данных в файле `backend/foodgram/settings.py`.
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```
8. Выполните миграции:
```
python manage.py migrate
```

9. Запустите Django сервер:
```
python manage.py runserver
```

## Запуск проекта на удаленном сервере :milky_way:

Процесс запуска проекта на удаленном сервере выполнен с использованием контейнеров Docker. :whale:

### Установка Docker и Docker Compose
1. Установите Docker на сервере:
   ```
   sudo apt install docker.io 
   ```

2. Установите Docker Compose на сервере. Следуйте инструкциям по установке и использованию Docker Compose в Ubuntu 20.04 (https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04-ru).

### Подготовка сервера
1. Создайте каталог foodgram на сервере.

2. В локальной среде отредактируйте файл infra/nginx.conf. В строке server_name впишите свой IP.

3. Скопируйте на сервер конфигурационные файлы docker-compose.yml и nginx.conf из каталога infra/. Скопируйте также ваш локальный файл .env в эту же директорию.

4. Выполните команду:
   ```
   sudo nano /etc/nginx/sites-enabled/default
   ```
   Добавьте ваш домен по следующему шаблону:
   ```
    server {
        server_name <Ваш домен>;

        location / {
            proxy_set_header Host $http_host;
            proxy_pass <Ваш адрес хоста>;
        }
    }
   ```
--------------------------------------------------------------------
#### Опционально: шифрование HTTPS
1. Установите certbot, используя пакетный менеджер snap. Выполните команду:
   ```
   sudo apt install snapd
   ```

2. Запустите certbot и получите SSL-сертификат:
   ```
   sudo certbot --nginx
   ```
   В процессе оформления сертификата необходимо будет указать свою электронную почту и ответить на несколько вопросов.

   После завершения процесса, конфигурация Nginx будет автоматически изменена: в файл /etc/nginx/sites-enabled/default будут добавлены новые настройки и прописаны пути к сертификату.

   Перезагрузите конфигурацию Nginx:
   ```
   sudo systemctl reload nginx
   ```

3. Откройте через браузер ваш проект. Теперь в адресной строке вместо HTTP будет указан протокол HTTPS, а рядом с адресом будет виден символ «замочек».

-------------------------------------------------------------------

## Запуск проекта
1. Скопируйте папку docs на сервер.

2. Для использования Workflow, добавьте переменные окружения в Secrets GitHub:
   ```
   POSTGRES_USER=<пользователь_бд>
   POSTGRES_PASSWORD=<пароль>
   DB_NAME=<имя_базы_данных>
   DB_HOST=<db>
   DB_PORT=<5432>
   DB_ENGINE=<django.db.backends.postgresql>
   DOCKER_PASSWORD=<пароль_DockerHub>
   DOCKER_USERNAME=<имя_пользователя_DockerHub>
   SSH_KEY=<ваш_SSH_ключ (для получения выполните команду: cat ~/ssh/id_rsa)>
   PASSPHRASE=<если_при_создании_ssh-ключа_вы_использовали_фразу-пароль>     
   SSH_USER=<username_для_подключения_к_серверу>
   SSH_HOST=<IP_сервера>
   ```

3. Запустите Docker Compose:
   ```
   sudo docker-compose up
   ```
   После сборки Docker Compose создадутся три контейнера:
   - контейнер базы данных db
   - контейнер приложения backend
   - контейнер веб-сервера nginx

4. Выполните следующие команды:
   
   sudo docker-compose exec backend python manage.py makemigrations users
   sudo docker-compose exec backend python manage.py migrate
   sudo docker-compose exec backend python manage.py makemigrations recipes
   sudo docker-compose exec backend python manage.py collectstatic --no-input
   
   После этого необходимо будет создать суперпользователя:
   
   sudo docker-compose exec backend python manage.py createsuperuser
   

5. Пример проекта доступен по https://foodgrambykhit.sytes.net/

## Участники проекта
- Frontend: https://github.com/yandex-praktikum/foodgram-project-react
- Backend: https://github.com/KhitK0101
