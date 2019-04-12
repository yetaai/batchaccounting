create table if not exists orga(
orga int,
sname varchar(30),
url varchar(100),
usr varchar(50),
password varchar(50),
usrxpath varchar(256),
passxpath varchar(256),
earliest varchar(10),
loginxpath varchar(256),
txt varchar(512),
UNIQUE INDEX organame (sname),
primary key (orga)
);
-- orga 0 means self managmed account.
create table if not exists acc (
orga int,
acc int,
accno varchar(30),
acctype varchar(20),
ledgertype varchar(20),
routineno varchar(30),
dayspan int,
txt varchar(512),
curdef varchar(5),
syncbal double,
syncdate bigint,
UNIQUE INDEX accno (orga, accno),
primary key (orga, acc)
);
create table if not exists trans (
id int,
orga int,
acc int,
ptime bigint,
sdate char(10),
curr varchar(5),
xrate double,
amt double,
earthid varchar(100),
impid bigint,
trantype varchar(20),
name varchar(512),
memo varchar(512),
txt varchar(512),
index accdate (orga, acc, sdate, curr, amt),
index earthid (earthid),
primary key(id)
);
create table if not exists track (
  trackid int,
  txt varchar(20),
  isdefault boolean,
  primary key (trackid)
);
create table if not exists trackitem (
  trackid int,
  expstep char(15),
  tranid int,
  primary key(trackid, tranid)
);
create table if not exists fields(
id int,
filetype varchar(10),
inname varchar(50),
extname varchar(50),
primary key (id)
);
