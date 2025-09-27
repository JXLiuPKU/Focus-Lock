# ASI_ZController_test_5nm.py
from time import sleep
from ASI_ZController import ASIZStage

def main():
    # 如需改口：port="COM4" 或你的实际串口
    z = ASIZStage(port="COM3", baud=9600, report=True)

    # 打印当前单位：期望 5 nm/单位（UM=200000）
    nm_per_unit = z.um_per_count * 1000.0
    print(f"[UM] 当前粒度 ≈ {nm_per_unit:.3f} nm/单位（期望 5.000）")

    start = z.zPosition()
    print("Start =", start, "um")

    # 目标：5 步 × 5 nm
    step_um = 0.005  # 5 nm
    for i in range(5):
        z.zMoveRel(step_um)
        # 轻微等待（机械稳定/读回更稳）
        sleep(0.02)
        cur = z.zPosition()
        print(f"Step {i+1}: +{step_um:.6f} um -> pos = {cur:.6f} um")

    end = z.zPosition()
    moved = end - start
    print(f"After 5×{step_um:.6f} um -> moved = {moved:.6f} um  (理论≈ {5*step_um:.6f} um)")
    print("Now at =", end, "um")

    z.close()

if __name__ == "__main__":
    main()
