# Proyecto: Descarga y Filtrado de Licitaciones por CPV

## Descripción
Este script automatiza la descarga de licitaciones publicadas el día laboral anterior desde la Plataforma de Contratación del Estado, filtradas por códigos CPV específicos. Posteriormente, los resultados se guardan en un archivo JSON y se envían por correo electrónico a las direcciones definidas.

## Características
- **Automatización con Selenium**: El script navega automáticamente por la plataforma de contratación.
- **Filtrado por CPV**: Se seleccionan códigos CPV predefinidos para obtener licitaciones relevantes.
- **Segundo filtrado por palabras clave**: Según las licitaciones obtenidas por el filtro de CPVs se aplica un segundo filtrado sobre los pliegos técnicos por *palabras clave*. ***(Falta perfeccionar para diferentes formatos por ahora solo funciona con `.pdf`)*** 
- **Generación de JSON**: Se almacenan los resultados en un archivo `tenders.json`.
- **Notificación por correo**: Se envían correos electrónicos con las licitaciones clasificadas en Publicadas, Adjudicadas y Modificadas.
- **Interfaz en consola**: Se proporciona feedback en tiempo real mediante `rich` para mejorar la experiencia del usuario.

## Requisitos
- Python 3.11
- Google Chrome y ChromeDriver
- Librerías necesarias (ver sección de instalación)

## Instalación
1. Clona este repositorio:
   ```bash
   git clone https://github.com/DiegoP2001/Scratender-2.0.git
   cd Ekilinfo-2.0
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configura las variables de entorno necesarias:
   ```bash
   export PROFILE_NAME="tu_perfil"
   export PATH_TO_PROFILE="ruta_a_tu_perfil"
   ```

## Uso
Ejecuta el script con:
```bash
python main.py
```

## Configuración
### Códigos CPV predefinidos
Los CPVs utilizados están definidos en el código como:
```python
DEFAULT_CPVS = ["71000000", "50230000", "45000000", "34990000", "34968200", "34920000", "31520000", "09300000", "50000000", "31530000"]
```
### Palabras clave predefinidas para el segundo filtrado
```python
KEYWORDS = [
   "luminaria", 
   "lluminària",
   "lluminàries",
   "alumbrado público",
   "enllumenat públic", 
   "alumbrado publico",
   "alumbrado exterior",
   "enllumenat exterior" 
   "iluminación solar", 
   "farola", 
   "fanall",
   "red de alumbrado", 
   "mejora de alumbrado",
   "mejora del alumbrado", 
   "renovación de alumbrado",
   "renovación del alumbrado",
   "renovació d'enllumenat"
]
```
Se pueden modificar en el código fuente si es necesario.


### Destinatarios de correo
El envío de correos se realiza a las siguientes direcciones: (se debe descargar el archivo "credentials.json" de tu cuenta de Google)
```python
notifier.send_email_v2_gmail_api(
    user_email="example@example.com",
    recipients_email=["example@example.com", "example1@example.com"],
    subject="Publicaciones",
    html_content=published
)
```
Modifica esta lista en el código si es necesario.

## Dependencias
Este script utiliza las siguientes librerías:

- `requests`
- `python-dotenv`
- `selenium`
- `beautifulsoup4`
- `webdriver-manager`
- `rich`
- `json`
- `os`
- `datetime`
- `time`
- `undetected_chromedriver`
- `fake_useragent`
- `google-api`
- `google-auth`
- `PyMuPDF`


Puedes instalarlas todas con:
```bash
pip install requests python-dotenv beautifulsoup4 selenium rich webdriver-manager undetected_chromedriver fake_useragent google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client PyMuPDF
```

## Autor
**Diego Piedra Alvarez**


