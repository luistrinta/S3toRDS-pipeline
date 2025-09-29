create table public.car_data(
deviceid varchar(10) not null,
timestamp date not null,
model varchar(30) not null default '-1',
odometer_km int null default -1,
trip_driven_km float null default 0,
instant_consumption_l_per_100km float null default 0,
fuel_level_pct float null default -1,
city varchar(50) null,
country_code varchar(4) null,
timezone varchar(30) null
)
partition by hash(model,city)


CREATE TABLE public.car_data_part1 PARTITION OF public.car_data FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE public.car_data_part2 PARTITION OF public.car_data FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE public.car_data_part3 PARTITION OF public.car_data FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE public.car_data_part4 PARTITION OF public.car_data FOR VALUES WITH (MODULUS 4, REMAINDER 3);
