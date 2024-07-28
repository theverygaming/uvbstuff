from . import routes, kiwi

def module_onload(env):
    env.register_model(kiwi.Kiwi)
    env.register_model(kiwi.KiwiTimeslot)
