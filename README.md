# UNIDAD-EDUCATIVA-LA-PAZ-A-
Desarrollar un sistema para la administración de citaciones que implemente un modelo de priorización basado en la Teoría de Colas, apoyando la comunicación entre el personal administrativo y los padres de familia.

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalados los siguientes requisitos:

- **Python 3.8 o superior**: Puedes descargarlo desde [python.org](https://www.python.org/downloads/)
- **MySQL**: Utilizamos MySQL como base de datos (conexión remota a Clever Cloud).
- **Git**: Para clonar el repositorio y gestionar versiones.
- **Virtualenv**: Para crear un entorno virtual y gestionar las dependencias.

## Instalación

1. **Clonar el repositorio**:

   Primero, clona el repositorio a tu máquina local usando Git:

   ```bash
   git clone https://github.com/denilsaa/UNIDAD-EDUCATIVA-LA-PAZ-A-.git
   cd UNIDAD-EDUCATIVA-LA-PAZ-A-
2. **Crear un entorno virtual**:
    Asegúrate de estar en el directorio del proyecto, luego crea un entorno virtual para instalar las dependencias.
## Windows
   - **python -m venv venv**
   - **.\venv\Scripts\activate**
## En Mac/Linux:
   - **python3 -m venv venv**
   - **source venv/bin/activate**

3. **Instalar las dependencias**:
    Una vez dentro del entorno virtual, instala todas las dependencias necesarias usando el archivo requirements.txt:
     - **pip install -r requirements.txt**

4. **Aplicar las migraciones**:
    Ejecuta el siguiente comando para aplicar las migraciones a la base de datos y crear las tablas necesarias.
     - **python manage.py migrate**
     
5. **Iniciar el servidor de desarrollo**:
    Finalmente, ejecuta el servidor de desarrollo para ver la aplicación en acción.
     - **python manage.py runserver**
    Ahora, abre tu navegador y visita http://127.0.0.1:8000 para ver el proyecto funcionando.



## Contribución

Si deseas contribuir al proyecto, por favor sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama para tus cambios:
   ```bash
   git checkout -b nombre-de-tu-rama
Realiza tus cambios y haz commit:
    -**git commit -am "Descripción de tus cambios"**
Haz un push a tu repositorio:
    -**git push origin nombre-de-tu-rama**
Abre un Pull Request en GitHub para que tus cambios sean revisados.