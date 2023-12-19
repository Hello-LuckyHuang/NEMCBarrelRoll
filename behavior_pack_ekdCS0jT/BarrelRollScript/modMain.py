# -*- coding: utf-8 -*-

from mod.common.mod import Mod
import mod.client.extraClientApi as ClientApi
import mod.server.extraServerApi as ServerApi

@Mod.Binding(name="BarrelRollScript", version="0.0.1")
class BarrelRollScript(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    def BarrelRollScriptServerInit(self):
        ServerApi.RegisterSystem('BRServer', 'BarrelRollServer', 'BarrelRollScript.ServerSys.Main')

    @Mod.DestroyServer()
    def BarrelRollScriptServerDestroy(self):
        pass

    @Mod.InitClient()
    def BarrelRollScriptClientInit(self):
         ClientApi.RegisterSystem('BRClient', 'BarrelRollClient', 'BarrelRollScript.ClientSys.Main')

    @Mod.DestroyClient()
    def BarrelRollScriptClientDestroy(self):
        pass
