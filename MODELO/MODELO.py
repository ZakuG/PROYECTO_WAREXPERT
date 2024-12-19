from tkinter import Tk, Frame, Text, Scrollbar, Label, END

# Configuración de la ventana principal
root = Tk()
root.title("Descripción con cuadro de texto")

# Marco para contener los widgets
info_frame = Frame(root)
info_frame.pack(pady=10, padx=10)

# Etiqueta descriptiva
Label(info_frame, text="Descripción:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")

# Cuadro de texto para la descripción
descripcion_texto = Text(info_frame, wrap="word", height=5, width=50, font=("Arial", 10))
descripcion_texto.grid(row=0, column=1, sticky="w")

# Scrollbar para el cuadro de texto
scroll = Scrollbar(info_frame, command=descripcion_texto.yview)
scroll.grid(row=0, column=2, sticky="ns")
descripcion_texto.config(yscrollcommand=scroll.set)

# Insertar texto en el cuadro de texto
descripcion = "Esta es una descripción de ejemplo que puede llegar a ser bastante extensa y por eso usamos un cuadro de texto con scroll para que sea más legible y manejable."
descripcion_texto.insert(END, descripcion)

# Configurar el cuadro de texto como solo lectura
descripcion_texto.config(state="disabled")

root.mainloop()