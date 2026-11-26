import requests

URL_PRODUCTOS = "https://static.compragamer.com/productos"

TIENDA = "compragamer"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-US,es-419;q=0.9,es;q=0.8,en;q=0.7",
    "Origin": "https://compragamer.com",
    "Referer": "https://compragamer.com/",
}


def extraer_sku(codigo_principal) -> str | None:
    """Extrae el codigo SKU limpio desde 'codigo_principal' si viene en lista (generalmente viene : codigo_principal : [ "SKU : K4545HFFCCC1"])"""
    
    if isinstance(codigo_principal, list) and codigo_principal: 
        valor = str(codigo_principal[0]).replace("SKU:", "").strip()
        return valor or None
    return None


def _a_float(valor) -> float | None : 
    if valor is None: 
        return None
    try:
        return float(valor)
    except(TypeError, ValueError): 
        return None
    
def obtener_productos_crudos(timeout: int = 15) -> list[dict]:
    try: 
        respuesta= requests.get(URL_PRODUCTOS, headers=HEADERS, timeout=timeout)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.RequestException as exc:
        print(f"[compragamer]Error de red/HTTP: {exc}")
        return []
    except ValueError as exc:
        print(f"[compragamer] Error al decodificar JSON: {exc}")
        return []
    
    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        for clave in ("productos", "data", "items", "resultados"):
            """Cuando los datos estan en un diccionario se ve asi: respuesta = { "productos" : [{ "id_producto"}, { "id_producto"}]...}"""
            if isinstance(datos.get(clave), list): 
                return datos[clave]
    print("[compragamer] Formato de JSON inesperado")
    return []                

def normalizar_productos(raw_items: list[dict]) -> list[dict]:
    """Convierte los ítems crudos al esquema estándar de la base de datos."""
    normalizados = []

    for item in raw_items:
        nombre = (item.get("nombre") or "").strip()
        id_externo = item.get("id_producto")

        if not nombre or id_externo is None:
            continue

        try:
            id_externo_int = int(id_externo)
        except (TypeError, ValueError):
            continue

        stock_raw = item.get("stock")
        try:
            stock = int(stock_raw) if stock_raw is not None else 0
        except (TypeError, ValueError):
            stock = 0

        vendible = bool(item.get("vendible"))
        disponible = vendible and stock > 0 and item.get("codigo") == "disponible"

        normalizados.append({
            "tienda": TIENDA,
            "id_externo": id_externo_int,
            "nombre": nombre,
            "sku": extraer_sku(item.get("codigo_principal")),
            "precio_especial": _a_float(item.get("precioEspecial")),
            "precio_lista": _a_float(item.get("precioLista")),
            "stock": stock,
            "disponible": disponible,
            "id_categoria": item.get("id_categoria"),
            "id_subcategoria": item.get("id_subcategoria"),
            "id_marca": item.get("id_marca"),
        })

    return normalizados