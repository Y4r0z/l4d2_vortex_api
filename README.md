Небольшой веб-сервис для серверов l4d2.


## Миграция Alembic
### Миграция базы данных
1. Создай python virtual enviroment
2. Установи все модули - `pip install -r requirements.txt`
3. Отметь свою версию БД как "первую" - `alembic stamp 35c7d4dd0cd1`
4. Улучшись до последней версии - `alembic upgrade head`

Это нужно проделать только один раз, в следующий раз можно прописывать только последнюю команду


## Если пакеты в Docker не устанавливаются
'sudo nano /etc/resolv.conf' > nameserver 8.8.8.8