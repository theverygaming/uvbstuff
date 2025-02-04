from . import routes, kiwi, menu, views

def module_onload(env):
    env.register_model(kiwi.Kiwi)
    env.register_model(kiwi.KiwiTimeslot)
