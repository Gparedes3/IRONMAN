# 🎬 Guía SÚPER fácil para grabar el vídeo de Jarvis

Sigue los pasos en orden. No te saltes ninguno. Lo que está en
`gris` se escribe tal cual. Lo que está en *"comillas"* se lee en voz alta.

---

## PARTE 1 — Preparar todo (antes de grabar)

**Paso 1.** Mira abajo a la derecha de la pantalla. ¿Ves el icono de una llama
(Ollama)? Si NO está, abre el menú Inicio, escribe `Ollama` y dale Enter.
Espera 5 segundos.

**Paso 2.** Abre **PowerShell**: menú Inicio → escribe `PowerShell` → Enter.

**Paso 3.** Copia esta línea, pégala en PowerShell (clic derecho pega) y dale Enter:

```
cd "$env:USERPROFILE\OneDrive\Documentos\IRONMAN"
```

**Paso 4.** Copia esta línea, pégala y Enter:

```
.\.venv\Scripts\Activate.ps1
```

Al principio de la línea debe aparecer `(.venv)`. Si aparece, vas bien.

**Paso 5.** Copia esto, pega y Enter (limpia la pantalla):

```
cls
```

**Paso 6.** Cierra WhatsApp, el correo y cualquier cosa personal. Vas a grabar
la pantalla y no quieres que salga nada privado.

**Paso 7.** Pon el volumen del micrófono. Habla una frase y comprueba que se oye.

---

## PARTE 2 — Empezar a grabar

**Paso 8.** Pulsa a la vez las teclas **`Windows`** y **`G`**. Se abre la
*Game Bar* (una barra de herramientas).

**Paso 9.** Busca el círculo de **Grabar** (●) y púlsalo. O pulsa a la vez
**`Windows`** + **`Alt`** + **`R`**. Verás un pequeño cronómetro: ya estás
grabando. 🎥

---

## PARTE 3 — Lo que dices y escribes (el guion)

> Consejo: mientras Jarvis "piensa" (tarda unos segundos), sigue hablando para
> que no haya silencios.

### 🗣️ Presentación (mira a la cámara o solo habla)

Lee esto en voz alta:

*"Hola, soy Guillermo. Esto es Jarvis, un asistente que funciona 100 % en mi
portátil, sin internet y sin GPU. Usa un modelo pequeño con Ollama, puede buscar
en documentos con RAG, y usar herramientas con un servidor MCP. Os enseño tres
cosas."*

**Paso 10.** Escribe en PowerShell y Enter:

```
python jarvis.py
```

Espera a que aparezca el mensaje de bienvenida de Jarvis.

---

### ✅ TAREA 1 — Una pregunta normal

**Paso 11.** Escribe esto tal cual y Enter:

```
Translate to English: 'el conocimiento es poder'
```

Mientras responde, di:

*"Aquí Jarvis responde él solo, con el modelo que corre en mi máquina, sin
buscar nada ni usar herramientas."*

---

### ✅ TAREA 2 — Buscar en los documentos (RAG)

**Paso 12.** Escribe esto tal cual y Enter:

```
Search the local docs: which environment variable changes where Ollama stores its models?
```

Cuando responda `OLLAMA_MODELS`, di:

*"Esto un modelo pequeño no se lo sabe de memoria. Lo ha buscado dentro de mi
corpus de documentación con un buscador local. Sin esa búsqueda, se lo
inventaría."*

---

### ✅ TAREA 3 — Usar una herramienta

**Paso 13.** Escribe esto tal cual y Enter:

```
Abre la calculadora
```

Cuando se abra la calculadora de Windows, di:

*"Aquí el modelo ha decidido usar una herramienta. El servidor MCP la ejecuta en
mi PC y abre la aplicación."*

---

### ⭐ TAREA 4 — Enseñar un fallo (opcional, pero suma nota)

**Paso 14.** Escribe esto tal cual y Enter:

```
Open the website ollama.com in my browser
```

Pase lo que pase, di:

*"A veces, con un modelo tan pequeño, en vez de ejecutar la herramienta escribe
la orden como texto. Es un límite conocido que tengo documentado en mi informe,
y tengo un mecanismo que lo recupera en la mayoría de los casos. Conocer los
límites es parte del trabajo."*

---

### 🗣️ Cierre

Lee esto en voz alta:

*"Y esto es todo. Funciona entero en mi portátil sin tarjeta gráfica. Los
números, las pruebas y los límites están explicados en mi informe. Gracias."*

**Paso 15.** Para salir de Jarvis, escribe `salir` (o `exit`) y Enter. Si no
funciona, pulsa **`Control`** + **`C`**.

---

## PARTE 4 — Parar la grabación

**Paso 16.** Pulsa otra vez **`Windows`** + **`Alt`** + **`R`** para parar.

**Paso 17.** El vídeo se guarda solo en la carpeta **Vídeos → Capturas**
(en inglés *Videos → Captures*). Ábrelo y míralo para comprobar que se ve y se
oye bien. Debe durar entre **3 y 5 minutos**. Si te pasaste, no importa
demasiado; si quedó muy largo puedes recortar el principio o el final.

---

## PARTE 5 — Subir el vídeo a internet

Elige UNA de las dos opciones.

### Opción A — YouTube (recomendada)
1. Entra en `https://youtube.com` con tu cuenta de Google.
2. Arriba a la derecha, pulsa la cámara con un **+** → **Subir vídeo**.
3. Arrastra tu archivo.
4. En "Visibilidad" elige **"No listado"** (así solo lo ve quien tenga el enlace).
5. Pulsa **Publicar**.
6. Copia el enlace que te da (algo como `https://youtu.be/xxxxxxxx`).

### Opción B — Google Drive
1. Entra en `https://drive.google.com`.
2. Arrastra el vídeo a Drive.
3. Cuando suba, clic derecho → **Compartir** → **Compartir**.
4. En "Acceso general" cambia a **"Cualquier persona con el enlace"**.
5. Pulsa **Copiar enlace**.

---

## PARTE 6 — Poner el enlace en el proyecto

**Paso 18.** Cuando tengas el enlace copiado, **escríbeme por aquí y pégamelo**.
Yo lo coloco automáticamente en el README, en el sitio correcto. Tú no tienes
que tocar nada más.

---

## ✅ Resumen de prompts (para copiar rápido)

1. `python jarvis.py`
2. `Translate to English: 'el conocimiento es poder'`
3. `Search the local docs: which environment variable changes where Ollama stores its models?`
4. `Abre la calculadora`
5. `Open the website ollama.com in my browser`

¡Y ya está! 🎉
