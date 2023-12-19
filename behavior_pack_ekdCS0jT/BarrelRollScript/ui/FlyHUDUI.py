# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
import time
import math

ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()


class Main(ScreenNode):
	def __init__(self, namespace, name, param):
		ScreenNode.__init__(self, namespace, name, param)
		self.client_sys = param['client']#获取客户端
		self.AttitudeAngleLabel = "/attitude_angle_label"
		self.speedLabel = "/speed_panel/speed_label"
		self.speedbar = "/speed_panel/speed_progress_bar"
		self.durabilityLabel = "/elytra_durability_panel/durability_label"
		self.durabilitybar = "/elytra_durability_panel/durability_progress_bar"
		self.directionLabel = "/direction_label"
		self.posLabel = "/flyMapPanel/pos_label"
		self.RollHUD = "/HUD_panel/roll_HUD"
		self.YawHUD = "/HUD_panel/yaw_HUD"

		self.player_comp = clientApi.GetEngineCompFactory().CreatePlayer(clientApi.GetLocalPlayerId())

		self.client_sys.ListenForEvent('BRServer', 'BarrelRollServer', 'ReturnDurability', self, self.updateDurability)

		self.tick = 0

		self.timestart = 0
		self.timeend = 0
		self.startpos = (0, 0, 0)
		self.endpos = (0, 0, 0)

	def Create(self):
		self.AttitudeAngleLabelItem = self.GetBaseUIControl(self.AttitudeAngleLabel).asLabel()
		self.speedLabelItem = self.GetBaseUIControl(self.speedLabel).asLabel()
		self.speedbarItem = self.GetBaseUIControl(self.speedbar).asProgressBar()
		self.speedPanelItem = self.GetBaseUIControl("/speed_panel")
		self.durabilityLabelItem = self.GetBaseUIControl(self.durabilityLabel).asLabel()
		self.durabilitybarItem = self.GetBaseUIControl(self.durabilitybar).asProgressBar()
		self.durabilityPanelItem = self.GetBaseUIControl("/elytra_durability_panel")
		self.directionLabelItem = self.GetBaseUIControl(self.directionLabel).asLabel()
		self.mapPanelItem = self.GetBaseUIControl("/flyMapPanel")
		self.posLabelItem = self.GetBaseUIControl(self.posLabel).asLabel()
		self.RollHUDItem = self.GetBaseUIControl(self.RollHUD).asImage()
		self.YawHUDItem = self.GetBaseUIControl(self.YawHUD).asImage()

		self.fleshHUDShow()

	def Destroy(self):
		self.client_sys.UnListenForEvent('BRServer', 'BarrelRollServer', 'ReturnDurability', self, self.updateDurability)

	def OnActive(self):
		pass

	def OnDeactive(self):
		pass

	def Update(self):
		self.tick += 1
		if self.player_comp.isGliding() and self.client_sys.HUDScreen:
			self.SetScreenVisible(True)
			angle = self.client_sys.camera_comp.GetCameraRotation()
			self.AttitudeAngleLabelItem.SetText("俯仰角:"+str(round(angle[0],2))+" 偏航角:"+str(round(angle[1],2))+" 翻滚角:"+str(round(angle[2],2)))
			self.RollHUDItem.Rotate(angle[2])
			self.YawHUDItem.SetFullPosition(axis="y", paramDict={"followType":"parent", "relativeValue":(angle[0]/90)*-0.6})

			#更新方向:
			if angle[1] > -45 and angle[1] <= 45:
				self.directionLabelItem.SetText("-------="+clientApi.GenerateColor("BLUE")+"北"+clientApi.GenerateColor("WHITE")+"=-------")
			elif angle[1] > 45 and angle[1] <= 135:
				self.directionLabelItem.SetText("-------=东=-------")
			elif angle[1] > 135 and angle[1] <= 180 or angle[1] >= -180 and angle[1] <= -135:
				self.directionLabelItem.SetText("-------="+clientApi.GenerateColor("RED")+"南"+clientApi.GenerateColor("WHITE")+"=-------")
			elif angle[1] > -135 and angle[1] <= -45:
				self.directionLabelItem.SetText("-------=西=-------")

			#更新位置:
			pcomp = clientApi.GetEngineCompFactory().CreatePos(clientApi.GetLocalPlayerId())
			ppos =  pcomp.GetPos()
			self.posLabelItem.SetText("x:"+str(round(ppos[0],1))+" y:"+str(round(ppos[1],1))+" z:"+str(round(ppos[2],1)))

			#更新速度:
			if self.tick % 10 == 0:
				self.timestart = time.time()
				self.startpos = pcomp.GetPos()

				l = math.sqrt((self.startpos[0] - self.endpos[0])**2 + (self.startpos[1] - self.endpos[1])**2 + (self.startpos[2] - self.endpos[2])**2)
				speed = round(l / (self.timestart - self.timeend), 2)
				self.speedLabelItem.SetText(str(speed))
				self.speedbarItem.SetValue(speed/40)

				self.endpos = pcomp.GetPos()
				self.timeend = time.time()

			#更新鞘翅耐久:
			if self.tick % 90 == 0:
				self.client_sys.NotifyToServer("GetElytraDurability", {"playerId": clientApi.GetLocalPlayerId()})

		else:
			self.SetScreenVisible(False)

	def updateDurability(self, event):
		durability = event["durability"]
		value = durability / 432.0
		self.durabilitybarItem.SetValue(value)
		self.durabilityLabelItem.SetText(str(durability)+"/432")

	def fleshHUDShow(self):
		#姿态角
		self.AttitudeAngleLabelItem.SetVisible(self.client_sys.angleshow)
		#HUD
		self.RollHUDItem.SetVisible(self.client_sys.flyHUDshow)
		self.YawHUDItem.SetVisible(self.client_sys.flyHUDshow)
		#耐久
		self.durabilityPanelItem.SetVisible(self.client_sys.elytradurabilityshow)
		#速度
		self.speedPanelItem.SetVisible(self.client_sys.flyspeedshow)
		#方向
		self.directionLabelItem.SetVisible(self.client_sys.directionshow)
		#地图
		self.mapPanelItem.SetVisible(self.client_sys.mapshow)
