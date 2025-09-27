# ASI_ZController_moveabs.py  —— 用 MOVE + WHERE，真正吃到 UM=100000 (10 nm/计数)
import re
from typing import Optional

from sc_hardware.ASI.ms2k import MS2000

class ASIZStage:
    def __init__(self, port="COM3", baud=9600, report=True, target_nm_per_count: Optional[float]=5.0, autosave=True):
        self.ms = MS2000(port, baud, report)
        self.ms.connect_to_serial()
        self._um = self._query_um() or 10000  # units/mm
        if target_nm_per_count is not None:
            self._set_um_and_verify(int(round(1e6/float(target_nm_per_count))), autosave)

        # ΣΔ 残差放在“UM 单位”的小数部分，避免浮点边界
        self._unit_residual = 0.0

    # ---------- UM ----------
    def _query_um(self) -> Optional[int]:
        self.ms.send_command("UM Z?")
        resp = self.ms.read_response()  # 可能是 ':A Z=100000' 或 ':Z=100000.000000 A'
        m = re.search(r'Z\s*=\s*(\d+)', resp or "")
        return int(m.group(1)) if m else None

    def _set_um_and_verify(self, units_per_mm: int, autosave: bool):
        old = self._query_um()
        self.ms.send_command(f"UM Z={int(units_per_mm)}"); self.ms.read_response()
        if autosave:
            self.ms.send_command("SS"); self.ms.read_response()
        new = self._query_um()
        if new == units_per_mm:
            self._um = new
            self._unit_residual = 0.0
            print(f"[UM] Applied: Z={new} units/mm → {1000/new:.5f} µm/unit")
        else:
            print(f"[UM][WARN] Controller kept Z={new or old}; not {units_per_mm}. Using {1000/self._um:.5f} µm/unit.")

    # ---------- 低层 WHERE/MOVE（直接使用 UM 单位） ----------
    def _where_units(self) -> int:
        # WHERE 的快捷是 W；返回形如 ':A -12345'
        self.ms.send_command("W Z")
        resp = self.ms.read_response()
        m = re.search(r':A\s+(-?\d+)', resp or "")
        if not m:
            # 尝试 WHERE Z
            self.ms.send_command("WHERE Z")
            resp = self.ms.read_response()
            m = re.search(r':A\s+(-?\d+)', resp or "")
        return int(m.group(1)) if m else 0

    def _move_abs_units(self, units: int):
        self.ms.send_command(f"M Z={int(units)}")
        self.ms.read_response()
        self.ms.wait_for_device()

    # ---------- 对外：µm 接口 ----------
    @property
    def um_nm_per_count(self) -> float:
        return 1e6 / self._um  # nm/UM-unit

    def zPosition(self) -> float:
        # µm = units * 1000 / UM
        return self._where_units() * (1000.0 / self._um)

    def zMoveTo(self, z_um: float):
        units = int(round(z_um * self._um / 1000.0))
        self._move_abs_units(units)
        self._unit_residual = 0.0

    def zMoveRel(self, dz_um: float):
        # 把相对 µm 转成 “UM 单位”的小数步长，做 ΣΔ，最后用 M 绝对落点
        du = self._unit_residual + (dz_um * self._um / 1000.0)
        k = int(du) if du >= 0 else -int(-du)
        if k != 0:
            cur = self._where_units()
            self._move_abs_units(cur + k)
            du -= k
        self._unit_residual = du

    def wait(self): self.ms.wait_for_device()
    def close(self): self.ms.disconnect_from_serial()
