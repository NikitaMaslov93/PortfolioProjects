-- Запрос создания представления обработанных данных для проведения RFM-анализа
create view cohort_als as (
-- Обработанные данные для проведения RFM-анализа
with data_rfm as (
select
    card,
    sum(summ) as monetary,
    count(card) over (partition by card) as frequency,
-- Определение даты, на которую будет проведен RFM-анализ
    max(datetime::date) over() as max_date,
    max(datetime::date) over (partition by card) as max_date_card
from checks
-- Выбор и фильтрация полей для проведения RFM-анализа
where card like '2000%'
group by
    datetime::date,
    card
)
select
    card,
    min(max_date - max_date_card) as recency,
    min(frequency) as frequency,
    sum(monetary) as monetary
from data_rfm
group by card
)
-- Расчет пороговых значений можно проводить разными способами, например:
-- Расчет среднего значения для определения пороговых значений в RFM-анализе
select
    avg(recency) as avg_recency,
    avg(frequency) as avg_frequency,
    avg(monetary) as avg_monetary
from cohort_als

-- Расчет перцентилей и медианы для определения пороговых значений в RFM-анализе
select
    percentile_disc(0.33) within group (order by recency) as percentile_33_recency,
    percentile_disc(0.33) within group (order by frequency) as percentile_33_frequency,
    percentile_disc(0.33) within group (order by monetary) as percentile_33_monetary,
    percentile_disc(0.5) within group (order by recency) as median_recency,
    percentile_disc(0.5) within group (order by frequency) as median_frequency,
    percentile_disc(0.5) within group (order by monetary) as median_monetary,
    percentile_disc(0.66) within group (order by recency) as percentile_66_recency,
    percentile_disc(0.66) within group (order by frequency) as percentile_66_frequency,
    percentile_disc(0.66) within group (order by monetary) as percentile_66_monetary
from cohort_als

-- Запрос создания представления по расчету процентилей
create view cohort_percentile as (
select
    percentile_disc(0.33) within group (order by recency) as percentile_33_recency,
    percentile_disc(0.33) within group (order by frequency) as percentile_33_frequency,
    percentile_disc(0.33) within group (order by monetary) as percentile_33_monetary,
    percentile_disc(0.5) within group (order by recency) as median_recency,
    percentile_disc(0.5) within group (order by frequency) as median_frequency,
    percentile_disc(0.5) within group (order by monetary) as median_monetary,
    percentile_disc(0.66) within group (order by recency) as percentile_66_recency,
    percentile_disc(0.66) within group (order by frequency) as percentile_66_frequency,
    percentile_disc(0.66) within group (order by monetary) as percentile_66_monetary
from cohort_als
)

-- Итоговый результат проведения RFM-анализа
with data_rfm as (
select
    card,
    case
        when recency <= (select percentile_33_recency from cohort_percentile) then 1
        when recency <= (select percentile_66_recency from cohort_percentile) then 2
        else 3
    end as r,
    case
        when frequency <= (select percentile_33_frequency from cohort_percentile) then 3
        when frequency <= (select percentile_66_frequency from cohort_percentile) then 2
        else 1
    end as f,
    case
        when monetary <= (select percentile_33_monetary from cohort_percentile) then 3
        when monetary <= (select percentile_66_monetary from cohort_percentile) then 2
        else 1
    end as m
from cohort_als
order by card
)
select
    card,
    concat(r, f, m) rfm_segm
from data_rfm
order by rfm_segm

-- Запрос создания представления по RFM-анализу
create view rfm_als as (
with data_rfm as (
select
    card,
    case
        when recency <= (select percentile_33_recency from cohort_percentile) then 1
        when recency <= (select percentile_66_recency from cohort_percentile) then 2
        else 3
    end as r,
    case
        when frequency <= (select percentile_33_frequency from cohort_percentile) then 3
        when frequency <= (select percentile_66_frequency from cohort_percentile) then 2
        else 1
    end as f,
    case
        when monetary <= (select percentile_33_monetary from cohort_percentile) then 3
        when monetary <= (select percentile_66_monetary from cohort_percentile) then 2
        else 1
    end as m
from cohort_als
order by card
)
select
    card,
    concat(r, f, m) rfm_segm
from data_rfm
order by rfm_segm
)

-- Список карт покупателей по сегментам:
select
    rfm_segm,
    string_agg(card, ', ')
from rfm_als
group by rfm_segm
order by rfm_segm

-- Количество покупателей в каждом сегменте
select
    rfm_segm,
    count(card) as cnt_customer
from rfm_als
group by rfm_segm
order by rfm_segm

-- Процентное соотношение покупателей в каждом сегменте
select
    rfm_segm,
    round(count(card)*100.0 / 5926, 2) as cnt_customer
from rfm_als
group by rfm_segm
order by rfm_segm desc