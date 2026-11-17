# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
import math
ClientSystem = clientApi.GetClientSystemCls()


class Main(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        namespace = clientApi.GetEngineNamespace()
        system_name = clientApi.GetEngineSystemName()

        self.barrelflySwitch = True

        self.TORAD = math.pi / 180
        self.TODEG = 1 / self.TORAD
        self.player_comp = clientApi.GetEngineCompFactory().CreatePlayer(clientApi.GetLocalPlayerId())
        self.camera_comp = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
        self.operation_comp = clientApi.GetEngineCompFactory().CreateOperation(clientApi.GetLevelId())
        self.neteaseWindowComp = None
        self.settingInst = None
        self.switchPanel = None
        self.flyHUDPanel = None
        self._uiReady = False
        self._destroyed = False
        self._dragBeforeFlight = None
        self._gyroLastTimestamp = None
        self._gyroSensorActive = False
        self.flightRotation = None

        self.tick = 0
        self.lt = [0.0,0.0]
        self.bt = [0.0,0.0]

        self.mouseTurnVec = [0.0, 0.0]

        self.delta = 1.0/30

        self.pitchSmoother = self.SmoothUtil()
        self.yawSmoother = self.SmoothUtil()
        self.rollSmoother = self.SmoothUtil()

        self.facing = None
        self.left = None

        self.config_comp = clientApi.GetEngineCompFactory().CreateConfigClient(clientApi.GetLevelId())
        #设置配置数据
        self.linminValue = 0.0
        self.strengValue = 0.0
        self.openYOverturn = False
        self.gyroControl = False
        rollConfigDict = self.config_comp.GetConfigData("barrelroll_rollconfig_rolldata", True)
        if rollConfigDict:
            self.linminValue = rollConfigDict["linminValue"]
            self.strengValue = rollConfigDict["strengthValue"]
            self.openYOverturn = rollConfigDict["openYOverturn"]
            self.gyroControl = rollConfigDict.get("gyroControl", False)
        else:
            self.linminValue = 1.8
            self.strengValue = 4.0
            self.openYOverturn = False
            self.gyroControl = False
            data = {
                "linminValue": 1.8,
                "strengthValue": 4.0,
                "openYOverturn": False,
                "gyroControl": False
            }
            #保存一下数据
            self.config_comp.SetConfigData("barrelroll_rollconfig_rolldata", data, True)

        #设置配置数据
        self.HUDScreen = False
        self.angleshow = False
        self.flyHUDshow = False
        self.elytradurabilityshow = False
        self.flyspeedshow = False
        self.directionshow = False
        self.mapshow = False
        flyShowconfigDict = self.config_comp.GetConfigData("barrelroll_flyshowconfig_flyshowdata", True)
        if flyShowconfigDict:
            self.HUDScreen = flyShowconfigDict["HUDScreen"]
            self.angleshow = flyShowconfigDict["angleshow"]
            self.flyHUDshow = flyShowconfigDict["flyHUDshow"]
            self.elytradurabilityshow = flyShowconfigDict["elytradurability"]
            self.flyspeedshow = flyShowconfigDict["flyspeedshow"]
            self.directionshow = flyShowconfigDict["directionshow"]
            self.mapshow = flyShowconfigDict["mapshow"]
        else:
            data = {
                "HUDScreen": False,
                "angleshow": False,
                "flyHUDshow": False,
                "elytradurability": False,
                "flyspeedshow": False,
                "directionshow": False,
                "mapshow": False
            }
            self.config_comp.SetConfigData("barrelroll_flyshowconfig_flyshowdata", data, True)

        self.ListenForEvent(namespace, system_name, "UiInitFinished", self, self.UiInit)#监听处理UI
        self.ListenForEvent(namespace, system_name, "PushScreenEvent", self, self.onScreenPushed)
        self.ListenForEvent(namespace, system_name, "GyroSensorChangedClientEvent", self, self.onGyroSensorChanged)
        self.ListenForEvent('BRServer', 'BarrelRollServer', "OpenSetting", self, self.openSettingPanel)
            
    def saveConfig(self):
        data = {
            "linminValue": self.linminValue,
            "strengthValue": self.strengValue,
            "openYOverturn": self.openYOverturn,
            "gyroControl": self.gyroControl
        }
        self.config_comp.SetConfigData("barrelroll_rollconfig_rolldata", data, True)
    
    def saveflyHUDConfig(self):
        data = {
            "HUDScreen": self.HUDScreen,
            "angleshow": self.angleshow,
            "flyHUDshow": self.flyHUDshow,
            "elytradurability": self.elytradurabilityshow,
            "flyspeedshow": self.flyspeedshow,
            "directionshow": self.directionshow,
            "mapshow": self.mapshow
        }
        self.config_comp.SetConfigData("barrelroll_flyshowconfig_flyshowdata", data, True)

    def openSettingPanel(self, event=None, source=None):
        if self._destroyed or not self._uiReady:
            return False
        if self.settingInst is None:
            self.registerModSettings()
        if self.neteaseWindowComp is None or self.settingInst is None:
            return False
        self.resetFlight()
        return self.neteaseWindowComp.OpenSettingUI()

    def registerModSettings(self):
        if self._destroyed or self.settingInst is not None:
            return
        self.neteaseWindowComp = clientApi.GetEngineCompFactory().CreateNeteaseWindow(clientApi.GetLevelId())
        self.settingInst = self.neteaseWindowComp.RegisterSettingInst(
            "BarrelRollScript", "滚筒飞行", None)
        if self.settingInst is None:
            return
        self.settingInst.Clear()

        # 官方通用设置滑块只支持整数，使用档位映射保留原来的 0.1 精度。
        (self.settingInst
         .AddText("barrel_section", "翻滚飞行设置", 0)
         .AddText("barrel_slider_hint", "灵敏度每档0.1（1.0～2.5）；回正强度每档0.1（2.0～6.0）", 1)
         .AddText("barrel_current_values", self.getRollValueText(), 2)
         .AddSlider("roll_sensitivity", "操作灵敏度", 15,
                    self.onRollSliderChanged, 3, self._linminToSlider())
         .AddSlider("roll_strength", "自动回正强度", 40,
                    self.onRollSliderChanged, 4, self._strengthToSlider())
         .AddToggle("invert_y", "Y轴反转", self.onSettingToggleChanged,
                    5, self.openYOverturn)
         .AddToggle("gyro_control", "陀螺仪控制（仅移动端）", self.onSettingToggleChanged,
                    6, self.gyroControl)
         .AddButton("reset_roll", "翻滚参数", "恢复默认",
                    self.onResetRollSettings, 7)
         .AddText("fly_hud_section", "飞行信息显示设置", 10)
         .AddToggle("show_angle", "角度显示", self.onSettingToggleChanged,
                    11, self.angleshow)
         .AddToggle("show_fly_hud", "飞行HUD显示", self.onSettingToggleChanged,
                    12, self.flyHUDshow)
         .AddToggle("show_elytra_durability", "鞘翅耐久显示", self.onSettingToggleChanged,
                    13, self.elytradurabilityshow)
         .AddToggle("show_fly_speed", "飞行速度显示", self.onSettingToggleChanged,
                    14, self.flyspeedshow)
         .AddToggle("show_direction", "方向显示", self.onSettingToggleChanged,
                    15, self.directionshow)
         .AddToggle("show_map", "地图显示", self.onSettingToggleChanged,
                    16, self.mapshow)
         .AddToggle("use_hud_screen", "使用HUD界面显示", self.onSettingToggleChanged,
                    17, self.HUDScreen)
         .AddButton("show_license", "开源许可", "查看说明",
                    self.onShowLicense, 20))
        self.syncModSettingValues()

    def _linminToSlider(self):
        return self.clampInt(round((self.linminValue - 1.0) * 10), 0, 15)

    def _strengthToSlider(self):
        return self.clampInt(round((self.strengValue - 2.0) * 10), 0, 40)

    def clampInt(self, value, minValue, maxValue):
        return max(minValue, min(maxValue, int(value)))

    def getRollValueText(self):
        return "当前：灵敏度 %.1f，回正强度 %.1f" % (self.linminValue, self.strengValue)

    def syncModSettingValues(self):
        if self.settingInst is None:
            return
        (self.settingInst
         .SetSliderDefault("roll_sensitivity", self._linminToSlider())
         .SetSliderValue("roll_sensitivity", self._linminToSlider())
         .SetSliderDefault("roll_strength", self._strengthToSlider())
         .SetSliderValue("roll_strength", self._strengthToSlider())
         .SetText("barrel_current_values", self.getRollValueText())
         .SetToggleDefault("invert_y", self.openYOverturn)
         .SetToggleValue("invert_y", self.openYOverturn)
         .SetToggleDefault("gyro_control", self.gyroControl)
         .SetToggleValue("gyro_control", self.gyroControl)
         .SetToggleDefault("show_angle", self.angleshow)
         .SetToggleValue("show_angle", self.angleshow)
         .SetToggleDefault("show_fly_hud", self.flyHUDshow)
         .SetToggleValue("show_fly_hud", self.flyHUDshow)
         .SetToggleDefault("show_elytra_durability", self.elytradurabilityshow)
         .SetToggleValue("show_elytra_durability", self.elytradurabilityshow)
         .SetToggleDefault("show_fly_speed", self.flyspeedshow)
         .SetToggleValue("show_fly_speed", self.flyspeedshow)
         .SetToggleDefault("show_direction", self.directionshow)
         .SetToggleValue("show_direction", self.directionshow)
         .SetToggleDefault("show_map", self.mapshow)
         .SetToggleValue("show_map", self.mapshow)
         .SetToggleDefault("use_hud_screen", self.HUDScreen)
         .SetToggleValue("use_hud_screen", self.HUDScreen))

    def onRollSliderChanged(self, key, value):
        value = int(value)
        if key == "roll_sensitivity":
            self.linminValue = round(1.0 + self.clampInt(value, 0, 15) * 0.1, 1)
        elif key == "roll_strength":
            self.strengValue = round(2.0 + self.clampInt(value, 0, 40) * 0.1, 1)
        self.saveConfig()
        if self.settingInst is not None:
            self.settingInst.SetText("barrel_current_values", self.getRollValueText())

    def onSettingToggleChanged(self, key, value):
        value = bool(value)
        if key == "invert_y":
            self.openYOverturn = value
            self.saveConfig()
            return
        if key == "gyro_control":
            self.setGyroControlEnabled(value)
            return
        attributes = {
            "show_angle": "angleshow",
            "show_fly_hud": "flyHUDshow",
            "show_elytra_durability": "elytradurabilityshow",
            "show_fly_speed": "flyspeedshow",
            "show_direction": "directionshow",
            "show_map": "mapshow",
            "use_hud_screen": "HUDScreen"
        }
        attribute = attributes.get(key)
        if attribute is None:
            return
        setattr(self, attribute, value)
        self.saveflyHUDConfig()
        self.refreshFlyHUD()

    def onResetRollSettings(self, key, value):
        self.linminValue = 1.8
        self.strengValue = 4.0
        self.openYOverturn = False
        self.setGyroControlEnabled(False, False)
        self.saveConfig()
        self.syncModSettingValues()
        gameComp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        gameComp.SetTipMessage("翻滚参数已恢复默认")

    def onShowLicense(self, key, value):
        self.neteaseWindowComp.CloseSettingUI()
        comp = clientApi.GetEngineCompFactory().CreateTextNotifyClient(clientApi.GetLevelId())
        comp.SetLeftCornerNotify(clientApi.GenerateColor("RED") + "终极翻滚+飞行信息显示组件使用GPL 3.0许可开源")
        comp.SetLeftCornerNotify(clientApi.GenerateColor("RED") + "组件开源地址:https://github.com/HXzhitang/netease-MC-addon-Barrel-Roll")

    def refreshFlyHUD(self):
        if self.flyHUDPanel is not None:
            self.flyHUDPanel.fleshHUDShow()

    def UiInit(self, event):
        if self._destroyed:
            return
        self._uiReady = False
        self.resetFlight()
        clientApi.RegisterUI('BarrelUI', 'barrelswitch', 'BarrelRollScript.ui.BarrelSwitchUI.Main', 'barrelSwitch.main')
        clientApi.RegisterUI('BarrelUI', 'flyshowHUD', 'BarrelRollScript.ui.FlyHUDUI.Main', 'fly_HUD.main')
        self.switchPanel = clientApi.GetUI('BarrelUI', 'barrelswitch')
        if self.switchPanel is None:
            self.switchPanel = clientApi.CreateUI('BarrelUI', 'barrelswitch', {"isHud": 1, "client": self})
        self.flyHUDPanel = clientApi.GetUI('BarrelUI', 'flyshowHUD')
        if self.flyHUDPanel is None:
            self.flyHUDPanel = clientApi.CreateUI('BarrelUI', 'flyshowHUD', {"isHud": 1, "client": self})
        self._uiReady = True
        self.registerModSettings()
        self.updateGyroSensorState()

    def onScreenPushed(self, event):
        if event.get('screenName') != 'hud_screen':
            self.resetFlight()

    def isInputBlocked(self):
        if not self._uiReady:
            return True
        # GetTopUI 包括背包、暂停、聊天及其他模组 PushScreen 的页面。
        return clientApi.GetTopUI() != 'hud_screen'

    def resetFlight(self):
        rotation = self.flightRotation
        previousDrag = self._dragBeforeFlight
        self.facing = None
        self.left = None
        self.flightRotation = None
        self._dragBeforeFlight = None
        self._gyroLastTimestamp = None
        self.lt = [0.0, 0.0]
        self.bt = [0.0, 0.0]
        self.mouseTurnVec = [0.0, 0.0]
        self.pitchSmoother.clear()
        self.yawSmoother.clear()
        self.rollSmoother.clear()
        # 仅恢复本系统接管的状态，保留进入前其他组件的拖屏设置。
        try:
            if previousDrag is not None:
                self.operation_comp.SetCanDrag(previousDrag)
        finally:
            if rotation is not None:
                self.camera_comp.SetCameraRotation((rotation[0], rotation[1], 0.0))

    # 监听引擎OnScriptTickClient事件，引擎会执行该tick回调，1秒钟30帧
    def OnTickClient(self):
        """
        Driven by event, One tick way
        """
        pass

    # 被引擎直接执行的父类的重写函数，引擎会执行该Update回调，1秒钟30帧
    def Update(self):
        if self._destroyed:
            return
        if (not self.barrelflySwitch or not self.player_comp.isGliding() or
                self.isInputBlocked()):
            self.resetFlight()
            return
        if self.facing is None or self.left is None:
            # 仅在重新进入飞行时读取相机，后续积分使用脚本姿态。
            rotation = self.camera_comp.GetCameraRotation()
            if not self.isFiniteVector(rotation):
                self.resetFlight()
                return
            self.facing = self.norm3D(clientApi.GetDirFromRot((rotation[0], rotation[1])))
            left = self.getAssumedLeft(rotation[1])
            self.left = self.norm3D(self.rotateAxisAngle(left, self.facing,
                                                       -rotation[2] * self.TORAD))
            self.flightRotation = self.getFlightRotation(self.facing, self.left)
            if self.flightRotation is None:
                self.resetFlight()
                return
            self.lt = [0.0, 0.0]
            self.bt = [0.0, 0.0]
            self._dragBeforeFlight = self.operation_comp.IsCanDrag()
            self.operation_comp.SetCanDrag(False)

        # 保留当前触摸输入方案，只修复进入/退出时的基线管理。
        touchX, touchY = clientApi.GetTouchPos()
        self.lt = [touchX, touchY]
        if self.lt != [0.0, 0.0] and self.bt != [0.0, 0.0]:
            move = [self.lt[0] - self.bt[0], self.lt[1] - self.bt[1]]
            if math.sqrt(move[0]**2 + move[1]**2) <= 120:
                self.changeElytraLook(move[1]*self.linminValue, 0, move[0]*self.linminValue)
        else:
            self.mouseTurnVec = [0.0, 0.0]
            self.changeElytraLook(0, 0, 0)
        if self.flightRotation is not None:
            self.bt = [touchX, touchY]

    def Destroy(self):
        self._destroyed = True
        self._uiReady = False
        self.resetFlight()
        namespace = clientApi.GetEngineNamespace()
        system_name = clientApi.GetEngineSystemName()

        self.UnListenForEvent(namespace, system_name, "UiInitFinished", self, self.UiInit)#监听处理UI
        self.UnListenForEvent(namespace, system_name, "PushScreenEvent", self, self.onScreenPushed)
        self.UnListenForEvent(namespace, system_name, "GyroSensorChangedClientEvent", self, self.onGyroSensorChanged)
        self.UnListenForEvent('BRServer', 'BarrelRollServer', "OpenSetting", self, self.openSettingPanel)
        if self._gyroSensorActive:
            clientApi.ToggleGyroSensor(False)
            self._gyroSensorActive = False
        for panel in (self.switchPanel, self.flyHUDPanel):
            if panel is not None:
                panel.SetRemove()
        self.settingInst = None
        self.neteaseWindowComp = None
        self.switchPanel = None
        self.flyHUDPanel = None

    def setGyroControlEnabled(self, enabled, shouldSave=True):
        self.gyroControl = bool(enabled)
        self._gyroLastTimestamp = None
        self.updateGyroSensorState()
        if shouldSave:
            self.saveConfig()

    def updateGyroSensorState(self):
        shouldEnable = self.gyroControl and not self._destroyed
        if shouldEnable:
            self._gyroSensorActive = bool(clientApi.ToggleGyroSensor(True))
            if self._gyroSensorActive:
                # 文档要求每次开启采集后重新设置上报频率。
                clientApi.SetGyroSensorReportRate(30)
        else:
            if self._gyroSensorActive:
                clientApi.ToggleGyroSensor(False)
            self._gyroSensorActive = False

    def onGyroSensorChanged(self, event):
        timestamp = event.get("timestamp")
        if timestamp is None:
            return
        timestamp = float(timestamp)
        previousTimestamp = self._gyroLastTimestamp
        self._gyroLastTimestamp = timestamp
        if (not self.gyroControl or self._destroyed or not self._uiReady or
                not self.barrelflySwitch or not self.player_comp.isGliding() or
                self.isInputBlocked() or self.facing is None or self.left is None):
            return
        if previousTimestamp is None:
            return
        elapsed = timestamp - previousTimestamp
        if elapsed <= 0.0 or elapsed > 0.25:
            return

        screenX, screenY, screenZ = self.getScreenGyroRates(
            float(event.get("xDiff", 0.0)),
            float(event.get("yDiff", 0.0)),
            float(event.get("zDiff", 0.0)),
            int(event.get("orientation", 0)))
        # 角速度乘以事件间隔得到转角，再换算为摄像机控制输入。
        scale = (self.linminValue / 1.8) * elapsed * self.TODEG / 0.45
        gyroDelta = [-screenX * scale, -screenY * scale, -screenZ * scale]
        gyroDelta = self.applyInvertPitch(gyroDelta, self.openYOverturn)
        self.changeElytraLookDirectly(gyroDelta)

    def getScreenGyroRates(self, xRate, yRate, zRate, orientation):
        if orientation == 1:
            return (yRate, -xRate, zRate)
        if orientation == 2:
            return (-xRate, -yRate, zRate)
        if orientation == 3:
            return (-yRate, xRate, zRate)
        return (xRate, yRate, zRate)

    def changeElytraLook(self, pitch, yaw, roll):
        rotDelta = [pitch, yaw, roll]
        
        rotDelta = self.sensitivity(rotDelta)
        rotDelta = self.applyInvertPitch(rotDelta, self.openYOverturn)#Y反转
        rotDelta = self.smooth(self.pitchSmoother, self.yawSmoother, self.rollSmoother, rotDelta)
        rotDelta = self.banking(rotDelta)
        self.changeElytraLookDirectly(rotDelta)

    def changeElytraLookDirectly(self, rot):
        pitch = rot[0]
        yaw = rot[1]
        roll = rot[2]

        #pitch
        self.facing = self.norm3D(self.rotateAxisAngle(self.facing, self.left, -0.45 * pitch * self.TORAD))
        #yaw
        up = self.crossProduct(self.facing, self.left)
        self.facing = self.norm3D(self.rotateAxisAngle(self.facing, up, 0.45 * yaw * self.TORAD))
        self.left = self.norm3D(self.rotateAxisAngle(self.left, up, 0.45 * yaw * self.TORAD))
        #roll
        self.left = self.norm3D(self.rotateAxisAngle(self.left, self.facing, 0.45 * roll * self.TORAD))

        self.changeFacingCamera(self.facing, self.left)

    #专门处理摄像机角度的函数
    def changeFacingCamera(self, facingVec, left):
        rotation = self.getFlightRotation(facingVec, left)
        if rotation is None:
            self.resetFlight()
            return
        self.flightRotation = rotation
        self.camera_comp.SetCameraRotation(rotation)

    def getFlightRotation(self, facingVec, left):
        if (not self.isFiniteVector(facingVec) or not self.isFiniteVector(left) or
                self.dotProduct(facingVec, facingVec) < 1E-12 or
                self.dotProduct(left, left) < 1E-12):
            return None
        pitch = -math.asin(self.clamp(facingVec[1], -1.0, 1.0)) * self.TODEG
        yaw = -math.atan2(facingVec[0], facingVec[2]) * self.TODEG
        roll = -self.getRoll(yaw, left)
        return (pitch, yaw, roll)

    def smooth(self, pitchSmoother, yawSmoother, rollSmoother, rot):
        return (
                pitchSmoother.smooth(rot[0], self.delta), 
                yawSmoother.smooth(rot[1], 0.4*self.delta), 
                rollSmoother.smooth(rot[2], self.delta)
                )

    def banking(self, rotDelta):
        # 相机读回值存在插值延迟；使用上一次积分得到的逻辑姿态。
        if self.flightRotation is None:
            return rotDelta
        currentRoll = self.flightRotation[2] * self.TORAD
        #消除误差
        if currentRoll < 2E-5 and currentRoll > -2E-5:
            currentRoll = 0

        strength = 10 * math.cos(self.flightRotation[0] * self.TORAD) * self.strengValue
        dX = math.sin(currentRoll) * strength
        dY = -strength + math.cos(currentRoll) * strength
        if (math.isnan(dX)):
            dX = 0
        if (math.isnan(dY)):
            dY = 0

        return self.addAbsolute(rotDelta, dX * self.delta, dY * self.delta, currentRoll)

    def getRoll(self, yaw, left):
        angle = -math.acos(self.clamp(self.dotProduct(self.getAssumedLeft(yaw), left), -1, 1)) * self.TODEG
        if (left[1] < 0):
            angle *= -1
        return angle

    def clamp(self, value, min, max):
        if value < min:
            return min
        elif value > max:
            return max
        return value
    
    def getAssumedLeft(self, yaw):
        yaw *= self.TORAD
        return (-math.cos(yaw), 0, -math.sin(yaw))

    def rotateAxisAngle(self, v, axis, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c

        x = (c + axis[0]*axis[0]*t) * v[0]
        y = (c + axis[1]*axis[1]*t) * v[1]
        z = (c + axis[2]*axis[2]*t) * v[2]
        tmp1 = axis[0]*axis[1]*t
        tmp2 = axis[2]*s
        y += (tmp1 + tmp2) * v[0]
        x += (tmp1 - tmp2) * v[1]
        tmp1 = axis[0]*axis[2]*t
        tmp2 = axis[1]*s
        z += (tmp1 - tmp2) * v[0]
        x += (tmp1 + tmp2) * v[2]
        tmp1 = axis[1]*axis[2]*t
        tmp2 = axis[0]*s
        z += (tmp1 + tmp2) * v[1]
        y += (tmp1 - tmp2) * v[2]

        return (x, y, z)

    def applyInvertPitch(self, rot, switch):
        if switch:
            return [-rot[0], rot[1], rot[2]]
        return rot

    def addAbsolute(self, rot, x, y, roll):
        cos = math.cos(roll)
        sin = math.sin(roll)
        return [rot[0] - y * cos - x * sin, -(rot[1] - y * sin + x * cos), rot[2]]

    def sensitivity(self, rot):
        return [rot[0]*1, rot[1]*0.4, rot[2]*1]

    def dotProduct(self, vec0, vec1):
        return vec0[0]*vec1[0]+vec0[1]*vec1[1]+vec0[2]*vec1[2]
    
    def crossProduct(self, vec0, vec1):
        return [vec0[1]*vec1[2]-vec0[2]*vec1[1],vec0[2]*vec1[0]-vec0[0]*vec1[2],vec0[0]*vec1[1]-vec0[1]*vec1[0]]

    def addVec(self, vec0, vec1):
        return [vec0[0]+vec1[0], vec0[1]+vec1[1], vec0[2]+vec1[2]]
    
    def mul(self, vec0, num):
        return [vec0[0]*num, vec0[1]*num, vec0[2]*num]
    
    def isFiniteVector(self, vec0):
        return (vec0 is not None and len(vec0) == 3 and
                all(not math.isnan(value) and not math.isinf(value) for value in vec0))

    def norm3D(self, vec0):
        if not self.isFiniteVector(vec0):
            return (0.0, 0.0, 0.0)
        l = vec0[0]**2+vec0[1]**2+vec0[2]**2
        if l >= 1E-12 and not math.isinf(l):
            m = math.sqrt(l)
            return (vec0[0]/m, vec0[1]/m, vec0[2]/m)
        return (0, 0, 0)
    
    def norm2D(self, vec0):
        l = vec0[0]**2+vec0[1]**2
        if l != 0:
            m = math.sqrt(l)
            return (vec0[0]/m, vec0[1]/m)
        return (0, 0)
    
    class SmoothUtil:
        def __init__(self):
            self.actualSum = 0.0
            self.smoothedSum = 0.0
            self.movementLatency = 0.0

        def smooth(self, original, smoother):
            self.actualSum += original
            d = self.actualSum - self.smoothedSum
            e = self.lerp(0.5, self.movementLatency, d)
            f = self.signum(d)
            if (f * d > f * self.movementLatency):
                d = e

            self.movementLatency = e
            self.smoothedSum += d * smoother
            return d * smoother
        
        def clear(self):
            self.actualSum = 0.0
            self.smoothedSum = 0.0
            self.movementLatency = 0.0

        def signum(self, num):
            if num > 0:
                return 1
            elif num < 0:
                return -1
            return 0
        
        def lerp(self, delta, start, end):
            return start + delta * (end - start)
