import sys
from .. import console

def check_variables():
    if console.API_ID == 0:
        console.logs(__name__).info("❌ 'API ID' - Not found❗")
        sys.exit()
    if not console.API_HASH:
        console.logs(__name__).info("❌ 'API_HASH' - Not found❗")
        sys.exit()
    if not console.BOT_TOKEN:
        console.logs(__name__).info("❌ 'BOT_TOKEN' - Not found❗")
        sys.exit()
    if (
        not console.STRING1
        and not console.STRING2
        and not console.STRING3
        and not console.STRING4
        and not console.STRING5
    ):
        console.logs(__name__).info("❌ 'STRING_SESSION' - Not found❗")
        sys.exit()
    if not console.MONGO_URL:
        console.logs(__name__).info("❌ 'MONGO_URL' - Not found❗")
        sys.exit()
    if console.OWNER_ID == 0:
        console.logs(__name__).info("❌ 'OWNER_ID' - Not found❗")
        sys.exit()
    if console.LOG_GROUP_ID == 0:
        console.logs(__name__).info("❌ 'LOG_GROUP_ID' - Not found❗")
        sys.exit()

check_variables()
