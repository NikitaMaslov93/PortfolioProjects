# coding=utf-8
from datetime import datetime, timedelta
import pandas as pd
import pandahouse as ph

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

# Основные настройки для задач
default_args = {
    'owner': 'admin_user',
    'depends_on_past': False,
    'retries': 1,
    'retry_interval': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

# График запуска DAG
schedule_interval = '0 9 * * *'

@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def dag_maslov_task():

    # Анализ действий в ленте: подсчёт просмотров и лайков
    @task()
    def extract_feed():
        # Параметры подключения к базе ClickHouse
        clickhouse_connection = {
            'host': 'https://clickhouse.lab.karpov.courses',
            'password': 'dpo_python_2020',
            'user': 'student',
            'database': 'simulator'
        }

        # SQL запрос для данных из feed_actions
        feed_query = '''
            select  yesterday() as event_date,
                    user_id,
                    sum(action = 'like') as likes,
                    sum(action = 'view') as views,
                    max(gender) as gender,
                    max(age) as age,
                    max(os) as os
            from simulator_20240320.feed_actions
            where toDate(time)+10 = yesterday() 
            group by user_id
        '''
        feed_data = ph.read_clickhouse(feed_query, connection=clickhouse_connection)
        return feed_data
    
    # Анализ сообщений: подсчёт отправленных и полученных сообщений
    @task()
    def extract_messages():
        # Параметры подключения к базе ClickHouse
        clickhouse_connection = {
            'host': 'https://clickhouse.lab.karpov.courses',
            'password': 'dpo_python_2020',
            'user': 'student',
            'database': 'simulator'
        }

        # SQL запрос для данных из message_actions
        message_query = '''
            select  yesterday() as event_date,
                    user_id,
                    count(receiver_id) as messages_sent,
                    countIf(user_id in  (select receiver_id from simulator_20240320.message_actions
                    where toDate(time)+10 = yesterday())
                    ) as messages_received,
                    count(distinct receiver_id) as users_sent,
                    countIf(user_id in  (select distinct receiver_id from simulator_20240320.message_actions
                    where toDate(time)+10 = yesterday())
                    ) as users_received,
                    max(gender) as gender,
                    max(age) as age,
                    max(os) as os
            from simulator_20240320.message_actions
            where toDate(time)+10 = yesterday() 
            group by user_id
        '''
        message_data = ph.read_clickhouse(message_query, connection=clickhouse_connection)
        return message_data    

    # Объединение данных
    @task
    def join_cubes(feed_data, message_data):
        combined_data = feed_data.merge(message_data, on=['event_date', 'user_id', 'gender', 'age', 'os'], how='outer')
        return combined_data

    # Подготовка отчёта по полу
    @task
    def transform_metric(combined_data):
        gender_stats = combined_data.groupby(['event_date', 'gender'])\
            .agg(views=('views', 'sum'),
                 likes=('likes', 'sum'),
                 messages_received=('messages_received', 'sum'),
                 messages_sent=('messages_sent', 'sum'),
                 users_received=('users_received', 'sum'),
                 users_sent=('users_sent', 'sum')
                )\
            .reset_index()\
            .rename(columns={'gender': 'dimension_value'})
        gender_stats.dimension_value = gender_stats.dimension_value.astype(str)
        gender_stats.insert(loc=1, column='dimension', value='gender')
        return gender_stats

    # Загрузка данных в ClickHouse
    @task
    def load(dataframe, table_name):
        # Параметры подключения к тестовой базе ClickHouse
        clickhouse_test_connection = {
            'host': 'https://clickhouse.lab.karpov.courses',
            'database': 'test',
            'user': 'student-rw',
            'password': '656e2b0c9c'
        }
        ph.to_clickhouse(df=dataframe, table=table_name, index=False, connection=clickhouse_test_connection)

    # Запуск DAG
    feed_data = extract_feed()
    message_data = extract_message()
    combined_data = join_cubes(feed_data, message_data)
    gender_stats = transform_metric(combined_data)
    load(gender_stats, 'maslov_dag')
    
dag_maslov_task = dag_maslov_task()
