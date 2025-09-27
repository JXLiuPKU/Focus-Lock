from sc_hardware.ASI.ms2k import MS2000
import math
UM_TO_ASI = 10  # 1 um = 10 ASI units (1 unit = 0.1 um)

class ASIZStage:
    """
    锁焦用 Z 轴控制适配：
      - zMoveTo(z_um) / zMoveRel(dz_um) / zPosition() / zPos()
      - zAtTarget(tol_um) / wait() / zZero() / close() / shutDown()
    依赖：
      - serialport.py：发送时自动追加 '\r'，按 '\r' 读取一行
      - ms2k.py：MOVE/MOVREL 等命令 + 稳健 WHERE 解析 + wait_for_device 轮询
    """
    def __init__(self, port: str = "COM3", baud: int = 9600, report: bool = True):
        self.ms = MS2000(port, baud, report)
        self.ms.connect_to_serial()
        self.um_per_count = 0.1  # ASI 控制器单位：1 count = 0.1 µm
        self._um_residual = 0.0  # ΣΔ残差，单位 µm
        # self._count_residual = 0.0

    # def zMoveTo(self, z_um: float) -> None:
    #     """移动到绝对位置，单位 μm。"""
    #     self.ms.move_axis("Z", int(round(z_um * UM_TO_ASI)))
    #
    # def zMoveRel(self, dz_um: float) -> None:
    #     """相对位移（μm）。"""
    #     self.ms.moverel_axis("Z", int(round(dz_um * UM_TO_ASI)))

    def zMoveRel(self, dz_um: float) -> None:
        """相对移动（单位 µm）。小步残差累加，攒满 1 个计数才下发。"""
        acc = self._um_residual + float(dz_um)
        step = self.um_per_count
        # 保留符号的“向外取整”：当 |acc| >= 1 个计数时才下发
        counts = int(acc / step) if acc >= 0 else -int((-acc) / step)
        if counts != 0:
            self.ms.moverel_axis("Z", counts)  # 仍发“整数计数”
            self.ms.wait_for_device()
            acc -= counts * step  # 扣掉已发部分
        self._um_residual = acc

    # def zMoveRel(self, dz_um: float) -> None:
    #     """相对移动（µm）。在“计数”单位做残差累加，避免浮点边界误差。"""
    #     # 把 µm 增量换算成“计数增量”，直接在计数域累计
    #     self._count_residual += float(dz_um) / self.um_per_count
    #
    #     k = 0
    #     if self._count_residual >= 1.0:
    #         k = int(math.floor(self._count_residual))
    #     elif self._count_residual <= -1.0:
    #         k = int(math.ceil(self._count_residual))
    #
    #     if k != 0:
    #         self.ms.moverel_axis("Z", k)  # 仍旧给整数计数
    #         self.ms.wait_for_device()
    #         self._count_residual -= k  # 扣掉已发出的计数

    def zMoveTo(self, z_um: float) -> None:
        """绝对移动（单位 µm）。转成相对移动走同一套 ΣΔ 逻辑。"""
        cur = float(self.ms.get_position_um("Z"))
        self.zMoveRel(z_um - cur)

    def zPosition(self) -> float:
        """当前 Z 位置（μm）。"""
        return float(self.ms.get_position_um("Z"))

    def zPos(self) -> float:        # 其实和zPosition一个意思，但此处主要是为了保持与 PriorZStage 同名/同义
        return self.zPosition()

    def zAtTarget(self, tol_um: float = 0.02) -> bool:
        """到位判断：MS-2000 返回 'B' 忙/运动中；非忙视为达标。"""
        return (not self.ms.is_axis_busy("Z"))

    def wait(self) -> None:
        """阻塞等待所有轴停止运动。"""
        self.ms.wait_for_device()

    def zZero(self) -> None:
        """将当前位置设为 Z=0（原点）。"""

        self.ms.send_command("ZERO Z")
        self.ms.read_response()

    def close(self) -> None:
        """关闭串口。"""
        self.ms.disconnect_from_serial()

    def shutDown(self) -> None:     # 其实和close一个意思，但此次主要是为了保持与 PriorZStage 同名/同义
        self.close()