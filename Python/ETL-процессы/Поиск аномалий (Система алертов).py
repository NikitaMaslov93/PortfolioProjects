import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import telegram
import pandahouse as ph
from datetime import date
import io
import sys
import os
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

# подключаемся к базе
connection = {
    'host': 'https://clickhouse.lab.karpov.courses',
    'password': 'dpo_python_2020',
    'user': 'student',
    'database': 'simulator_20230520'
}

# Прописываем пераметры ДАГ'а
default_args = {
    'owner': 'n-maslov',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'start_date': datetime(2023, 6, 15),
}

# Периодичность проверки на аномалии устанавливаем с частотой раз в 15 минут
schedule_interval = '*/15 * * * *' 

# функция check_anomaly предлагает алгоритм проверки значения на аномальность по средством сравнения текущего межквартильного размаха
# на основе среднех значений n-ого числа последних 15-ти минуток.   
def check_anomaly(df, metric, a=4, n=5):
    
    df['q25'] = df[metric].shift(1).rolling(n).quantile(0.25)
    df['q75'] = df[metric].shift(1).rolling(n).quantile(0.75)
    
    df['igr'] = df['q75'] - df['q25']
    df['up'] = df['q75'] + a * df['igr']
    df['low'] = df['q25'] - a * df['igr']
    
    df['up'] = df['up'].rolling(n, center=True, min_periods=1).mean()
    df['low'] = df['low'].rolling(n, center=True, min_periods=1).mean()
    
    # если значение порога больше допустимого - вернем 1, иначе 0
    if df[metric].iloc[-1] < df['low'].iloc[-1] or df[metric].iloc[-1] > df['up'].iloc[-1]:
        is_alert = 1
    else:
        is_alert = 0   

    return is_alert, df

def run_alerts():
    chat_id = -969316925
    bot = telegram.Bot(token='6083809220:AAExjUJZaa8pF2p7AoqUVwZpfgYly8MleCY')

    # для удобства построения графиков в запрос можно добавить колонки date и hm
    q = """ SELECT * FROM
                    (SELECT
                      toStartOfFifteenMinutes(time) as ts
                    , toDate(ts) as date
                    , formatDateTime(ts, '%R') as hm
                    , uniqExact(user_id) as users_feed
                    , countIf(user_id, action='view') as views
                    , countIf(user_id, action='like') as likes
                    , likes / views as ctr
                    FROM simulator_20230520.feed_actions
                    WHERE ts >=  today() - 1 and ts < toStartOfFifteenMinutes(now())
                    GROUP BY ts, date, hm
                    ORDER BY ts) t1
        
                JOIN
                     (SELECT toStartOfFifteenMinutes(time) as ts,
                    toDate(time) as date,
                    formatDateTime(ts, '%R') as hm,
                    uniq(user_id) as users_mes,
                    count(user_id) as mes
                    FROM simulator_20230520.message_actions 
                    WHERE time >= today() - 1 and time < toStartOfFifteenMinutes(now())
                    GROUP BY ts, date, hm
                    ORDER BY ts) t2
                USING (ts, date, hm) """
    
    data = ph.read_clickhouse(q, connection=connection)
#Создаем список метрик по которым будем пробегаться нашим алгоритмом для поиска аномалий.    
    metrics_list = ['users_feed', 'views', 'likes', 'ctr', 'users_mes', 'mes']
    for metric in metrics_list:
        df = data[['ts', 'date', 'hm', metric]].copy()
        is_alert, df = check_anomaly(df, metric)
    
    
        if is_alert == 1: 

            msg = '''Метрика {metric}:\nтекущее значение = {current_value:.2f}\nотклонение от предыдущего значения 
                     {last_val_diff:.2%}'''.format(metric=metric,
                                            current_value=df[metric].iloc[-1],
                                            last_val_diff=abs(1-(df[metric].iloc[-1]/df[metric].iloc[-2])))

# Задаю параметры графика и определяю данные на его оси
            sns.set(rc={'figure.figsize': (16, 12)}) 
            plt.tight_layout()

            ax = sns.lineplot(x=df['ts'], y=df[metric],label='metric')
            ax = sns.lineplot(x=df['ts'], y=df['up'],label='up')
            ax = sns.lineplot(x=df['ts'], y=df['low'],label='low')
            
# Этим циклом разряжаем подписи координат по оси Х, чтобы не было наслоения дат друг на друга
            for ind, label in enumerate(ax.get_xticklabels()):
                if ind % 2 == 0:
                    label.set_visible(True)
                else:
                    label.set_visible(False)

            ax.set(xlabel='time') 
            ax.set(ylabel=metric) 
            ax.set_title(metric) 
            ax.set(ylim=(0, None))

            # формируем файловый объект, чтобы не складировать изображения графиков локально, а перезаписывать
            plot_object = io.BytesIO()
            ax.figure.savefig(plot_object)
            plot_object.seek(0)
            plot_object.name = '{0}.png'.format(metric)
            plt.close()

            # отправляем алерт В чат
            bot.sendMessage(chat_id=chat_id, text=msg)
            bot.sendPhoto(chat_id=chat_id, photo=plot_object)

@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def anomaly_detection_maslov():
    
    @task
    def load_report():
        run_alerts()
    load_report()
    
    
anomaly_detection_maslov = anomaly_detection_maslov()