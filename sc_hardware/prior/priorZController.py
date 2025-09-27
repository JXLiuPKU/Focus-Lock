#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Modified to connect to a Prior z-stage using the NPC-D-6110 controller 
and the H117P1XD/F z-stages.

com 3: xy
com 5: z

Xiaodong Guan, Jau 2025
"""

# priorSDK 瞎写，默认单位是1μm，不是 100 nm ( 0.1 μm) 
# sp400型号 标准行程 0--400 μm ，有10%的超调量，实际行程可达 -40--440 μm 但属于开环行程 【实际代码测试出的行程】
# servo 默认开启？
# 与PI N-725正负对半分的量程不同

#%%
from ctypes import WinDLL, create_string_buffer
import os
import sys
import time

path = "D:/GXD/Prior_stage_documents/PriorSDK_1.9.2/x64/PriorScientificSDK.dll"

class PriorZStage(object):
    def __init__(self, com = 20):
        
        self.path = "D:/GXD/Prior_stage_documents/PriorSDK_1.9.2/x64/PriorScientificSDK.dll"
        self.rx = create_string_buffer(1000)
        self.com = com    
        self.unit_to_um = 1   #  1 um per default unit               SDK 错误信息： 0.1 um (100 nm) per default unit   
        self.um_to_unit = 1.0/self.unit_to_um
        
        self.rangemin = 0   # 
        self.rangemax = 400    #    型号先验，暂无代码读取此信息
        
        if os.path.exists(self.path):
            self.SDKPrior = WinDLL(self.path)
        else:
            raise RuntimeError("Prior DLL could not be loaded.")

        # necessary   不初始化连接不上
        init_rev = self.SDKPrior.PriorScientificSDK_Initialise()
        if init_rev:
            print(f"Error initialising {init_rev}")
            sys.exit()
        else:
            print(f"Ok initialising {init_rev}")
            
        # sdk_ver = self.SDKPrior.PriorScientificSDK_Version(self.rx)
        # print(f"dll version api ret={sdk_ver}, version={self.rx.value.decode()}")

        self.sessionID = self.SDKPrior.PriorScientificSDK_OpenNewSession()
        print(f"SessionID = {self.sessionID}")
        
        msg_0 = "controller.connect {}".format(self.com)
        
        connectLabel = self.SDKPrior.PriorScientificSDK_cmd(self.sessionID, create_string_buffer(msg_0.encode()), self.rx
        )
        # print("connectLabel: ", connectLabel)
        
        if connectLabel:
            print("Prior z-stage connect failed")
        else:
            print("Prior z-stage connected")
            # print(f"0 means success, {connectLabel} ")
        
        self.good = connectLabel + 1
        
        msg_1 = "controller.z.position.get"
        self.curpos = self.SDKPrior.PriorScientificSDK_cmd(self.sessionID, create_string_buffer(msg_1.encode()), self.rx
        )
        # print("self.curpos: ", self.curpos)
        print('Initial position of z stage is {:.3f} um'.format( self.unit_to_um*self.curpos))
        
    def getStatus(self):
        return self.good
    
    def cmd(self, msg):
        ret = self.SDKPrior.PriorScientificSDK_cmd(
            self.sessionID, create_string_buffer(msg.encode()), self.rx
        )
        if ret:
            print(f"Api error {ret}")
        else:
            try:
                return self.rx.value.decode()
            except:
                return self.rx.value

    def zMoveTo(self, z):
        """
        Move the z stage to the specified position (in microns).
        """
        if self.good:
            Z = z * self.um_to_unit
            if Z > self.rangemin and Z < self.rangemax:
                msg = "controller.z.goto-position {}".format(Z)
                self.cmd(msg)
                # self.msleep(10)
                # ontarget = self.waitontarget(z)
                # print("ontarget: ", ontarget)    
                # print('z stage moved to {:.4f} um'.format(z))
            else:
                print('requested move outside max range!')
    
    def zPosition(self):
        
        msg = "controller.z.position.get"
        
        curpos_unit = self.cmd(msg)
        curpos_um = float(curpos_unit) * self.unit_to_um
        print("current z is {:.3f} μm".format(curpos_um))
        
        # return {"current z (μm)" : curpos_um}
    
    def zPos(self):
        """
        Query for current z position in microns.
        """
        msg = "controller.z.position.get"
        
        curpos_unit = self.cmd(msg)
        # print("curpos_unit: ", curpos_unit)
        curpos_um = float(curpos_unit) * self.unit_to_um
        
        return curpos_um    
    
    def zZero(self):
        target_z = 0
        msg = "controller.z.goto-position {}".format(target_z)
        rev = self.cmd(msg)
        ontarget = self.waitontarget(target_z)
        # print("ontarget: ", ontarget)  
        # self.zPosition()
    
    def shutDown(self):
        msg = "controller.disconnect"
        self.cmd(msg)
        print("Prior z-stage disconnected")

    def msleep(self, ms):
        time.sleep(ms/1000)

    def waitontarget(self,target_z):
        ontarget = False
        curpos = self.zPos()
        while abs(curpos - target_z) > 0.001:
            self.msleep(2)
            curpos = self.zPos()
        ontarget = True
        
        return ontarget
        
if (__name__ == "__main__"):
    zstage = PriorZStage()
    
    if not zstage.getStatus():
        exit()
    else:
        zstage.zMoveTo(100)
        zstage.zPosition()
        
        zstage.zMoveTo(300)
        zstage.zPosition()
        
        zstage.zZero()
        zstage.zPosition()
        
        zstage.shutDown()