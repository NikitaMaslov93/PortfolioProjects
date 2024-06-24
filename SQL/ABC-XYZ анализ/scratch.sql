--  запрос по проведению ABC-анализа
create view result_abc as (
    with sales_data as (
    select
        name,
        sum(quantity) as amount,
        sum(revenue) as revenue
    from pizza_full_data
    where year = 2015
    group by name
    order by name
)
select
    name,
    case
        when sum(amount) over(order by amount desc) / sum(amount) over() <= 0.8 then 'A'
        when sum(amount) over(order by amount desc) / sum(amount) over() <= 0.95 then 'B'
        else 'C'
    end abc_amount,
    case
        when sum(revenue) over(order by revenue desc) / sum(revenue) over() <= 0.8 then 'A'
        when sum(revenue) over(order by revenue desc) / sum(revenue) over() <= 0.95 then 'B'
        else 'C'
    end abc_revenue
from sales_data
)
-- запрос по проведению XYZ-анализа
create view result_xyz as (
    with group_data_xyz as (
    select
        month,
        name,
        sum(quantity) as quantity
    from pizza_full_data
    where year = 2015
    group by month, name
    order by name
), xyz as (
    select
        month,
        name,
        quantity,
        stddev_pop(quantity) over (partition by name),
        avg(quantity) over (partition by name),
        round(stddev_pop(quantity) over (partition by name) / avg(quantity) over (partition by name), 3) as covar
from group_data_xyz
), xyz_total as (
select
    name,
    min(covar) as cov
from xyz
group by name
)
select
    name,
    cov,
    case
        when cov <= 0.1 then 'X'
        when cov <= 0.20 then 'Y'
        else 'Z'
    end xyz
from xyz_total
order by name
)

-- Объединение результатов для ABC-XYZ анализа
with abc_xyz as (
    select
    abc.name,
    abc.abc_amount,
    abc.abc_revenue,
    xyz.xyz
 from result_abc abc
 join result_xyz xyz
    on abc.name = xyz.name
order by abc.name
)

-- Итоговый запрос
select
    name as pizza,
    abc_amount || xyz as abc_xyz_quantity,
    abc_revenue || xyz as abc_xyz_revenue
from abc_xyz