# Manual de configuración — Tesis Precio de Bolsa
### Para: Ana
### Proyecto: Modelo predictivo del precio de bolsa de energía en Colombia

---

## ¿Qué vamos a hacer?

Este manual te guía paso a paso para configurar tu computador y empezar a trabajar en el proyecto de tesis. Al final tendrás:

- El código del proyecto descargado en tu computador
- Python configurado con todas las librerías necesarias
- Git configurado para trabajar en conjunto con Manu

---

## Parte 1 — Instalar las herramientas base

### 1.1 Instalar Miniconda

Miniconda es el gestor de entornos de Python que vamos a usar.

1. Ve a **https://www.anaconda.com/download** en tu navegador
2. Descarga **Miniconda** para tu sistema operativo:
   - Si tienes **Mac con chip M1/M2/M3**: descarga el archivo `.pkg` para macOS Apple Silicon
   - Si tienes **Mac con Intel**: descarga el archivo `.pkg` para macOS Intel
   - Si tienes **Windows**: descarga el instalador `.exe`
3. Ejecuta el instalador y acepta todas las opciones por defecto

**Verificar que quedó instalado:**

En Mac, abre la aplicación **Terminal** (búscala en Spotlight con Cmd+Space).
En Windows, abre **Anaconda Prompt** desde el menú inicio.

Ejecuta:
```
conda --version
```

Debe aparecer algo como `conda 24.x.x`. Si dice "command not found", cierra y vuelve a abrir la Terminal e intenta de nuevo.

---

### 1.2 Instalar Git

Git es el sistema que nos permite trabajar en el mismo código sin pisarnos.

**En Mac:**
Ejecuta en la Terminal:
```
git --version
```
Si ya está instalado aparece la versión. Si no, Mac te ofrece instalarlo automáticamente — acepta.

**En Windows:**
Descarga e instala desde **https://git-scm.com/download/win** con todas las opciones por defecto.

---

### 1.3 Crear cuenta en GitHub

1. Ve a **https://github.com** y crea una cuenta gratuita
2. Comparte tu nombre de usuario con Manu para que te agregue como colaboradora al repositorio

---

## Parte 2 — Descargar el proyecto

### 2.1 Obtener acceso al repositorio

Manu te va a enviar una invitación al correo que usaste para crear tu cuenta de GitHub. Acéptala antes de continuar.

### 2.2 Clonar el repositorio

"Clonar" significa descargar el proyecto en tu computador. Ejecuta en la Terminal:

**En Mac:**
```
git clone https://github.com/maguverm/tesis-bolsa.git ~/Documents/tesis-bolsa
```

**En Windows:**
```
git clone https://github.com/maguverm/tesis-bolsa.git C:\proyectos\tesis-bolsa
```

Cuando te pida usuario y contraseña:
- **Usuario**: tu nombre de usuario de GitHub
- **Contraseña**: necesitas un token (ver sección 2.3)

### 2.3 Crear un Personal Access Token

GitHub no acepta tu contraseña directamente — necesitas un token:

1. Ve a **github.com** → tu foto de perfil → **Settings**
2. Baja hasta el final → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token (classic)**
5. Dale un nombre (ej. "tesis"), selecciona el scope **repo**, y genera el token
6. Copia el token — solo lo verás una vez
7. Úsalo como contraseña cuando Git te la pida

---

## Parte 3 — Configurar el entorno de Python

El entorno de Python garantiza que tú y Manu tengan exactamente las mismas librerías instaladas.

### 3.1 Crear el entorno

**En Mac:**
```
cd ~/Documents/tesis-bolsa
conda create -n tesis-bolsa python=3.12.7
conda activate tesis-bolsa
conda install numpy pandas matplotlib seaborn scikit-learn -y
pip install jupyter pydataxm pyarrow python-dateutil requests
```

**En Windows:**
```
cd C:\proyectos\tesis-bolsa
conda create -n tesis-bolsa python=3.12.7
conda activate tesis-bolsa
conda install numpy pandas matplotlib seaborn scikit-learn -y
pip install jupyter pydataxm pyarrow python-dateutil requests
```

### 3.2 Verificar que quedó bien

Ejecuta:
```
python -c "import pandas; import pydataxm; print('Todo OK')"
```

Debe aparecer `Todo OK`.

---

## Parte 4 — Flujo de trabajo diario

Cada vez que vayas a trabajar en el proyecto sigue estos pasos:

### 4.1 Activar el entorno

**Mac:**
```
conda activate tesis-bolsa
cd ~/Documents/tesis-bolsa
```

**Windows:**
```
conda activate tesis-bolsa
cd C:\proyectos\tesis-bolsa
```

### 4.2 Traer los cambios de Manu

Antes de empezar a trabajar, descarga lo que Manu haya subido:
```
git pull
```

### 4.3 Trabajar en el código

Puedes abrir Jupyter Notebook para trabajar:
```
jupyter notebook
```

O abrir la carpeta del proyecto en VS Code si lo tienes instalado.

### 4.4 Guardar y subir tus cambios

Cuando termines de trabajar, sube tus cambios:

```
git add .
git commit -m "descripción breve de lo que hiciste"
git push
```

**Ejemplos de mensajes de commit:**
- `exploración precio de bolsa 2013-2020`
- `notebook preprocesamiento hidrología`
- `primer modelo baseline LSTM`

---

## Estructura del proyecto

```
tesis-bolsa/
├── data/
│   ├── raw/          ← datos originales descargados (no modificar)
│   ├── processed/    ← datos limpios listos para modelar
│   └── external/     ← variables externas (ONI, TRM, etc.)
├── notebooks/
│   ├── 01_exploracion/
│   ├── 02_preprocesamiento/
│   └── 03_experimentos/
├── src/
│   └── data/         ← scripts de descarga de datos
├── experiments/      ← resultados y métricas de modelos
├── reports/          ← gráficas y tablas para la tesis
└── README.md
```

---

## Solución de problemas frecuentes

**"conda: command not found" después de instalar**
→ Cierra y vuelve a abrir la Terminal. Si persiste, ejecuta `source ~/.zshrc` (Mac) o reinicia el computador (Windows).

**"Authentication failed" al hacer git clone**
→ Asegúrate de usar el Personal Access Token como contraseña, no tu contraseña de GitHub.

**"ModuleNotFoundError" al importar una librería**
→ Verifica que el entorno esté activo: debe aparecer `(tesis-bolsa)` al inicio del prompt. Si no, ejecuta `conda activate tesis-bolsa`.

**Conflictos al hacer git pull**
→ Avísale a Manu antes de resolver cualquier conflicto.

---

## Contacto

Cualquier duda con la configuración, escríbele a Manu.
