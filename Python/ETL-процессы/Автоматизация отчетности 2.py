#загружаем необходимые бибилиотеки
import telegram
import pandas as pd
import pandahouse as ph
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

#подключаемся к базе данных
connection = {
    'host': 'https://clickhouse.lab.karpov.courses',
                      'database':'simulator_20230520',
                      'user':'student', 
                      'password':'dpo_python_2020'
                     }

#устанавливаем аргументы Дага
default_args = {
    'owner': 'n-maslov',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'start_date': datetime(2023, 6, 12),
}
# Установим расписание
schedule_interval = '0 11 * * *' 

#определяем токен бота
my_token = '6083809220:AAExjUJZaa8pF2p7AoqUVwZpfgYly8MleCY'
bot = telegram.Bot(token=my_token)

#указываем номер ID чата с ботом
chat_id = -910929714


#создаем базу для отравки отчета за вчера
dates = """
SELECT toStartOfDay(time) as days,
    count(DISTINCT user_id) as DAU,
    countIf(user_id, action = 'view') as views,
    countIf(user_id, action = 'like') as likes,
    countIf(user_id, action = 'like') / countIf(user_id, action = 'view') as CTR
    FROM simulator_20230520.feed_actions 
WHERE days = yesterday() 
GROUP BY days
ORDER BY days DESC"""

#формируем отчетность для графиков                                                                                            
week_for_graph = """
SELECT toStartOfDay(time) as days,
    count(DISTINCT user_id) as DAU,
    countIf(user_id, action = 'view') as views,
    countIf(user_id, action = 'like') as likes,
    countIf(user_id, action = 'like') / countIf(user_id, action = 'view') as CTR
FROM simulator_20230520.feed_actions 
WHERE toDate(time) BETWEEN today() - 7 AND yesterday() 
GROUP BY days
ORDER BY days DESC"""  


@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def n_maslov_bot():
    @task
    def my_bot_report():
        df = ph.read_clickhouse(dates, connection=connection)
        msg = '''Отчет за {days}:\nDAU: {DAU}\nViews: {views}\nLikes: {likes}\nCTR: {CTR:.2%}'''\
        .format(days=str(df.days[0]).split(' ')[0],
            DAU=df.DAU[0],
            views=df.views[0],
            likes=df.likes[0],
            CTR=df.CTR[0])  
        bot.sendMessage(chat_id=chat_id, text=msg)
        
        df_2 = ph.read_clickhouse(week_for_graph, connection=connection)
        fig, ax = plt.subplots(2, 2, figsize=(25, 20))
        ax[0, 0].plot(df_2['days'], df_2['DAU'], marker="o", label="uniqal users", color = 'indigo')
        ax[0, 0].set_xlabel('date')
        ax[0, 0].set_ylabel('DAU')
        ax[0, 0].set_title('DAU за прошедшую неделю', fontsize=20, fontweight="bold")

        ax[0, 1].plot(df_2['days'], df_2['CTR'], marker="o", label="uniqal users", color = 'darkorange')
        ax[0, 1].set_xlabel('date')
        ax[0, 1].set_ylabel('CTR')
        ax[0, 1].set_title('CTR за прошедшую неделю', fontsize=20, fontweight="bold")

        ax[1, 0].plot(df_2['days'], df_2['views'], marker="o", label="uniqal users", color = 'crimson')
        ax[1, 0].set_xlabel('date')
        ax[1, 0].set_ylabel('views')
        ax[1, 0].set_title('Views за прошедшую неделю', fontsize=20, fontweight="bold")

        ax[1, 1].plot(df_2['days'], df_2['likes'], marker="o", label="uniqal users", color = 'green')
        ax[1, 1].set_xlabel('date')
        ax[1, 1].set_ylabel('likes')
        ax[1, 1].set_title('Likes за прошедшую неделю', fontsize=20, fontweight="bold")

        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.seek(0)
        plot_object.name = 'my_report_bot.png'
        plt.close()
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
        
    my_bot_report()
    
n_maslov_bot = n_maslov_bot()
