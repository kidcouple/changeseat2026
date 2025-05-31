import tkinter as tk
from changeseat import SeatLayoutApp

try:
    root = tk.Tk()
    
    # 창을 화면 중앙에 위치시키기
    window_width = 1000
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = SeatLayoutApp(root)
    root.mainloop()
except Exception as e:
    print(f"오류 발생: {str(e)}")
    import traceback
    traceback.print_exc() 