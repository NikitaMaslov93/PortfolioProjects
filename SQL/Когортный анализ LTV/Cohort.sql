with data_cohort as (
select
    card,
    datetime,
    first_value(to_char(datetime, 'YYYY-MM')) over(partition by card order by datetime) as cohort,
    extract(days from datetime - first_value(datetime) over(partition by card order by datetime)) as df_days,
    summ
from checks
-- Есть "битые" данные, поэтому требуется фильтр (корректные данные начинаются всегда с "2000")
where card like '2000%'
order by card
)
select
    cohort,
    count(distinct card) as cnt_customer,
    max(df_days) as max_df_days,
    round(sum(case when df_days = 0 then summ end) / count(distinct card)) as "0_day",
 -- Округленная средняя выручка на одного покупателя в каждой когорте
 -- конструкция дает null если время "жизни" когорты недостаточно для попадания, например в группу 60 дня
    round(case when max(df_days) > 0 then sum(case when df_days <= 30 then summ end) / count(distinct card) end) as "30_day",
    round(case when max(df_days) > 30 then sum(case when df_days <= 60 then summ end) / count(distinct card) end) as "60_day",
    round(case when max(df_days) > 60 then sum(case when df_days <= 90 then summ end) / count(distinct card) end) as "90_day",
    round(case when max(df_days) > 90 then sum(case when df_days <= 180 then summ end) / count(distinct card) end) as "180_day",
    round(case when max(df_days) > 180 then sum(case when df_days <= 300 then summ end) / count(distinct card) end) as "300_day",
    round(case when max(df_days) > 300 then sum(case when df_days <= 400 then summ end) / count(distinct card) end) as "400_day"
from data_cohort
group by cohort
order by cohort