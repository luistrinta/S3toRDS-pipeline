create table car_data(
deviceid varchar(10) not null,
timestamp date not null,
model varchar(20) null default '-1',
odometer_km int null default -1,
trip_driven_km float null default 0,
instant_consumption_l_per_100km float null default 0,
fuel_level_pct float null default -1,
city varchar(50) null,
country_code varchar(4) null,
region varchar(30) null
)
partition by hash(model,city)
