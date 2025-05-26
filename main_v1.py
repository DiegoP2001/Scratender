from base.scrapper import Scrapper
from sender import Sender

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from typing import Dict, List
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List
from time import sleep

import os
import json
import fitz
import requests
import re

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
   # "fotovoltaic", 
   "farola", 
   "fanall",
   #"energía solar", 
   #"energia solar",
   "red de alumbrado", 
   #"eficiencia energética",
   #"eficiencia energetica", 
   "mejora de alumbrado",
   "mejora del alumbrado", 
   "renovación de alumbrado",
   "renovación del alumbrado",
   "renovació d'enllumenat"
]

def delete_tender_docs():
    """ Elimina todos los archivos .pdf en el directorio actual """
    with console.status("[bold cyan]Eliminando documentos analizados...[/]", spinner="dots"):
        pdf_files = Path(".").glob("*.pdf")
        for file in pdf_files:
            try:
                file.unlink()
                console.print(f"[bold green]✅ Eliminado: {file}")
            except Exception as e:
                console.print(f"[bold red]❌ Error eliminando {file}: {e}")

def download_file(url: str, filename: str):
    """ Descarga un archivo desde una URL """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        file = f"{filename if filename.find('.pdf') != -1 else filename + '.pdf'}"
        with open(file, "wb") as f:
            f.write(response.content)
        return file
    except requests.RequestException as e:
        console.print(f"[bold red]❌ Error descargando el PDF: {e}")
        return None

def get_technical_requirements(pdf_path: str):
    """ Extrae un enlace cercano a 'Pliego Prescripciones Técnicas' si está presente en el PDF """
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        text_instances = page.search_for("Pliego Prescripciones Técnicas")
        links = page.get_links()

        for link in links:
            if "uri" in link and link["uri"]:  # Verifica si es un enlace válido
                link_rect = fitz.Rect(link["from"])  # Obtener la posición del enlace
                
                for rect in text_instances:
                    if rect.intersects(link_rect):  # Verifica si se superponen
                        return link['uri']  # Retorna el primer enlace encontrado

    return None  # Si no se encuentra el enlace



def extract_text_from_pdf(pdf_path_or_stream):
    """ Extrae el texto de un PDF desde un archivo o un stream """
    doc = fitz.open(pdf_path_or_stream)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.lower()

def contains_keywords(text, keywords):
    """ Verifica si el texto contiene alguna de las palabras clave """
    return any(keyword in text for keyword in keywords)

def analyze_pdf_from_link(pdf_url):
    """ Descarga y analiza un PDF para determinar si contiene palabras clave """
    pdf_stream = download_file(pdf_url, "archivo")
    if not pdf_stream:
        console.print(f"[bold red]❌ No se pudo descargar el PDF.")
        return None
    
    text = extract_text_from_pdf(pdf_stream)
    
    if contains_keywords(text, KEYWORDS):
        console.print(f"[bold green]✅ ¡El documento contiene palabras clave relacionadas con iluminación!")
        return True
    else:
        console.print(f"[bold red]❌ No se encontraron palabras clave relevantes.")
        return False
    
def analyze_pdf_from_path(pdf_stream: str):
    """ Descarga y analiza un PDF para determinar si contiene palabras clave """
    text = extract_text_from_pdf(pdf_stream)
    
    if contains_keywords(text, KEYWORDS):
        console.print(f"[bold green]✅ ¡El documento contiene palabras clave relacionadas con iluminación!")
        return True
    else:
        console.print(f"[bold red]❌ No se encontraron palabras clave relevantes.")
        return False

def get_main_doc(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        rows = soup.find_all("tr")

        for row in rows:
            tipo_documento = row.find("td", class_="tipoDocumento")
            
            if tipo_documento and ("Pliego" in tipo_documento.get_text(strip=True)):
                
                pdf_link = row.find("a", string="Pdf")
                if pdf_link:
                    pdf_url = pdf_link["href"]
                    return [pdf_url]
                else:
                    print("No se encontró un enlace PDF en esta fila.")
            
        links = soup.find_all("a")
        pdf_links = []
        for link in links:
            if "descarga de pliegos" in link.text.lower():
                pdf_links.append(link["href"])
        if len(pdf_links) > 0:
            return pdf_links
        return None       
    else:
        print(response)
        print("Error al acceder a la página. Código de estado:", response.status_code)
        return None

def get_original_url(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        try:
            a_tag = soup.find("a", id=re.compile(r"link_EnlaceLicAgr$"))
            original_link = a_tag.get("href")
        except:
            original_link = None
        return original_link
    return None

def get_previous_laboral_day_date():
    today = datetime.today()
    if today.weekday() == 0:
        prev_date = today - timedelta(days=3)  
    else:
        prev_date = today - timedelta(days=1)  

    return prev_date.strftime("%d-%m-%Y")

def create_table(licitaciones):
    table = Table(title="📋 Licitaciones Encontradas", show_lines=True)
    table.add_column("Expediente", justify="center", style="cyan", no_wrap=True)
    table.add_column("Título", style="magenta")
    table.add_column("Importe", justify="right", style="green")
    table.add_column("Estado", justify="center", style="bold yellow")

    for lic in licitaciones:
        table.add_row(lic["Expediente"], lic["Titulo"], lic["Importe"], lic["Estado"])

    return table

config = {}
scrapper = Scrapper(
    profile_name=config.get("profile_name", os.getenv("PROFILE_NAME")),
    path_to_profile=config.get("path_to_profile", os.getenv("PATH_TO_PROFILE")),
)
wait = scrapper.wait(timeout=60)
notifier = Sender()
console = Console()
MAX_LEVEL_DEPTH = 2

# SCRAPPING ____________________________________________________________________________________________________________________>

def search_tenders() -> bool:
    error = False

    with console.status("[bold cyan]Navegando a la Plataforma de Contratación del Estado...[/]", spinner="dots"):  
        scrapper.navigate_to("https://contrataciondelestado.es/wps/portal/plataforma")
        console.print("[bold green]✅ ¡Ya estamos en la Plataforma![/bold green]")

    try:
        with console.status("[bold cyan]Obteniendo enlace de búsqueda...[/]", spinner="dots"):  
            search = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[title='Search']")))[-1].get_attribute("href")
            console.print("[bold green]✅ ¡Enlace de búsqueda obtenido![/bold green]")
    except Exception as e:
        error = True
        console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")

    # Navegamos a Buscador
    with console.status("[bold cyan]Navegando al buscador...[/]", spinner="dots"):
        scrapper.navigate_to(search)

    try:
        with console.status("[bold cyan]Obteniendo enlace de búsqueda avanzada...[/]", spinner="dots"): 
            advanced_search = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".paddingLeft1 > a"))).get_attribute("href")
            console.print("[bold green]✅ ¡Enlace de búsqueda avanzada obtenido![/bold green]")
    except Exception as e:
        error = True
        console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")


    # Navegamos a búsqueda avanzada
    with console.status("[bold cyan]Navegando al buscador avanzado...[/]", spinner="dots"):
        scrapper.navigate_to(advanced_search)
        console.print("[bold green]✅ ¡Ya estamos en el buscador avanzado![/bold green]")

    try:
        with console.status("[bold cyan]Obteniendo enlace a formulario de CPVs...[/]", spinner="dots"):  
            tenders_search_form = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:linkFormularioBusqueda")))
            console.print("[bold green]✅ ¡Enlace al formulario de CPVs obtenido![/bold green]")
    except Exception as e:
        error = True
        console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")

    # Navegamos al formulario de búsqueda
    with console.status("[bold cyan]Navegando al formulario de CPVs...[/]", spinner="dots"):
        scrapper.browser.execute_script("arguments[0].click();", tenders_search_form)

    # ANTES "71540000", "71310000"
    DEFAULT_CPVS = ["71540000", "71310000", "50230000", "45000000", "34990000", "34968200", "34920000", "31520000", "09300000", "50000000", "31530000"]
    # DEFAULT_CPVS = ["45000000"]

    try:
            with console.status("[bold cyan]Abriendo árbol de cpvs...[/]", spinner="dots"):
                select_cpvs = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:cpvMultiplelinkBuscarMultiple")))
                scrapper.browser.execute_script("arguments[0].click();", select_cpvs)
                tree_level = 0
                while tree_level <= MAX_LEVEL_DEPTH:
                    try:
                        tree_open_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img[alt='Click to expand']")))
                        for tree_open_icon in tree_open_links:
                            scrapper.browser.execute_script("arguments[0].click();", tree_open_icon)
                        sleep(1)
                        tree_level += 1
                    except Exception as e:
                        console.print(f"[bold yellow]✅ ¡Árbol de CPVs abierto completamente! [/bold yellow]")
            with console.status("[bold cyan]Seleccionando CPVs...[/]", spinner="dots"):
                try:
                    cpv_labels = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "label")))
                    for cpv in cpv_labels:
                        if cpv.text.startswith(tuple(DEFAULT_CPVS)):
                            scrapper.browser.execute_script("arguments[0].click();", cpv)
                except Exception as e:
                    error = True
                    console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")

                try:
                    accept_button = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:button1")))
                    accept_button.click()
                except Exception as e:
                    error = True
                    console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")
            console.print("[bold green]✅ ¡CPVs seleccionados con éxito![/bold green]")
    except Exception as e:
        error = True
        console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")

    try:
        with console.status("[bold cyan]Introduciendo rango de fechas...[/]", spinner="dots"):
            prev_date = get_previous_laboral_day_date()
            publication_date_start = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:textMinFecAnuncioMAQ2")))
            publication_date_start.send_keys(prev_date)
            # publication_date_start.send_keys("02-04-2025")
            publication_date_end = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:textMaxFecAnuncioMAQ")))
            publication_date_end.send_keys(prev_date if datetime.now().weekday() != 0 else (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y"))
            # publication_date_end.send_keys("03-04-2025")
            console.print("[bold green]✅ ¡Fechas colocadas![/bold green]")
    except Exception as e:
        error = True
        console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")


    try: 
        with console.status("[bold cyan]Presionando botón de búsqueda...[/]", spinner="dots"):
            search_button = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:button1")))
            search_button.click()
            console.print("[bold green]✅ ¡Botón de búsqueda presionado![/bold green]")
    except Exception as e:
        error = True
        console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")


    # Obtener los resultados
    with console.status("[bold cyan]Buscando licitaciones...[/]", spinner="dots"):
        try:                                                              
            total_pages = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:textfooterInfoTotalPaginaMAQ")), message="Total de páginas no encontrado.").text
            print(f"Total pages: {total_pages}")
            current_page = 1
            data: List[dict] = []
            while int(current_page) <= int(total_pages):
                table_founded = False 
                max_attempts = 10
                attempts = 0
                while not table_founded and attempts < max_attempts:
                    try:
                        table = wait.until(EC.presence_of_element_located((By.ID, "myTablaBusquedaCustom")), message="Tabla no encontrada")
                        table_founded = True
                    except:
                        console.print(f"[bold yellow]⚠️ Intento #{attempts} para intentar obtener la tabla[/bold yellow]")
                        attempts += 1
                        table_founded = False
                        sleep(10)

                if not table_founded:
                    notifier.send_email_v2_gmail_api(
                        user_email="example@example.com", # -> from email
                        recipients_email=["example@example.com"], # recipients
                        subject="Error obteniendo licitaciones",
                        html_content="<h1>ERROR TABLA NO ENCONTRADA</h1>"
                    )
                    raise Exception("La tabla no ha podido ser encontrada debido a que la conexión con PLCSP es muy lenta.")

                current_page = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:textfooterInfoNumPagMAQ")), message="Número de página no encontrado").text
                print(f"Current page: {current_page}")
                tbody = table.find_element(By.TAG_NAME, "tbody")
                rows = tbody.find_elements(By.TAG_NAME, "tr")
                for index, row in enumerate(rows):
                    contractor = row.find_element(By.CSS_SELECTOR, ".tdOrganoContratacion")
                    contractor_link = None
                    try:
                        a_element = contractor.find_element(By.TAG_NAME, "a")
                        contractor_link = a_element.get_attribute("href")
                        contractor_name = a_element.text
                    except Exception as e:
                        contractor_name = contractor.text

                    tender = {
                            "Expediente": row.find_element(By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:textoEnlace_" + str(index)).text,
                            "Link": row.find_element(By.CSS_SELECTOR, ".tdExpediente > div:first-child > a:last-child").get_attribute("href"),
                            "Titulo": row.find_element(By.CSS_SELECTOR, ".tdExpediente > div:last-child").text,
                            "TipoContrato": row.find_element(By.CSS_SELECTOR, ".tdTipoContrato > div:first-child").text,
                            "Estado": row.find_element(By.CSS_SELECTOR, ".tdEstado").text,
                            "Importe": row.find_element(By.CSS_SELECTOR, ".tdImporte").text,
                            "Presentacion": row.find_element(By.CSS_SELECTOR, ".tdFechaLimite").text,
                            "OrganoContratacion": contractor_name,
                            "OrganoContratacionLink": contractor_link
                    }
                    data.append(tender)

                    console.print(
                            f"\n[bold cyan]📌 Nueva Licitación Encontrada:[/bold cyan]\n"
                            f"🔹 [bold]Expediente:[/bold] {tender['Expediente']}\n"
                            f"🔹 [bold]Título:[/bold] {tender['Titulo']}\n"
                            f"🔹 [bold]Estado:[/bold] {tender['Estado']}\n"
                            f"🔹 [bold]Importe:[/bold] {tender['Importe']}\n"
                            f"🔹 [bold]Presentación:[/bold] {tender['Presentacion']}\n"
                            f"🔹 [bold]Órgano Contratación:[/bold] {tender['OrganoContratacion']}\n"
                            f"🔗 [bold blue]Enlace:[/bold blue] {tender['Link']}\n"
                            f"{'-' * 50}"
                    )  
                    
                try:
                    next_page = wait.until(EC.presence_of_element_located((By.ID, r"viewns_Z7_AVEQAI930OBRD02JPMTPG21004_:form1:footerSiguiente")), message="Botón de página siguiente no encontrado.")
                    scrapper.browser.execute_script("arguments[0].click();", next_page)
                except Exception as e:
                    console.print(f"[bold green]✅ ¡Scrapping de Licitaciones del día {prev_date} ha sido realizado con éxito![/bold green]")
                    break    

        except Exception as e:
            error = True
            console.print(f"[bold yellow]⚠️ {e}[/bold yellow]")
        finally:
            scrapper.browser.quit()

    # ===============================================================================================================================================

    print("\n")
    print("-" * 50)
    if not data:
        return True # si no hay datos por algún error silencioso o que se me haya escapado reiniciamos el script

    for index in reversed(range(len(data))):
        tender = data[index]
        is_interesting = []
        if tender["Estado"] == "Publicada":
            link = tender['Link']
            
            with console.status(f"[bold cyan]Accediendo a pliegos de licitación {tender['Expediente']} ...[/]", spinner="dots"):
                try:
                    docs = get_main_doc(link)
                    original_url = get_original_url(link)
                    tender['Link'] = original_url if original_url is not None else link
                    if not docs:
                        console.print(f"[bold red]❌ No se encontraron documentos para la licitación: {tender['Expediente']}[/bold red]")
                        print("-" * 50)
                        continue  # Pasamos a la siguiente licitación
                except Exception as e:
                    console.print(f"[bold red]❌ Error al obtener los documentos: {e}[/bold red]")
                    print("-" * 50)
                    continue  # Pasamos a la siguiente licitación
            
            # print(docs["links"])
            for doc_index, doc in enumerate(docs):
                if doc is None:
                    console.print(f"[bold red]❌ Documento no encontrado para la licitación: {tender['Expediente']}[/bold red]")
                    print("-" * 50)
                    continue  # Continuamos con otros documentos en la misma licitación
                
                with console.status(f"[bold cyan]Descargando pliegos de licitación {tender['Expediente']} ...[/]", spinner="dots"):
                    try:
                        doc_path = download_file(doc, f"document_{doc_index}_{index}")
                        console.print(f"[bold green]✅ Documento descargado de la licitación {tender['Expediente']}![/bold green]")
                    except Exception as e:
                        console.print(f"[bold red]❌ Error al descargar el pliego de licitación {tender['Expediente']}: {e}[/bold red]")
                        print("-" * 50)
                        continue  # Pasamos al siguiente documento si hay error

                with console.status(f"[bold cyan]Analizando requerimientos técnicos de licitación {tender['Expediente']} ...[/]", spinner="dots"):
                    try:
                        if len(docs) == 1:
                            technical_requirements = get_technical_requirements(doc_path)
                            if technical_requirements is None:
                                continue
                            is_interesting.append(analyze_pdf_from_link(technical_requirements))
                        else:
                            is_interesting.append(analyze_pdf_from_path(doc_path))
                        console.print(f"[bold green]✅ ¡Requerimientos analizados de la licitación {tender['Expediente']}![/bold green]")
                        # Optimizar, si hay interesante salir del bucle
                        if any(is_interesting):
                            break
                        if is_interesting.count(None) > 0: # Error descargando el PDF
                            is_interesting.append(True)
                    except Exception as e:
                        console.print(f"[bold red]❌ Error al analizar los requerimientos técnicos: {e}[/bold red]")
                        is_interesting.append(True) # Añado esto porque no sabemos que tiene dentro la licitación si entra en esta Exception
                        print("-" * 50)
            
            delete_tender_docs()

            if not any(is_interesting):
                data.pop(index)  # Eliminamos la licitación si no es interesante
                console.print(f"[bold red]❌ La licitación {tender['Expediente']} no es interesante y ha sido eliminada.[/bold red]")
                print("-" * 50)
            else:
                console.print(f"[bold green]✅ La licitación {tender['Expediente']} parece interesante.[/bold green]")
                print("-" * 50)

                    

    with console.status(f"[bold cyan]Escribiendo archivo de licitaciones ...[/]", spinner="dots"):
        with open("tenders.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(data, ensure_ascii=False, indent=3))
            console.print("[bold green]✅ ¡Archivo de licitaciones escrito con éxito!")


    tenders_grouped: Dict[str, List[dict]] = {
            "published": [],
            "awarded": [],
            "others": []
    }

    for tender in data:
        if "Resuelta" in tender.get("Estado"):
            continue
        if "Publicada" in tender.get("Estado"):
            tenders_grouped["published"].append(tender)
            continue
        if "Adjudicada" in tender.get("Estado"):
            tenders_grouped["awarded"].append(tender)
            continue
        tenders_grouped["others"].append(tender)

    published = "\n\n".join(
                f"""
                <div class="licitacion">
                    <h3>Licitación: {tender.get("Titulo", "")}</h3>
                    <table>
                        <tr>
                            <th>Nº de Expediente</th>
                            <td>{tender.get("Expediente", "")}</td>
                        </tr>
                        <tr>
                            <th>Categoría</th>
                            <td>{tender.get("TipoContrato", "")}</td>
                        </tr>
                        <tr>
                            <th>Fecha fin de presentación</th>
                            <td>{tender.get("Presentacion", "")}</td>
                        </tr>
                        <tr>
                            <th>Órgano de contratación</th>
                            <td>{tender.get("OrganoContratacion", "")}</td>
                        </tr>
                        <tr>
                            <th>Importe</th>
                            <td>{tender.get("Importe", "")}€</td>
                        </tr>
                        <tr>
                            <th>Estado</th>
                            <td>{tender.get("Estado", "")}</td>
                        </tr>
                    </table>
                    <div class="actions">
                        <a href="{tender.get("Link", "")}" class="button" style="color: black; text-decoration: none;">Ver Detalles</a>
                    </div>
                </div>
                """
                for tender in tenders_grouped.get("published")
            )
    awarded = "\n\n".join(
                    f"""
                <div class="licitacion">
                    <h3>Licitación: {tender.get("Titulo", "")}</h3>
                    <table>
                        <tr>
                            <th>Nº de Expediente</th>
                            <td>{tender.get("Expediente", "")}</td>
                        </tr>
                        <tr>
                            <th>Categoría</th>
                            <td>{tender.get("TipoContrato", "")}</td>
                        </tr>
                        <tr>
                            <th>Fecha fin de presentación</th>
                            <td>{tender.get("Presentacion", "")}</td>
                        </tr>
                        <tr>
                            <th>Órgano de contratación</th>
                            <td>{tender.get("OrganoContratacion", "")}</td>
                        </tr>
                        <tr>
                            <th>Importe</th>
                            <td>{tender.get("Importe", "")}€</td>
                        </tr>
                        <tr>
                            <th>Estado</th>
                            <td>{tender.get("Estado", "")}</td>
                        </tr>
                    </table>
                    <div class="actions">
                        <a href="{tender.get("Link", "")}" class="button" style="color: black; text-decoration: none;">Ver Detalles</a>
                    </div>
                </div>
                    """
                    for tender in tenders_grouped.get("awarded")
            )
    others = "\n\n".join(
                    f"""
                <div class="licitacion">
                    <h3>Licitación: {tender.get("Titulo", "")}</h3>
                    <table>
                        <tr>
                            <th>Nº de Expediente</th>
                            <td>{tender.get("Expediente", "")}</td>
                        </tr>
                        <tr>
                            <th>Categoría</th>
                            <td>{tender.get("TipoContrato", "")}</td>
                        </tr>
                        <tr>
                            <th>Fecha fin de presentación</th>
                            <td>{tender.get("Presentacion", "")}</td>
                        </tr>
                        <tr>
                            <th>Órgano de contratación</th>
                            <td>{tender.get("OrganoContratacion", "")}</td>
                        </tr>
                        <tr>
                            <th>Importe</th>
                            <td>{tender.get("Importe", "")}€</td>
                        </tr>
                        <tr>
                            <th>Estado</th>
                            <td>{tender.get("Estado", "")}</td>
                        </tr>
                    </table>
                    <div class="actions">
                        <a href="{tender.get("Link", "")}" class="button" style="color: black; text-decoration: none;">Ver Detalles</a>
                    </div>
                </div>
                    """
                    for tender in tenders_grouped.get("others")
            )

    notifier.send_email_v2_gmail_api(
        user_email="example@example.com",
        recipients_email=["example@example.com", "example1@example.com"],
        subject="Publicaciones",
        html_content=published
    )

    notifier.send_email_v2_gmail_api(
        user_email="example@example.com",
        recipients_email=["example@example.com", "example1@example.com"],
        subject="Adjudicaciones",
        html_content=awarded
    )

    notifier.send_email_v2_gmail_api(
        user_email="example@example.com",
        recipients_email=["example@example.com", "example1@example.com"],
        subject="Modificaciones",
        html_content=others
    )


    return error


reboot_script = True
while reboot_script:
    reboot_script = search_tenders()
    console.print(f"[bold red]❌ Ha ocurrido un error y se reiniciará el script.[/bold red]" if reboot_script else "[bold green]✅ El script ha sido ejecutado con éxito.[/bold green]")
    sleep(5)

