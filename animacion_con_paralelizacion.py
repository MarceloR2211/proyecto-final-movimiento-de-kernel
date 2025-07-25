import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading

lock = threading.Lock()

# Colores
pasto = np.array([124, 252, 0], dtype=np.uint8)
cielo = np.array([135, 206, 235], dtype=np.uint8)
negro = np.array([0, 0, 0], dtype=np.uint8)
morado = np.array([104, 58, 183], dtype=np.uint8)
verde = np.array([104, 159, 56], dtype=np.uint8)
a = np.array([0, 0, 1], dtype=np.uint8)
b = np.array([124, 252, 1], dtype=np.uint8)

# Fondo
def crear_fondo(cielo, pasto):
    fondo = np.zeros((300, 400, 3), dtype=np.uint8)
    fondo[:] = cielo
    fondo[-100:] = pasto
    return fondo

# kernel
def crear_objeto(a,b):
    objeto = np.array([
        [cielo, cielo, negro, negro, negro, negro, negro, negro, negro, negro, negro, negro, cielo, cielo],
        [cielo, negro, negro, verde, verde, verde, verde, verde, verde, verde, verde, verde, negro, cielo],
        [negro, morado, negro, verde, verde, verde, negro, verde, verde, verde, verde, verde, verde, negro],
        [negro, morado, negro, verde, verde, verde, negro, verde, verde, negro, verde, verde, negro, negro],
        [negro, negro, negro, negro, verde, verde, verde, verde, verde, verde, verde, verde, verde, negro],
        [cielo, negro, morado, negro, verde, verde, verde, verde, verde, verde, verde, verde, verde, negro],
        [cielo, negro, morado, negro, verde, verde, verde, verde, verde, verde, verde, verde, verde, negro],
        [cielo, negro, negro, negro, negro, verde, verde, verde, verde, negro, negro, negro, negro, negro],
        [cielo, cielo, negro, negro, negro, verde, verde, verde, verde, verde, negro, cielo, cielo, cielo],
        [cielo, cielo, negro, verde, negro, verde, verde, verde, verde, verde, negro, cielo, cielo, cielo],
        [pasto, pasto, pasto, negro, negro, verde, verde, verde, verde, verde, negro, pasto, b, pasto],
        [pasto, pasto, b, b, negro, negro, negro, negro, negro, negro, negro, b, b, pasto],
        [pasto, pasto, b, pasto, pasto, a, pasto, pasto, pasto, a, pasto, pasto, pasto, pasto],
        [pasto, pasto, pasto, pasto, pasto, a, a, pasto, pasto, a, a, pasto, pasto, pasto]
    ], dtype=np.uint8)
    return np.repeat(np.repeat(objeto, 10, axis=0), 10, axis=1) 

#crear mascaras
def crear_mascaras(objeto, a, b):
    mascara_a = (objeto == a).all(axis=-1)
    mascara_b = (objeto == b).all(axis=-1)
    #mascara_a = np.repeat(np.repeat(mascara_a, 10, axis=0), 10, axis=1)
    #mascara_b = np.repeat(np.repeat(mascara_b, 10, axis=0), 10, axis=1)
    return mascara_a, mascara_b

# alternar colores
def alternar_colores_objeto(objeto, mascara_a, mascara_b, frame_num, a, b):
    color_a = a if (frame_num // 5) % 2 == 0 else b
    color_b = b if (frame_num // 5) % 2 == 0 else a

    objeto_modificado = objeto.copy()
    objeto_modificado[mascara_a] = color_a
    objeto_modificado[mascara_b] = color_b
    return objeto_modificado

# Fragmentar imagen completa en bloques de 7x7
def fragmentar_bloques(imagen, tam_bloque=7):
    bloques = []
    alto, ancho, _ = imagen.shape
    for i in range(0, alto, tam_bloque):
        for j in range(0, ancho, tam_bloque):
            bloque = imagen[i:i+tam_bloque, j:j+tam_bloque].copy()
            bloques.append((i, j, bloque))
    return bloques

# Actualizar una imagen con un bloque
def actualizar_imagen(imagen, patron, i, j):
    alto, ancho, _ = patron.shape
    for y in range(alto):
        for x in range(ancho):
            imagen[i + y, j + x] = patron[y, x]
    return imagen

# Hilo que actualiza bloques
def procesar_hilo(bloques_objeto, bloques_fondo, resultados, idx_inicio, idx_fin):
    for k in range(idx_inicio, idx_fin):
        i, j, bloque_fondo = bloques_fondo[k]
        _, _, bloque_obj = bloques_objeto[k]
        bloque_actualizado = actualizar_imagen(bloque_fondo.copy(), bloque_obj, 0, 0)
        with lock:
            resultados[k] = (i, j, bloque_actualizado)

# Reconstruir objeto completo a partir de bloques
def reconstruir_objeto(bloques, alto, ancho):
    imagen = np.zeros((alto, ancho, 3), dtype=np.uint8)
    for i, j, bloque in bloques:
        h, w, _ = bloque.shape
        imagen[i:i+h, j:j+w] = bloque
    return imagen

# Crear un frame
def crear_frame(pos_x, pos_y, frame_num):
    objeto_dinamico = alternar_colores_objeto(objeto, mascara_a, mascara_b, frame_num, a, b)
    bloques_obj = fragmentar_bloques(objeto_dinamico)
    alto, ancho, _ = objeto_dinamico.shape
    bloques_fondo = []
    for i, j, _ in bloques_obj:
        bloque = fondo[pos_y+i:pos_y+i+7, pos_x+j:pos_x+j+7].copy()
        bloques_fondo.append((i, j, bloque))

    total = len(bloques_obj)
    resultados = [None] * total
    hilos = []
    n_por_hilo = 3
    for k in range(0, total, n_por_hilo):
        h = threading.Thread(target=procesar_hilo, args=(
            bloques_obj, bloques_fondo, resultados, k, min(k+n_por_hilo, total)))
        h.start()
        hilos.append(h)

    for h in hilos:
        h.join()

    objeto_actualizado = reconstruir_objeto(resultados, alto, ancho)
    frame = fondo.copy()
    frame[pos_y:pos_y+alto, pos_x:pos_x+ancho] = objeto_actualizado
    return frame

# Mostrar animación
fondo = crear_fondo(cielo, pasto)
objeto = crear_objeto(a,b)
mascara_a, mascara_b = crear_mascaras(objeto, a, b)

fig, ax = plt.subplots()
im = ax.imshow(crear_frame(0, 100, 0))
ax.axis('off')

def actualizar(frame_num):
    x = 10 + frame_num
    y = 100
    im.set_array(crear_frame(x, y, frame_num))
    return [im]

anim = animation.FuncAnimation(fig, actualizar, frames=250, interval=80, blit=True)
plt.show()