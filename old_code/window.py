import tkinter as tk


window = tk.Tk()
window.title("Bank App")
window.geometry("400x300")

label = tk.Label(window, text="Hello!")
label.pack(pady=10)

entry = tk.Entry(window)
entry.pack()

def clicked():
    label.config(text="You typed: " + entry.get())

button = tk.Button(window, text="Submit", command=clicked)
button.pack(pady=10)

window.mainloop()
































