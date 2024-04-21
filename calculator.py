import tkinter as tk
from tkinter import ttk

def hesapla():
    num1 = float(sayi1_entry.get())
    num2 = float(sayi2_entry.get())
    islem_turu = islem.get()
    
    if islem_turu == "Toplama":
        sonuc = num1 + num2
    elif islem_turu == "Çıkarma":
        sonuc = num1 - num2
    elif islem_turu == "Çarpma":
        sonuc = num1 * num2
    elif islem_turu == "Bölme":
        if num2 != 0:
            sonuc = num1 / num2
        else:
            sonuc_label.config(text="Sıfıra bölme hatası!")
            return
    sonuc_label.config(text="Sonuç: " + str(sonuc))

root = tk.Tk()
root.title("Basit Hesap Makinesi")

sayi1_label = ttk.Label(root, text="Birinci Sayı:")
sayi1_label.grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)

sayi1_entry = ttk.Entry(root)
sayi1_entry.grid(column=1, row=0, padx=5, pady=5)

sayi2_label = ttk.Label(root, text="İkinci Sayı:")
sayi2_label.grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)

sayi2_entry = ttk.Entry(root)
sayi2_entry.grid(column=1, row=1, padx=5, pady=5)

islem = ttk.Combobox(root, values=["Toplama", "Çıkarma", "Çarpma", "Bölme"])
islem.grid(column=1, row=2, padx=5, pady=5)
islem.set("İşlem Seçiniz")

hesapla_button = ttk.Button(root, text="Hesapla", command=hesapla)
hesapla_button.grid(column=1, row=3, padx=5, pady=5)

sonuc_label = ttk.Label(root, text="Sonuç:")
sonuc_label.grid(column=0, row=4, columnspan=2, sticky=tk.W, padx=5, pady=5)

root.mainloop()
