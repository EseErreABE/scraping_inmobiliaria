from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd


def configurar_driver():
    """Configura y retorna un driver de Chrome con opciones optimizadas."""
    # Opciones para optimizar el rendimiento
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar sin interfaz gráfica
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Deshabilitar carga de imágenes
    
        
    # Instalar y configurar el driver
    driver = webdriver.Chrome(options=chrome_options)
    
    # Establecer timeouts
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    
    return driver

def scrape_pagina_dinamica(url, tiempo_espera=10):
    """Realiza web scraping en una página con contenido dinámico usando Selenium.
    
    Args:
        url: URL del sitio a scrapear
        tiempo_espera: Tiempo máximo de espera para elementos dinámicos
    
    Returns:
        Los datos extraídos (formato depende de la implementación específica)
    """
    driver = configurar_driver()
    resultados = []
    
    try:
        # Cargar la página
        print(f"Accediendo a {url}...")
        driver.get(url)
        
        # Esperar a que la página cargue completamente (ajusta el selector según tu caso)
        # Por ejemplo, esperamos a que aparezca un contenedor principal
        WebDriverWait(driver, tiempo_espera).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "postingsList-module__postings-container")) #"main-content-selector"))
        )
        
        # Opcional: scroll para cargar contenido lazy-loaded
        scroll_altura_pagina(driver)
        
        # Extraer datos de la página
        elementos = driver.find_elements(by='xpath', value='//div[@class="postingsList-module__card-container"]')
        
        for elemento in elementos:
            # Extracción de datos específicos (ajusta según tus necesidades)
            titulo = elemento.find_element(By.CSS_SELECTOR, "selector-titulo").text
            descripcion = elemento.find_element(By.CSS_SELECTOR, "selector-descripcion").text
            precio = elemento.find_element(By.CSS_SELECTOR, "selector-precio").text
            
            resultados.append({
                "titulo": titulo,
                "descripcion": descripcion,
                "precio": precio
            })
            
        # Ejemplo: convertir resultados a DataFrame
        df = pd.DataFrame(resultados)
        return df
        
    except Exception as e:
        print(f"Error durante el scraping: {e}")
        return None
    
    finally:
        # Siempre cerrar el driver cuando termines
        driver.quit()

def scroll_altura_pagina(driver, pausas=5):
    """Realiza scroll gradual por la página para cargar elementos lazy-load."""
    # Obtener altura de la página
    altura_pagina = driver.execute_script("return document.body.scrollHeight")
    paso = altura_pagina // pausas
    
    for i in range(0, altura_pagina, paso):
        driver.execute_script(f"window.scrollTo(0, {i})")
        # Pequeña pausa para permitir la carga
        time.sleep(0.5)
    
    # Scroll final al fondo
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)

def scrape_paginacion(url_base, total_paginas=5):
    """Scrape de múltiples páginas con paginación."""
    driver = configurar_driver()
    todos_resultados = []
    
    try:
        for pagina in range(1, total_paginas + 1):
            url_pagina = f"{url_base}?page={pagina}"  # Ajusta según el formato de URL del sitio
            
            print(f"Procesando página {pagina} de {total_paginas}")
            driver.get(url_pagina)
            
            # Esperar a que cargue el contenido
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "selector-contenedor-principal"))
            )
            
            # Extraer datos (ajusta los selectores según tu caso)
            elementos = driver.find_elements(By.CSS_SELECTOR, "selector-items")
            
            for elemento in elementos:
                datos = {
                    "titulo": elemento.find_element(By.CSS_SELECTOR, "selector-titulo").text,
                    # Agrega más campos según necesites
                }
                todos_resultados.append(datos)
            
            # Pausa para evitar sobrecarga del servidor
            time.sleep(2)
        
        return pd.DataFrame(todos_resultados)
    
    finally:
        driver.quit()

def interactuar_con_elementos(url):
    """Ejemplo de cómo interactuar con elementos en páginas dinámicas."""
    driver = configurar_driver()
    
    try:
        driver.get(url)
        
        # Esperar y hacer clic en un botón
        boton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "selector-boton"))
        )
        boton.click()
        
        # Esperar a que aparezca nuevo contenido tras la interacción
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "selector-nuevo-contenido"))
        )
        
        # Llenar un formulario
        driver.find_element(By.ID, "campo-nombre").send_keys("Ejemplo")
        driver.find_element(By.ID, "campo-email").send_keys("ejemplo@ejemplo.com")
        
        # Seleccionar una opción de un dropdown
        from selenium.webdriver.support.select import Select
        dropdown = Select(driver.find_element(By.ID, "selector-dropdown"))
        dropdown.select_by_visible_text("Opción Deseada")
        
        # Enviar formulario
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Extraer resultados después de la interacción
        resultados = driver.find_elements(By.CSS_SELECTOR, "selector-resultados")
        return [r.text for r in resultados]
        
    finally:
        driver.quit()

# Ejemplo de uso
if __name__ == "__main__":
    # Reemplaza con la URL del sitio que quieres scrapear
    url_objetivo = "https://urbania.pe/buscar/venta-de-departamentos-en-san-borja-o-santiago-de-surco--lima--lima?bedroomMin=1&bedroomMax=2"
    
    # Obtener datos
    datos = scrape_pagina_dinamica(url_objetivo)
    
    if datos is not None and not datos.empty:
        print(f"Se obtuvieron {len(datos)} resultados")
        print(datos.head())
        
        # Guardar resultados
        datos.to_csv("resultados_scraping.csv", index=False)
        print("Resultados guardados en 'resultados_scraping.csv'")
    else:
        print("No se pudieron obtener datos")