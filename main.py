if __name__ == "__main__":
    import tkinter as tk
    from ui import EnergyApp  # assuming your Tkinter app is saved in a file named energy_app_tk.py

    root = tk.Tk()
    app = EnergyApp(root)
    root.mainloop()
