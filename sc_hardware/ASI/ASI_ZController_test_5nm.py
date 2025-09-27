# test_moveabs_10nm.py
from time import sleep
from ASI_ZController_5nm import ASIZStage

z = ASIZStage(port="COM3", baud=9600, report=True, target_nm_per_count=5.0)

print(f"[UM] now {z.um_nm_per_count:.3f} nm/unit (expected 10.000)")
start = z.zPosition()
print("Start =", start, "um")

# 两次 10 nm
for _ in range(5):
    z.zMoveRel(0.005)   # 10 nm
    sleep(0.02)

now = z.zPosition()
print("After 2×0.001 um -> moved =", now - start, "um  (≈ 0.025 um)")

# 归位
z.zMoveTo(start)
z.close()
