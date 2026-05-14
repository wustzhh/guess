import random
import re
import os
import json as json_lib
from difflib import SequenceMatcher
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Character Database ──────────────────────────────────────────────

CHARACTERS = [
    # ═══ 蜀汉 ═══
    {
        "name": "诸葛亮", "alias": ["孔明", "卧龙"],
        "category": "三国", "death_year": 234, "born_year": 181, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": False, "是文臣": True, "是谋士": True,
                  "文武兼备": True, "上阵杀敌": False, "当过大都督": False, "当过丞相": True,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "诸葛亮（181年—234年），字孔明，号卧龙，琅琊阳都人。早年隐居隆中，刘备三顾茅庐请其出山。辅佐刘备建立蜀汉政权，任丞相。刘备去世后受托孤之重，辅佐刘禅。五次北伐曹魏，最终病逝于五丈原。被誉为「千古第一贤相」，是中国历史上智慧和忠诚的象征。",
        "events": [
        {
                "text": "三顾茅庐出山",
                "year": 207
        },
        {
                "text": "赤壁之战",
                "year": 208
        },
        {
                "text": "病逝五丈原",
                "year": 234
        }
]
    },
    {
        "name": "刘备", "alias": ["刘玄德", "刘皇叔"],
        "category": "三国", "death_year": 223, "born_year": 161, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": True, "是武将": False, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": True},
        "bio": "刘备（161年—223年），字玄德，涿郡涿县人。东汉末年起兵，先后依附公孙瓒、陶谦、曹操、袁绍、刘表等。三顾茅庐请出诸葛亮后事业转机。赤壁之战后夺取荆州、益州，221年称帝建立蜀汉。夷陵之战大败后病逝于白帝城，临终托孤诸葛亮。以仁德著称，是蜀汉开国皇帝。",
        "events": [
        {
                "text": "三顾茅庐",
                "year": 207
        },
        {
                "text": "赤壁之战",
                "year": 208
        },
        {
                "text": "入主益州",
                "year": 214
        },
        {
                "text": "称帝",
                "year": 221
        },
        {
                "text": "夷陵之战大败",
                "year": 222
        },
        {
                "text": "白帝城托孤",
                "year": 223
        }
]
    },
    {
        "name": "关羽", "alias": ["关云长", "关公", "美髯公"],
        "category": "三国", "death_year": 220, "born_year": 160, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "关羽（？—220年），字云长，河东解良人。与刘备、张飞桃园结义。曾一度被曹操俘虏，但「身在曹营心在汉」，最终回到刘备身边。镇守荆州期间威震华夏，水淹七军擒于禁斩庞德。后被吕蒙偷袭荆州，败走麦城被杀。被后世尊为「武圣」，是忠义的化身。",
        "events": [
        {
                "text": "水淹七军斩庞德",
                "year": 219
        },
        {
                "text": "被吕蒙袭杀",
                "year": 219
        }
]
    },
    {
        "name": "张飞", "alias": ["张翼德"],
        "category": "三国", "death_year": 221, "born_year": 165, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "张飞（？—221年），字翼德，涿郡人。与刘备、关羽桃园结义。以勇猛著称，长坂坡据水断桥，喝退曹军。随刘备入蜀，义释严颜。官至车骑将军。因急于为关羽报仇，酒后鞭打部下，被部下刺杀。性格豪爽粗犷，但后来也有义释严颜这样的智慧之举。",
        "events": [
        {
                "text": "被部下刺杀",
                "year": 221
        }
]
    },
    {
        "name": "赵云", "alias": ["赵子龙"],
        "category": "三国", "death_year": 229, "born_year": 168, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": True, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "赵云（？—229年），字子龙，常山真定人。初属公孙瓒，后投奔刘备。长坂坡单骑救阿斗，七进七出。汉水之战以空营计退敌。随刘备入蜀，参与博望坡、赤壁等重大战役。官至镇军将军。以忠勇谨慎著称，是蜀汉五虎上将之一。",
        "events": [
        {
                "text": "长坂坡救阿斗",
                "year": 208
        },
        {
                "text": "汉水空营退敌",
                "year": 219
        }
]
    },
    {
        "name": "马超", "alias": ["马孟起"],
        "category": "三国", "death_year": 222, "born_year": 176, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "马超（176年—222年），字孟起，扶风茂陵人。东汉名将马援之后。在关中起兵反曹操，一度大败曹操使其割须弃袍。后被曹操击败，先投张鲁，再降刘备。刘备称汉中王后封马超为左将军。以「锦马超」之名威震西北，是蜀汉五虎上将之一。",
        "events": [
        {
                "text": "起兵反曹操",
                "year": 211
        },
        {
                "text": "降刘备",
                "year": 214
        }
]
    },
    {
        "name": "黄忠", "alias": ["黄汉升"],
        "category": "三国", "death_year": 220, "born_year": 148, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "黄忠（？—220年），字汉升，南阳人。原为刘表部下，后归顺刘备。定军山之战中斩杀曹操大将夏侯渊，威震天下。虽年事已高却老当益壮。刘备称汉中王后封黄忠为后将军，位列五虎上将之一。次年病逝。以「老当益壮」留名青史。",
        "events": [
        {
                "text": "定军山斩夏侯渊",
                "year": 219
        }
]
    },
    {
        "name": "魏延", "alias": ["魏文长"],
        "category": "三国", "death_year": 234, "born_year": 175, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "魏延（？—234年），字文长，义阳人。原为刘备部曲，随刘备入蜀，屡立战功。汉中太守，镇守汉中十余年。诸葛亮北伐时，魏延多次提出子午谷奇谋但未被采纳。性格骄傲，与杨仪不和。诸葛亮死后，与杨仪争权失败，被马岱斩杀。是蜀汉后期重要将领。",
        "events": [
        {
                "text": "被马岱斩杀",
                "year": 234
        }
]
    },
    {
        "name": "姜维", "alias": ["姜伯约"],
        "category": "三国", "death_year": 264, "born_year": 202, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": True, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "姜维（202年—264年），字伯约，天水冀县人。原为曹魏将领，后降诸葛亮，深受器重。诸葛亮死后继承其遗志，多次北伐曹魏。官至大将军。263年蜀汉灭亡后，他策划复国但事泄被杀。是蜀汉最后的名将，诸葛亮北伐事业的继承者。",
        "events": [
        {
                "text": "降蜀汉",
                "year": 228
        },
        {
                "text": "九伐中原",
                "year": 249
        },
        {
                "text": "蜀亡被杀",
                "year": 264
        }
]
    },
    {
        "name": "徐庶", "alias": ["徐元直"],
        "category": "三国", "death_year": 235, "born_year": 170, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": False, "是文臣": False, "是谋士": True,
                  "文武兼备": False, "上阵杀敌": False, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "徐庶（约170年—约235年），字元直，颍川阳翟人。初投奔刘备，是刘备第一位真正意义上的谋士。向刘备力荐好友诸葛亮。后来母亲被曹操掳走，被迫投奔曹魏。临别时向刘备保证「终身不为曹操设一谋」——「身在曹营心在汉」由此而来。在曹魏官至右中郎将，终生未曾为曹操献过一策。",
        "events": [
        {
                "text": "投刘备荐诸葛亮",
                "year": 207
        },
        {
                "text": "被迫投曹",
                "year": 208
        },
        {
                "text": "卒于曹魏",
                "year": 235
        }
]
    },
    {
        "name": "庞统", "alias": ["庞士元", "凤雏"],
        "category": "三国", "death_year": 214, "born_year": 179, "gender": "男",
        "阵营": "蜀",
        "flags": {"是君主": False, "是武将": False, "是文臣": True, "是谋士": True,
                  "文武兼备": False, "上阵杀敌": False, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "庞统（179年—214年），字士元，号凤雏，襄阳人。与诸葛亮齐名，被誉为「卧龙凤雏，得一可安天下」。初投刘备，不被重视，后经诸葛亮和鲁肃推荐被重用。随刘备入蜀，在围攻雒城时中流矢身亡，年仅36岁。英年早逝，未能充分施展才华。",
        "events": [
        {
                "text": "随刘备入蜀",
                "year": 211
        },
        {
                "text": "雒城中箭身亡",
                "year": 214
        }
]
    },
    # ═══ 曹魏 ═══
    {
        "name": "曹操", "alias": ["曹孟德", "曹阿瞒"],
        "category": "三国", "death_year": 220, "born_year": 155, "gender": "男",
        "阵营": "魏",
        "flags": {"是君主": True, "是武将": False, "是文臣": False, "是谋士": False,
                  "文武兼备": True, "上阵杀敌": True, "当过大都督": False, "当过丞相": True,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "曹操（155年—220年），字孟德，沛国谯县人。东汉末年杰出的政治家、军事家、文学家。讨伐董卓起家，逐步统一北方。挟天子以令诸侯，官渡之战大败袁绍，为曹魏奠定基础。任丞相，封魏王。死后其子曹丕称帝，追尊为魏武帝。一生雄才大略，是三国第一枭雄。",
        "events": [
        {
                "text": "官渡之战败袁绍",
                "year": 200
        },
        {
                "text": "赤壁之战",
                "year": 208
        },
        {
                "text": "称魏王",
                "year": 216
        },
        {
                "text": "病逝洛阳",
                "year": 220
        }
]
    },
    {
        "name": "司马懿", "alias": ["司马仲达"],
        "category": "三国", "death_year": 251, "born_year": 179, "gender": "男",
        "阵营": "魏",
        "flags": {"是君主": False, "是武将": False, "是文臣": True, "是谋士": True,
                  "文武兼备": True, "上阵杀敌": False, "当过大都督": True, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "司马懿（179年—251年），字仲达，河内温县人。曹魏重臣，杰出的军事家和政治家。先后辅佐曹操、曹丕、曹叡三代。以隐忍著称，熬死了诸葛亮。高平陵之变夺取曹魏政权，为西晋建立奠定基础。孙子司马炎称帝后追尊为晋宣帝。是三国最大的赢家。",
        "events": [
        {
                "text": "征辽东斩公孙渊",
                "year": 238
        },
        {
                "text": "高平陵之变夺权",
                "year": 249
        },
        {
                "text": "去世",
                "year": 251
        }
]
    },
    {
        "name": "郭嘉", "alias": ["郭奉孝"],
        "category": "三国", "death_year": 207, "born_year": 170, "gender": "男",
        "阵营": "魏",
        "flags": {"是君主": False, "是武将": False, "是文臣": False, "是谋士": True,
                  "文武兼备": False, "上阵杀敌": False, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "郭嘉（170年—207年），字奉孝，颍川阳翟人。初投袁绍，后经荀彧推荐投奔曹操。官渡之战前提出「十胜十败论」，坚定了曹操的决战信心。多次为曹操出谋划策，算无遗策。在征乌桓途中病逝，年仅38岁。曹操赤壁兵败后曾感叹：「郭奉孝在，不使孤至此。」",
        "events": [
        {
                "text": "投曹操",
                "year": 196
        },
        {
                "text": "征乌桓途中病逝",
                "year": 207
        }
]
    },
    {
        "name": "荀彧", "alias": ["荀文若"],
        "category": "三国", "death_year": 212, "born_year": 163, "gender": "男",
        "阵营": "魏",
        "flags": {"是君主": False, "是武将": False, "是文臣": True, "是谋士": True,
                  "文武兼备": False, "上阵杀敌": False, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "荀彧（163年—212年），字文若，颍川颍阴人。初投袁绍，后投奔曹操。曹操称之为「吾之子房」。为曹操制定统一北方的战略蓝图。推荐了郭嘉、荀攸、钟繇等人才。因反对曹操称公，被曹操猜忌，服毒自尽（一说忧郁而死）。是曹操手下最重要的谋主。",
        "events": [
        {
                "text": "投曹操",
                "year": 191
        },
        {
                "text": "反对称公自杀",
                "year": 212
        }
]
    },
    {
        "name": "典韦", "alias": [],
        "category": "三国", "death_year": 197, "born_year": 160, "gender": "男",
        "阵营": "魏",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "典韦（？—197年），陈留己吾人。身材魁梧，膂力过人。初属张邈，后归曹操。宛城之战中，曹操被张绣偷袭，典韦为保护曹操脱逃，死守营门，身中数十枪而亡。曹操闻讯痛哭，亲自祭奠。是曹魏著名的猛将，被誉为「古之恶来」。",
        "events": [
        {
                "text": "宛城之战战死",
                "year": 197
        }
]
    },
    {
        "name": "张辽", "alias": ["张文远"],
        "category": "三国", "death_year": 222, "born_year": 169, "gender": "男",
        "阵营": "魏",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "张辽（169年—222年），字文远，雁门马邑人。初属丁原、吕布，后降曹操。合肥之战中以八百精骑击退孙权十万大军，威震逍遥津，东吴小儿闻张辽之名不敢夜啼。官至征东将军。是曹操麾下「五子良将」之首，以智勇双全著称。",
        "events": [
        {
                "text": "白狼山斩踏顿",
                "year": 207
        },
        {
                "text": "合肥之战破孙权",
                "year": 215
        }
]
    },
    # ═══ 东吴 ═══
    {
        "name": "孙权", "alias": ["孙仲谋"],
        "category": "三国", "death_year": 252, "born_year": 182, "gender": "男",
        "阵营": "吴",
        "flags": {"是君主": True, "是武将": False, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": False, "当过大都督": False, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": True},
        "bio": "孙权（182年—252年），字仲谋，吴郡富春人。继承父兄基业，坐镇江东。赤壁之战联合刘备大败曹操，奠定了三国鼎立的局面。袭取荆州杀关羽，夷陵之战以陆逊大败刘备。229年称帝建立东吴。晚年多疑好杀，引发「二宫之争」，是东吴在位最久的君主。",
        "events": [
        {
                "text": "赤壁之战联刘抗曹",
                "year": 208
        },
        {
                "text": "袭取荆州",
                "year": 219
        },
        {
                "text": "称帝",
                "year": 229
        }
]
    },
    {
        "name": "周瑜", "alias": ["周公瑾"],
        "category": "三国", "death_year": 210, "born_year": 175, "gender": "男",
        "阵营": "吴",
        "flags": {"是君主": False, "是武将": False, "是文臣": False, "是谋士": True,
                  "文武兼备": True, "上阵杀敌": False, "当过大都督": True, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "周瑜（175年—210年），字公瑾，庐江舒县人。东吴名将，相貌英俊，精通音律。与孙策为好友，共同打下江东基业。赤壁之战中力主抗曹，以火攻大败曹操。后计划攻取益州时病逝于巴丘，年仅36岁。以「周郎」闻名，是东吴四大都督之一，英年早逝的代表。",
        "events": [
        {
                "text": "赤壁之战火烧曹军",
                "year": 208
        },
        {
                "text": "病逝巴丘",
                "year": 210
        }
]
    },
    {
        "name": "鲁肃", "alias": ["鲁子敬"],
        "category": "三国", "death_year": 217, "born_year": 172, "gender": "男",
        "阵营": "吴",
        "flags": {"是君主": False, "是武将": False, "是文臣": True, "是谋士": True,
                  "文武兼备": False, "上阵杀敌": False, "当过大都督": True, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "鲁肃（172年—217年），字子敬，临淮东城人。孙权的重要谋士和外交家。在赤壁之战中力主联刘抗曹。周瑜死后接任大都督，主张孙刘联盟。为人慷慨大方，「指囷相赠」的故事流传至今。战略眼光深远，是东吴四大都督之一。",
        "events": [
        {
                "text": "接任大都督",
                "year": 210
        },
        {
                "text": "去世",
                "year": 217
        }
]
    },
    {
        "name": "吕蒙", "alias": ["吕子明"],
        "category": "三国", "death_year": 219, "born_year": 178, "gender": "男",
        "阵营": "吴",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": True, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "吕蒙（178年—219年），字子明，汝南富陂人。孙权麾下大将。早年以勇武闻名，后听从孙权劝告发奋读书，「士别三日当刮目相待」便出自他的典故。白衣渡江袭取荆州，擒杀关羽。官至都督，封孱陵侯。夺得荆州后不久病逝。是东吴四大都督之一。",
        "events": [
        {
                "text": "白衣渡江袭荆州",
                "year": 219
        }
]
    },
    {
        "name": "陆逊", "alias": ["陆伯言"],
        "category": "三国", "death_year": 245, "born_year": 183, "gender": "男",
        "阵营": "吴",
        "flags": {"是君主": False, "是武将": False, "是文臣": True, "是谋士": True,
                  "文武兼备": True, "上阵杀敌": False, "当过大都督": True, "当过丞相": True,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "陆逊（183年—245年），字伯言，吴郡吴县人。东吴重臣。初与吕蒙合谋袭取荆州，夷陵之战中拜大都督，以火攻大败刘备，奠定三国鼎立格局。石亭之战大败曹休。后拜丞相，集军政大权于一身。晚年因卷入「二宫之争」忧愤而死。是东吴文武兼备的顶级名将。",
        "events": [
        {
                "text": "夷陵之战火攻破刘备",
                "year": 222
        },
        {
                "text": "石亭之战败曹休",
                "year": 228
        },
        {
                "text": "拜丞相",
                "year": 244
        },
        {
                "text": "忧愤而死",
                "year": 245
        }
]
    },
    {
        "name": "孙策", "alias": ["孙伯符", "小霸王"],
        "category": "三国", "death_year": 200, "born_year": 175, "gender": "男",
        "阵营": "吴",
        "flags": {"是君主": True, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "孙策（175年—200年），字伯符，吴郡富春人。孙坚长子，孙权的哥哥。以传国玉玺向袁术借兵，短短数年平定江东六郡，为东吴奠定基业。勇猛无敌，人称「小霸王」。后遇刺受伤，临终将基业托付给弟弟孙权。年仅26岁便英年早逝，是三国最让人惋惜的少年英雄。",
        "events": [
        {
                "text": "平定江东六郡",
                "year": 195
        },
        {
                "text": "遇刺身亡",
                "year": 200
        }
]
    },
    # ═══ 群雄 ═══
    {
        "name": "吕布", "alias": ["吕奉先"],
        "category": "三国", "death_year": 198, "born_year": 156, "gender": "男",
        "阵营": "群雄",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": False,
                  "改换门庭": True, "是女性": False, "称过帝": False},
        "bio": "吕布（？—198年），字奉先，五原九原人。三国第一猛将，善骑射，人称「人中吕布，马中赤兔」。先杀丁原投董卓，又杀董卓投王允。后自立门户，割据徐州。因反复无常、三姓家奴的名声，最终被曹操击败，绞死于白门楼。武艺超群但无谋略，是三国悲剧英雄。",
        "events": [
        {
                "text": "杀董卓",
                "year": 192
        },
        {
                "text": "白门楼被曹操绞杀",
                "year": 198
        }
]
    },
    {
        "name": "袁绍", "alias": ["袁本初"],
        "category": "三国", "death_year": 202, "born_year": 154, "gender": "男",
        "阵营": "群雄",
        "flags": {"是君主": True, "是武将": False, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": False, "当过大都督": False, "当过丞相": False,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "袁绍（？—202年），字本初，汝南汝阳人。出身四世三公的名门望族。起兵讨伐董卓被推为盟主。后占据冀、青、幽、并四州，成为北方最强诸侯。但官渡之战中被曹操以少胜多击败，不久后病逝。多谋少断、外宽内忌的性格导致其最终失败。",
        "events": [
        {
                "text": "讨伐董卓被推盟主",
                "year": 190
        },
        {
                "text": "官渡之战败于曹操",
                "year": 200
        },
        {
                "text": "病逝",
                "year": 202
        }
]
    },
    {
        "name": "董卓", "alias": ["董仲颖"],
        "category": "三国", "death_year": 192, "born_year": 139, "gender": "男",
        "阵营": "群雄",
        "flags": {"是君主": False, "是武将": True, "是文臣": False, "是谋士": False,
                  "文武兼备": False, "上阵杀敌": True, "当过大都督": False, "当过丞相": True,
                  "改换门庭": False, "是女性": False, "称过帝": False},
        "bio": "董卓（？—192年），字仲颖，陇西临洮人。东汉末年权臣。趁朝廷内乱带兵入京，废少帝立献帝，把持朝政。迁都长安，烧毁洛阳。因其暴虐残忍，激起天下诸侯共讨。后中了王允的连环计，被义子吕布所杀。是东汉末年天下大乱的导火索。",
        "events": [
        {
                "text": "废少帝立献帝",
                "year": 189
        },
        {
                "text": "迁都长安",
                "year": 190
        },
        {
                "text": "被吕布刺杀",
                "year": 192
        }
]
    },
]


# ── DeepSeek AI Engine ──────────────────────────────────────────────

class DeepSeekAI:
    """DeepSeek API-powered answerer. Falls back gracefully on any failure."""

    API_URL = "https://api.deepseek.com/chat/completions"
    MODEL = "deepseek-chat"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")

    @property
    def available(self):
        return bool(self.api_key)

    def answer(self, character, question, qa_log=None):
        if not self.available:
            return None

        history = ""
        if qa_log:
            lines = []
            for item in qa_log[-6:]:  # last 6 rounds for context
                lines.append(f"玩家问：{item['q']}")
                lines.append(f"你回答：{item['a']}")
            history = "\n".join(lines)

        system_prompt = f"""你是一个猜人物游戏的裁判，你必须在回答中严格保密。

你心中的人物是：{character['name']}
以下资料仅供你判断用，绝不可让玩家察觉：
{character['bio']}

【核心铁律（违反任何一条即游戏失败）】
⛔ 绝不能在"不是"后追加任何解释——只回答"不是"二字
⛔ 绝不能在"是"后追加任何解释——只回答"是"二字
⛔ 绝不用"是也不是"暗示身份特征（如"被讨伐的""群雄阵营""割据一方""反叛朝廷"等标签性词汇）
⛔ 绝不能提及人物名字/字号/绰号/典故/代表事件/代表作
⛔ 绝不能评价人物（如"很出名""很厉害""比较冷门"）
⛔ 对于时间/年代/年份问题、阵营归属问题、性别问题等客观事实，回答"是"或"不是"即可
⛔ 当被问及两个事件发生的先后顺序时，如果只知道大概年份但不知精确时间顺序（同一年内先后），必须回答"无法判断"

【二选一问题（含"还是"时）】
当玩家问"A还是B"时，直接给出选项词，不套"是"或"不是"：
{{"type":"choice","text":"之前"}}
{{"type":"choice","text":"偏文"}}

【回答格式】
是非题——直接答"是"或"不是"
二选一题——输出 choice 类型
模棱两可——用 maybe 加最模糊泛词

纯JSON输出：
{{"type":"yes","text":"是"}}
{{"type":"no","text":"不是"}}
{{"type":"choice","text":"偏文"}}
{{"type":"maybe","text":"是也不是，偏后期"}}
{{"type":"unknown","text":"无法判断，换种方式问吧"}}"""

        user_msg = f"玩家提问：{question}"
        if history:
            user_msg = f"对话历史：\n{history}\n\n{user_msg}"

        try:
            data = json_lib.dumps({
                "model": self.MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.3,
                "max_tokens": 150,
                "stream": False,
            }).encode("utf-8")

            req = Request(self.API_URL, data=data, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            })
            with urlopen(req, timeout=15) as resp:
                body = json_lib.loads(resp.read().decode("utf-8"))
                content = body["choices"][0]["message"]["content"].strip()

            # Parse JSON from response (strip markdown fences if present)
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"```\s*$", "", content)
            result = json_lib.loads(content)

            # Normalize types
            t = result.get("type", "unknown")
            if t in ("yes", "no", "maybe", "unknown", "choice"):
                return {"type": t, "text": result.get("text", "")}
            return None

        except (URLError, OSError, ValueError, KeyError, json_lib.JSONDecodeError) as e:
            print(f"[DeepSeek] API error: {e}")
            return None


# ── Question-Answer Engine ──────────────────────────────────────────

class CharacterEngine:
    def __init__(self, api_key=None):
        self.characters = CHARACTERS
        self.ai = DeepSeekAI(api_key) if api_key else None
        for c in self.characters:
            if "qa_predefined" not in c:
                c["qa_predefined"] = self._generate_qa(c)

    def pick_random(self, category=None):
        chars = self.characters if not category else [c for c in self.characters if c["category"] == category]
        if not chars:
            chars = self.characters
        return random.choice(chars)

    def answer(self, character, question, qa_log=None):
        question = question.strip()
        if not question:
            return {"type": "unknown", "text": "请提出一个问题"}

        # 1. Guess detection (always local — fast + prevents AI leaks)
        guess = self._check_guess(question, character)
        if guess is not None:
            return guess

        # 2. Local deterministic checks (override AI for factual questions)
        local = self._local_fact(question, character)
        if local:
            return local

        # 3. Try AI (DeepSeek) first if available
        if self.ai and self.ai.available:
            result = self.ai.answer(character, question, qa_log)
            if result:
                return result

        # 4. Fall back to local fuzzy + keyword matching
        fuzzy = self._fuzzy_match(question, character)
        if fuzzy:
            return {"type": "answer", "text": fuzzy}

        kw = self._keyword_match(question, character)
        if kw:
            return {"type": "answer", "text": kw}

        return {"type": "unknown", "text": "这个问题难以判断，换种方式问吧"}

    def _local_fact(self, question, character):
        """Deterministic fact checks that override AI. Returns answer dict or None."""
        death = character.get("death_year")
        born = character.get("born_year")
        q = question

        # ── Binary choice questions (A还是B) ──
        if "还是" in q:

            # Time comparison: "死于234年之前还是之后"
            time_m = re.search(r"(\d+)\s*年.*还是.*(?:之前|之后|以前|以后)", q)
            if time_m and death:
                year = int(time_m.group(1))
                if re.search(r"(?:之前|以前|早于)", q.split("还是")[0]):
                    return {"type": "choice", "text": f"{year}年之前死的" if death < year else f"{year}年之后死的" if death > year else f"就是{year}年死的"}
                else:
                    # "A还是B" where the options are in the later part
                    pass

            # "死于X年之前还是之后" simplified
            time_m2 = re.search(r"(\d+)\s*年", q)
            if time_m2 and death:
                year = int(time_m2.group(1))
                if "之前" in q and "之后" in q:
                    if death < year:
                        return {"type": "choice", "text": f"{year}年之前死的"}
                    elif death > year:
                        return {"type": "choice", "text": f"{year}年之后死的"}
                    else:
                        return {"type": "choice", "text": f"就是{year}年死的"}

            # "偏文还是偏武"
            f = character.get("flags", {})
            if re.search(r"文.*还是.*武|武.*还是.*文|文还是武|偏文还是偏武|文将还是武将|文臣还是武将", q):
                if f.get("文武兼备"):
                    return {"type": "choice", "text": "文武兼备"}
                if f.get("是武将") and not f.get("是谋士") and not f.get("是文臣"):
                    return {"type": "choice", "text": "偏武"}
                return {"type": "choice", "text": "偏文"}

            # "前期还是后期" / "早还是晚"
            if re.search(r"(?:前期|早期).*(?:后期|晚期)|(?:后期|晚期).*(?:前期|早期)", q):
                if death and death <= 210:
                    return {"type": "choice", "text": "偏前期"}
                elif death and death >= 230:
                    return {"type": "choice", "text": "偏后期"}
                elif death:
                    return {"type": "choice", "text": "中期"}

        # ── Time comparison (yes/no format) ──
        time_m = re.search(r"(\d+)\s*年", q)
        if time_m:
            year = int(time_m.group(1))
            if death:
                if re.search(r"(?:之前|以前|早于|前于)", q):
                    if death < year:
                        return {"type": "yes", "text": "是"}
                    elif death == year:
                        return {"type": "maybe", "text": f"是也不是，就是{year}年"}
                    else:
                        return {"type": "no", "text": "不是"}
                if re.search(r"(?:之后|以后|晚于|后于)", q):
                    if death > year:
                        return {"type": "yes", "text": "是"}
                    elif death == year:
                        return {"type": "maybe", "text": f"是也不是，就是{year}年"}
                    else:
                        return {"type": "no", "text": "不是"}

        # ── Event timeline comparison ──
        # "张辽斩踏顿的时候，他是否还活着" / "X事件发生时他还活着吗"
        evt_m = re.search(
            r"([\u4e00-\u9fff]{2,4})(?:斩|杀|败|破|灭|擒|诛|征|伐|定|取|夺|平|攻)([\u4e00-\u9fff]{1,4})",
            q)
        if evt_m and death and "还活着" in q or "在(?:他|世)" in q:
            e_subj = evt_m.group(1)  # e.g. "张辽"
            e_text = evt_m.group(0)  # full matched phrase
            # Search all characters for matching event
            evt_year = None
            for c2 in self.characters:
                if c2["name"].startswith(e_subj) or e_subj in c2["name"]:
                    for ev in c2.get("events", []):
                        if any(ch in ev["text"] for ch in evt_m.group(2)):
                            evt_year = ev["year"]
                            break
                if evt_year:
                    break
            if evt_year:
                if death < evt_year:
                    return {"type": "yes", "text": "是"}
                elif death == evt_year:
                    return {"type": "unknown", "text": "无法判断，同一年发生"}
                else:
                    return {"type": "no", "text": "不是"}

        # ── Gender question ──
        if re.search(r"(?:女性|女人|女的|女子|妇人|是女)", q):
            return {"type": "yes", "text": "是"} if character.get("性别") == "女" else {"type": "no", "text": "不是"}
        if re.search(r"(?:男性|男人|男的|男子)", q) and character.get("性别"):
            return {"type": "yes", "text": "是"} if character.get("性别") == "男" else {"type": "no", "text": "不是"}

        # ── Faction question ──
        if re.search(r"(?:魏蜀吴|三国)", q) and not re.search(r"(?:蜀国|魏国|吴国|东吴|蜀汉|曹魏|孙吴|是蜀|是魏|是吴)", q):
            in_three = character["阵营"] in ("蜀", "魏", "吴")
            return {"type": "yes", "text": "是"} if in_three else {"type": "no", "text": "不是"}

        for label, faction in [("蜀", "蜀"), ("魏", "魏"), ("吴", "吴")]:
            if re.search(rf"(?:是{label}|{label}国|{label}汉|东{label}|孙{label}|曹{label}|{label}阵营)", q):
                match = character["阵营"] == faction
                return {"type": "yes", "text": "是"} if match else {"type": "no", "text": "不是"}

        # ── Surname check ──
        surname_m = re.search(r"姓([\u4e00-\u9fff]{1,4})(?:吗|吧|呢|的|啊|$)", q)
        if surname_m:
            raw = surname_m.group(1)
            match = character["name"].startswith(raw) or \
                    any(character["name"].startswith(c) for c in raw)
            return {"type": "yes", "text": "是"} if match else {"type": "no", "text": "不是"}

        return None

    def _check_guess(self, question, character):
        q = question.strip().rstrip("？?!！吗吧呢。，, ")
        names = [character["name"]] + character.get("alias", [])

        for name in names:
            if q == name:
                return {"type": "correct", "text": "猜对了！"}
            if q == f"他是{name}":
                return {"type": "correct", "text": "猜对了！"}
            if q == f"是{name}":
                return {"type": "correct", "text": "猜对了！"}
            if q.startswith("他是") and q.endswith("吗"):
                inner = q[2:-1]
                if inner == name:
                    return {"type": "correct", "text": "猜对了！"}
            # Partial match for guess-like patterns
            if re.search(rf"(?:我猜是|猜他是|就是)({re.escape(name)})", q):
                return {"type": "correct", "text": "猜对了！"}

        # Check if user is guessing a wrong name
        guess_patterns = [r"^我猜是(.+)", r"^猜他是(.+)", r"^就是(.+)", r"^(.+)吗$"]
        for pat in guess_patterns:
            m = re.match(pat, q)
            if m:
                guessed = m.group(1).strip()
                if guessed and len(guessed) <= 4 and not any(kw in guessed for kw in ["是", "不", "有", "在", "当", "死"]):
                    for name in names:
                        if guessed == name or guessed in character.get("alias", []):
                            return {"type": "correct", "text": "猜对了！"}
                    # It looks like a guess but didn't match
                    return {"type": "wrong_guess", "text": "不是"}

        return None

    def _fuzzy_match(self, question, character):
        best_ratio = 0.58
        best_answer = None
        for q_template, answer in character.get("qa_predefined", {}).items():
            ratio = SequenceMatcher(None, question, q_template).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_answer = answer
        return best_answer

    def _keyword_match(self, question, character):
        f = character.get("flags", {})

        # Score-based matching: count keyword hits per pattern
        patterns = [
            (["蜀", "蜀国", "蜀汉"], lambda: _bool_ans(cmp("蜀"), False)),  # uses 阵营 below
        ]

        # Direct 阵营 check
        lower_q = question.lower()
        for faction, name in [("蜀", "蜀"), ("魏", "魏"), ("吴", "吴")]:
            if any(kw in question for kw in [f"{name}国", f"{name}汉", f"{name}魏", name]):
                if character["阵营"] == faction:
                    return "是"
                else:
                    return "不是"
            if any(kw in question for kw in ["东吴", "孙吴", "江东"]) and character["阵营"] == "吴":
                # Context: if asking about Wu, check if character is Wu
                return "是"

        # Check for negation: "不是X吧", "不是X的吗"
        negate = bool(re.search(r"不是|并非|没有", question))

        # ── Flag-based patterns ──
        flag_map = [
            (["君主", "主公", "皇帝", "称帝", "开国", "建国", "君主吗", "是皇帝"], "是君主"),
            (["武将", "上阵", "砍人", "杀敌", "冲锋", "打仗", "勇猛", "猛将", "武将吗", "是武将", "上战场"], "是武将"),
            (["文臣", "文官", "内政", "文职", "文臣吗", "是文臣", "管政务"], "是文臣"),
            (["谋士", "军师", "智囊", "出谋划策", "运筹帷幄", "谋士吗", "是谋士", "策划"], "是谋士"),
            (["文武兼备", "文武双全", "既文又武", "能文能武", "文武", "文还是武", "偏文还是偏武", "文将还是武将"], "文武兼备"),
            (["大都督", "都督"], "当过大都督"),
            (["丞相", "宰辅"], "当过丞相"),
            (["跳槽", "改换门庭", "换主", "叛变", "投降", "背叛", "易主"], "改换门庭"),
            (["从一而终"], "改换门庭"),  # special: negate for this one
            (["女性", "女人", "女的", "女子", "妇人"], "是女性"),
            (["称帝", "做了皇帝", "当过皇帝", "登基"], "称过帝"),
        ]

        for keywords, flag in flag_map:
            if any(kw in question for kw in keywords):
                value = f.get(flag, False)
                if flag == "改换门庭" and "从一而终" in question:
                    value = not value  # 从一而终 means NOT 改换门庭
                if negate:
                    value = not value
                if flag == "文武兼备" and any(kw in question for kw in ["文还是武", "偏文还是偏武", "文将还是武将"]):
                    # Either/or question about 文武
                    if f.get("文武兼备"):
                        return "是也不是，文武兼备"
                    if f.get("是武将"):
                        return "偏武"
                    if f.get("是谋士") or f.get("是文臣"):
                        return "偏文"
                    return "无法判断"
                return "是" if value else "不是"

        # ── Time-based questions ──
        death_year_keywords = ["234年", "234"]
        if any(kw in question for kw in death_year_keywords):
            death = character.get("death_year")
            if death is None:
                return "无法判断"
            if any(kw in question for kw in ["之前", "以前", "早于"]):
                if death < 234:
                    return "是"
                elif death == 234:
                    return "是也不是，就是234年"
                else:
                    return "不是"
            if any(kw in question for kw in ["之后", "以后", "晚于"]):
                if death > 234:
                    return "是"
                elif death == 234:
                    return "是也不是，就是234年"
                else:
                    return "不是"

        # ── Age/death related ──
        if any(kw in question for kw in ["英年早逝", "早逝", "早死", "短命", "早亡", "夭折", "英年"]):
            born = character.get("born_year")
            death = character.get("death_year")
            if born and death and (death - born) < 45:
                return "是"
            elif born and death:
                return "不是"
            return "无法判断"

        # ── "魏蜀吴阵营的吗" generic ──
        if any(kw in question for kw in ["魏蜀吴", "三国", "阵营"]) and not any(kw in question for kw in
                                                                                ["蜀国", "魏国", "吴国", "东吴"]):
            if character["阵营"] in ["蜀", "魏", "吴"]:
                return "是"
            return "不是"

        return None

    def _generate_qa(self, character):
        qa = {}
        c = character
        f = c.get("flags", {})

        # 阵营
        for faction in ["蜀", "魏", "吴"]:
            truth = c["阵营"] == faction
            for q in [f"他是{faction}国人吗", f"他是{faction}国的吗",
                       f"是{faction}国的人吗", f"是{faction}的吗",
                       f"是{faction}人吗"]:
                qa[q] = "是" if truth else "不是"

        # 阵营否定
        for faction in ["蜀", "魏", "吴"]:
            if c["阵营"] != faction:
                qa[f"他不是{faction}国人吧"] = "是"  # confirming the negation

        # Generic 三国/魏蜀吴
        qa["他是魏蜀吴阵营的吗"] = "是" if c["阵营"] in ["蜀", "魏", "吴"] else "不是"
        qa["是三国的人吗"] = "是" if c["阵营"] in ["蜀", "魏", "吴"] else "不是"

        # Flags
        flag_map = {
            "是君主": ["他是君主吗", "他是主公吗", "他当过皇帝吗", "他称过帝吗"],
            "是武将": ["他是武将吗", "他上阵砍人吗", "他上阵杀敌吗", "他去打仗吗"],
            "是文臣": ["他是文臣吗", "他是文官吗"],
            "是谋士": ["他是谋士吗", "他是军师吗", "他出谋划策吗"],
            "文武兼备": ["他文武兼备吗", "他文武双全吗", "他偏文还是偏武",
                      "他是文将还是武将"],
            "当过大都督": ["他当过大都督吗", "他当过都督吗"],
            "当过丞相": ["他当过丞相吗"],
            "改换门庭": ["他改换过门庭吗", "他换过主吗", "他跳过槽吗",
                       "他从一而终吗", "他叛变过吗", "他投降过吗"],
            "是女性": ["他是女性吗", "他是女人吗", "他是女的吗"],
            "称过帝": ["他称过帝吗", "他当过皇帝吗"],
        }
        for flag, qs in flag_map.items():
            value = f.get(flag, False)
            for q in qs:
                if flag == "改换门庭":
                    if "从一而终" in q:
                        qa[q] = "不是" if value else "是"
                    else:
                        qa[q] = "是" if value else "不是"
                elif flag == "文武兼备" and ("偏文还是偏武" in q or "文将还是武将" in q):
                    if f.get("文武兼备"):
                        qa[q] = "是也不是，文武兼备"
                    elif f.get("是武将"):
                        qa[q] = "偏武"
                    elif f.get("是谋士") or f.get("是文臣"):
                        qa[q] = "偏文"
                else:
                    qa[q] = "是" if value else "不是"

        # Time questions
        death = c.get("death_year")
        if death:
            if death < 234:
                qa["他死于234年之前吗"] = "是"
                qa["他死于234年之后吗"] = "不是"
            elif death > 234:
                qa["他死于234年之前吗"] = "不是"
                qa["他死于234年之后吗"] = "是"
            else:
                qa["他死于234年之前吗"] = "是也不是，就是234年"
                qa["他死于234年之后吗"] = "是也不是，就是234年"

        # Early death
        born = c.get("born_year")
        if death and born:
            early = (death - born) < 45
            for q in ["他是英年早逝吗", "他短命吗", "他早逝吗"]:
                qa[q] = "是" if early else "不是"

        return qa


def _bool_ans(value, negate=False):
    if negate:
        return "不是" if value else "是"
    return "是" if value else "不是"


def cmp(val):
    """Used in lambda patterns for comparing character attributes."""
    return val
