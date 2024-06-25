---
title: Prozhito Recsys
emoji: 📈
colorFrom: gray
colorTo: indigo
sdk: docker
app_port: 8501
---

# Демо-приложение для рекомендательной системы в проекте Прожито

## Подготовка

Приложение поставляется без базы данных записей Прожито.
Для работы приложения необходимо скачать файл DuckDB с векторизацией записей.

**Вариант 1**: использовать локальный файл: `data/diaries_vec.db` (путь настраивается в `app/config.py`).

**Вариант 2**: использовать ссылку на удалённый файл в контейере. Для этого необходимо [установить секрет для Docker](https://docs.docker.com/build/building/secrets/) c id `data_download_url` на URL файла. И затем запускать контейнер с использованием параметра `-secret id=data_download_url,src=...`
 
## Запуск

### Docker

Установка секрета:
```bash
mkdir .secrets
echo "YOUR_URL/diaries_vec.db" > .secrets/data-download-url
```

Билд и запуск контейнера:
```bash
docker build --secret id=data_download_url,src=".secrets/data-download-url"  . --tag prozhito-streamlit
docker run -p 8501:8501 prozhito-streamlit
```

### Poetry

Установите [Poetry](https://python-poetry.org/docs/).

```bash
poetry init
poetry run streamlit run app/app.py
```
