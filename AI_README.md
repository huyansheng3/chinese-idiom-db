# 数据表结构

sqlite> PRAGMA table_info(idiom);
cid  name     type     notnull  dflt_value  pk
---  -------  -------  -------  ----------  --
0    id       INTEGER  0                    1 
1    char1    TEXT     1                    0 
2    char2    TEXT     1                    0 
3    char3    TEXT     1                    0 
4    char4    TEXT     1                    0 
5    example  TEXT     0                    0 
6    mean     TEXT     0                    0 
7    py1      TEXT     1                    0 
8    py2      TEXT     1                    0 
9    py3      TEXT     1                    0 
10   py4      TEXT     1                    0 
11   pytone1  TEXT     1                    0 
12   pytone2  TEXT     1                    0 
13   pytone3  TEXT     1                    0 
14   pytone4  TEXT     1                    0 
15   source   TEXT     0                    0 


# 数据样例

sqlite> select * from idiom limit 3;
id  char1  char2  char3  char4  example                             mean                 py1  py2   py3  py4   pytone1  pytone2  pytone3  pytone4  source                                
--  -----  -----  -----  -----  ----------------------------------  -------------------  ---  ----  ---  ----  -------  -------  -------  -------  --------------------------------------
1   哀      思      如      潮                                          哀伤的思绪如同潮涌一般。形容极度悲痛。  ai   si    ru   chao  āi       sī       rú       cháo                                           
2   哀      痛      欲      绝      宝庆给大哥唱了一曲挽歌，直唱得泣不成声，～。（老舍《鼓书艺人》十七）  伤心得要死。形容悲痛到了极点。      ai   tong  yu   jue   āi       tòng     yù       jué      清·曹雪芹《红楼梦》第十三回：“那宝珠按未嫁女之礼在灵前哀哀欲绝。”    
3   挨      肩      擦      膀      那两边围看的，～，不知其数。（明·兰陵笑笑生《金瓶梅词话》第四二回）  指身体相贴近。也形容人群拥挤。      ai   jian  ca   bang  āi       jiān     cā       bǎng     元·刘君锡《来生债》第一折：“你怎么偏要挨肩擦膀的，舒着手往我怀里摸甚么？”


# 数据处理
帮我写一个脚本，将数据表转为csv 格式




