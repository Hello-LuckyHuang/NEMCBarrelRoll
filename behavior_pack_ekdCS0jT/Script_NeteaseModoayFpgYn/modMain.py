# -*- coding: utf-8 -*-

from mod.common.mod import Mod


@Mod.Binding(name="Script_NeteaseModoayFpgYn", version="0.0.1")
class Script_NeteaseModoayFpgYn(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    def Script_NeteaseModoayFpgYnServerInit(self):
        pass

    @Mod.DestroyServer()
    def Script_NeteaseModoayFpgYnServerDestroy(self):
        pass

    @Mod.InitClient()
    def Script_NeteaseModoayFpgYnClientInit(self):
        pass

    @Mod.DestroyClient()
    def Script_NeteaseModoayFpgYnClientDestroy(self):
        pass
