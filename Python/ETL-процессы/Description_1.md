# Описание задачи

Бизнес-заказчик - зам. руководителя маркетинга социальной сети. Соц. сеть имеет встроенную ленту новостей (постов) и чат для пользователей. Руководитель хочет ежедневно отслеживать показатели по просмотрам, лайкам, количеству отправленных и полученных сообщений в разрезе пола и ОS. Результаты должны быть сохранены в Clickhouse и в дальнейшем обновляться.

В рамках данной работы мной был подготовлен ETL-процесс с использованием Airflow, где данные из разных таблиц БД подтягиваются, преобразуются и выгругружаются в требуемом виде.
В этот репозиторий для примера я включил:

1. [Код, отрабатывающий задачу разово](https://github.com/NikitaMaslov93/PortfolioProjects/blob/main/Python/ETL-%D0%BF%D1%80%D0%BE%D1%86%D0%B5%D1%81%D1%81%D1%8B/etl_descrp.ipynb) (`.ipynb`)
2. [код ETL-процесса для Airflow](https://github.com/NikitaMaslov93/PortfolioProjects/blob/main/Python/ETL-%D0%BF%D1%80%D0%BE%D1%86%D0%B5%D1%81%D1%81%D1%8B/etl_process.py) (`.py`)
3. [Cхема пайплайна](https://github.com/NikitaMaslov93/PortfolioProjects/blob/main/Python/ETL-%D0%BF%D1%80%D0%BE%D1%86%D0%B5%D1%81%D1%81%D1%8B/pipline_scheme.png)
4. [Результат ETL-процесса](https://github.com/NikitaMaslov93/PortfolioProjects/blob/main/Python/ETL-%D0%BF%D1%80%D0%BE%D1%86%D0%B5%D1%81%D1%81%D1%8B/etl_result.PNG)

