# SPDX-License-Identifier: AGPL-3.0-only
import logging
from pathlib import Path
import silly
import sillyorm

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
    )
    conn = sillyorm.dbms.sqlite.SQLiteConnection("db.sqlite3", check_same_thread=False)
    silly.main.init(conn)

    silly_mod_path = str(Path(silly.__file__).parent / "modules")
    silly.modload.add_module_paths([silly_mod_path, "./"])
    silly.modload.load_module("autoreload")

    silly.main.run()
