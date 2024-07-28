from pathlib import Path
import silly
import sillyorm

if __name__ == "__main__":
    conn = sillyorm.dbms.sqlite.SQLiteConnection("data.db", check_same_thread=False)
    silly.main.init(conn)

    silly_mod_path = str(Path(silly.__file__).parent / "data" / "modules")
    silly.modload.set_module_paths([silly_mod_path, "./"])
    silly.modload.load_module("autoreload", silly.main.env)

    silly.main.run()
