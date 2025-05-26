"""
FastAPI WhatsApp Cloud API Bot con Integración OpenAI

Este módulo implementa un servidor webhook para WhatsApp Cloud API que:
1. Verifica el registro del webhook (petición GET)
2. Recibe mensajes entrantes (petición POST)
3. Procesa mensajes usando la API de OpenAI
4. Envía respuestas de vuelta a través de WhatsApp
"""

import os
import logging
import base64
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar aplicación FastAPI
app = FastAPI(title="WhatsApp OpenAI Bot", version="1.0.0")

# Variables de entorno
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validar variables de entorno requeridas
required_vars = ["VERIFY_TOKEN", "WHATSAPP_TOKEN", "PHONE_NUMBER_ID", "OPENAI_API_KEY"]
for var in required_vars:
    if not os.getenv(var):
        logger.error(f"Falta la variable de entorno requerida: {var}")
        raise ValueError(f"La variable de entorno {var} es requerida")

# Inicializar cliente OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# URL base de la API de WhatsApp
WHATSAPP_API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"


class WebhookData(BaseModel):
    """Modelo Pydantic para validación de datos del webhook entrante"""
    object: str
    entry: list


def download_media_file(media_id: str) -> Optional[str]:
    """
    Descargar archivo multimedia de WhatsApp y convertir a base64
    
    Args:
        media_id (str): ID del archivo multimedia de WhatsApp
        
    Returns:
        Optional[str]: Archivo en base64 o None si falla
    """
    try:
        # Paso 1: Obtener URL del archivo
        url_response = requests.get(
            f"https://graph.facebook.com/v22.0/{media_id}",
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        )
        url_response.raise_for_status()
        file_url = url_response.json().get("url")
        
        if not file_url:
            logger.error("No se pudo obtener la URL del archivo")
            return None
            
        # Paso 2: Descargar el archivo
        file_response = requests.get(
            file_url,
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        )
        file_response.raise_for_status()
        
        # Paso 3: Convertir a base64
        file_base64 = base64.b64encode(file_response.content).decode('utf-8')
        logger.info(f"Archivo descargado exitosamente: {len(file_base64)} caracteres")
        
        return file_base64
        
    except Exception as e:
        logger.error(f"Error descargando archivo multimedia: {str(e)}")
        return None


def get_openai_response_with_media(message: str, media_data: Optional[Dict] = None) -> str:
    """
    Generar respuesta usando la Response API de OpenAI con soporte para multimedia
    
    Args:
        message (str): Mensaje de entrada del usuario
        media_data (Optional[Dict]): Datos multimedia si los hay
        
    Returns:
        str: Respuesta generada por IA
    """
    try:
        # Preparar input según el tipo de contenido
        if media_data and media_data.get("type") == "image" and media_data.get("base64"):
            # Para imágenes, usar formato con imagen
            input_data = [
                {
                    "role": "system",
                    "content": "Eres un asistente útil de WhatsApp llamado WaChat Bot. Mantén las respuestas concisas y amigables. Puedes analizar imágenes, documentos, ubicaciones y contactos que te envíen. Siempre responde en español y de manera conversacional."
                },
                {
                    "role": "user", 
                    "content": message
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{media_data['base64']}"
                        }
                    ]
                }
            ]
        else:
            # Para texto y otros tipos de contenido
            enhanced_message = f"Instrucciones del sistema: Eres un asistente útil de WhatsApp llamado WaChat Bot. Mantén las respuestas concisas y amigables. Siempre responde en español.\n\nMensaje del usuario: {message}"
            
            if media_data:
                if media_data.get("type") == "location":
                    enhanced_message += f"\n\nDetalles de ubicación: Latitud {media_data.get('latitude')}, Longitud {media_data.get('longitude')}"
                    if media_data.get('name'):
                        enhanced_message += f", Lugar: {media_data.get('name')}"
                    if media_data.get('address'):
                        enhanced_message += f", Dirección: {media_data.get('address')}"
                elif media_data.get("type") == "contacts":
                    enhanced_message += f"\n\nEl usuario compartió {len(media_data.get('contacts', []))} contacto(s): {media_data.get('contact_names', 'N/A')}"
                elif media_data.get("type") == "document":
                    enhanced_message += f"\n\nDocumento enviado: {media_data.get('filename', 'Nombre no disponible')}, Tipo: {media_data.get('mime_type', 'N/A')}"
                    if media_data.get('caption'):
                        enhanced_message += f", Descripción: {media_data.get('caption')}"
                elif media_data.get("type") == "sticker":
                    enhanced_message += "\n\nEl usuario envió un sticker (emoji/imagen expresiva)"
                elif media_data.get("type") == "audio":
                    enhanced_message += "\n\nEl usuario envió un mensaje de audio/voz"
            
            input_data = enhanced_message
        
        # Usar la nueva Response API
        response = openai_client.responses.create(
            model="gpt-4.1",
            input=input_data
        )
        
        # Log de la respuesta para debugging
        logger.info(f"Respuesta de OpenAI Response API: {response.output_text}")
        
        return response.output_text.strip()
        
    except Exception as e:
        logger.error(f"Error en la Response API de OpenAI: {str(e)}")
        return "Lo siento, tengo problemas para procesar tu solicitud ahora. Por favor intenta de nuevo más tarde."


def get_openai_response(message: str) -> str:
    """
    Wrapper para mantener compatibilidad hacia atrás
    """
    return get_openai_response_with_media(message)


def send_whatsapp_message(to_phone: str, message: str) -> bool:
    """
    Enviar un mensaje de texto a través de la API Cloud de WhatsApp
    
    Args:
        to_phone (str): Número de teléfono del destinatario
        message (str): Texto del mensaje a enviar
        
    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        logger.info(f"Enviando mensaje de texto a {to_phone}")
        logger.info(f"URL: {WHATSAPP_API_URL}")
        logger.info(f"Payload: {payload}")

        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        response.raise_for_status()
        logger.info(f"Mensaje enviado exitosamente a {to_phone}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {str(e)}")
        return False


def send_whatsapp_media(to_phone: str, media_type: str, media_id: str, caption: str = "") -> bool:
    """
    Enviar multimedia (imagen, audio, documento, sticker) a través de la API Cloud de WhatsApp
    
    Args:
        to_phone (str): Número de teléfono del destinatario
        media_type (str): Tipo de media ('image', 'audio', 'document', 'sticker')
        media_id (str): ID del archivo multimedia de WhatsApp
        caption (str): Texto opcional para acompañar el media
        
    Returns:
        bool: True si el media se envió correctamente, False en caso contrario
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Configurar payload según el tipo de media
    if media_type == "sticker":
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "sticker",
            "sticker": {"id": media_id}
        }
    elif media_type == "image":
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "image",
            "image": {"id": media_id}
        }
        if caption:
            payload["image"]["caption"] = caption
    elif media_type == "audio":
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "audio",
            "audio": {"id": media_id}
        }
    elif media_type == "document":
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "document",
            "document": {"id": media_id}
        }
        if caption:
            payload["document"]["caption"] = caption
    else:
        logger.error(f"Tipo de media no soportado: {media_type}")
        return False
    
    try:
        logger.info(f"Enviando {media_type} a {to_phone} con ID: {media_id}")
        logger.info(f"Payload: {payload}")

        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        response.raise_for_status()
        logger.info(f"{media_type.capitalize()} enviado exitosamente a {to_phone}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error enviando {media_type}: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error enviando {media_type}: {str(e)}")
        return False


def send_whatsapp_location(to_phone: str, latitude: float, longitude: float, name: str = "", address: str = "") -> bool:
    """
    Enviar ubicación a través de la API Cloud de WhatsApp
    
    Args:
        to_phone (str): Número de teléfono del destinatario
        latitude (float): Latitud de la ubicación
        longitude (float): Longitud de la ubicación
        name (str): Nombre del lugar (opcional)
        address (str): Dirección del lugar (opcional)
        
    Returns:
        bool: True si la ubicación se envió correctamente, False en caso contrario
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "location",
        "location": {
            "latitude": latitude,
            "longitude": longitude
        }
    }
    
    if name:
        payload["location"]["name"] = name
    if address:
        payload["location"]["address"] = address
    
    try:
        logger.info(f"Enviando ubicación a {to_phone}: {latitude}, {longitude}")
        logger.info(f"Payload: {payload}")

        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        response.raise_for_status()
        logger.info(f"Ubicación enviada exitosamente a {to_phone}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error enviando ubicación: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error enviando ubicación: {str(e)}")
        return False


def extract_message_data(webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extraer datos relevantes del mensaje desde el payload del webhook
    
    Args:
        webhook_data (Dict): Datos crudos del webhook de WhatsApp
        
    Returns:
        Optional[Dict]: Información del mensaje extraída o None si no hay mensaje válido
    """
    try:
        entry = webhook_data.get("entry", [])
        if not entry:
            return None
            
        changes = entry[0].get("changes", [])
        if not changes:
            return None
            
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return None
            
        message = messages[0]
        message_type = message.get("type")
        
        # Extraer información básica del mensaje
        result = {
            "from": message.get("from"),
            "message_id": message.get("id"),
            "type": message_type,
            "media_data": None
        }
        
        # Procesar diferentes tipos de mensajes
        if message_type == "text":
            result["text"] = message.get("text", {}).get("body", "")
            
        elif message_type == "sticker":
            sticker_data = message.get("sticker", {})
            result["text"] = "📍 Usuario envió un sticker"
            result["media_data"] = {
                "type": "sticker",
                "id": sticker_data.get("id"),
                "mime_type": sticker_data.get("mime_type"),
                "animated": sticker_data.get("animated", False)
            }
            
        elif message_type == "image":
            image_data = message.get("image", {})
            result["text"] = "📷 Usuario envió una imagen"
            result["media_data"] = {
                "type": "image", 
                "id": image_data.get("id"),
                "mime_type": image_data.get("mime_type"),
                "caption": image_data.get("caption", "")
            }
            
        elif message_type == "audio":
            audio_data = message.get("audio", {})
            result["text"] = "🎵 Usuario envió un audio"
            result["media_data"] = {
                "type": "audio",
                "id": audio_data.get("id"),
                "mime_type": audio_data.get("mime_type")
            }
            
        elif message_type == "document":
            doc_data = message.get("document", {})
            result["text"] = "📄 Usuario envió un documento"
            result["media_data"] = {
                "type": "document",
                "id": doc_data.get("id"),
                "filename": doc_data.get("filename", "Archivo sin nombre"),
                "mime_type": doc_data.get("mime_type"),
                "caption": doc_data.get("caption", "")
            }
            
        elif message_type == "location":
            location = message.get("location", {})
            lat = location.get("latitude", "N/A")
            lng = location.get("longitude", "N/A")
            result["text"] = f"📍 Usuario compartió ubicación"
            result["media_data"] = {
                "type": "location",
                "latitude": lat,
                "longitude": lng,
                "name": location.get("name", ""),
                "address": location.get("address", "")
            }
            
        elif message_type == "contacts":
            contacts = message.get("contacts", [])
            contact_names = []
            for contact in contacts:
                name = contact.get("name", {})
                full_name = f"{name.get('first_name', '')} {name.get('last_name', '')}".strip()
                if full_name:
                    contact_names.append(full_name)
            
            result["text"] = f"👤 Usuario compartió {len(contacts)} contacto(s)"
            result["media_data"] = {
                "type": "contacts",
                "contacts": contacts,
                "contact_names": ", ".join(contact_names) if contact_names else "Sin nombres"
            }
            
        else:
            result["text"] = f"❓ Usuario envió un mensaje de tipo: {message_type}"
            
        return result
    except Exception as e:
        logger.error(f"Error extrayendo datos del mensaje: {str(e)}")
        return None


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """
    Endpoint de verificación del webhook para WhatsApp Cloud API
    
    Meta envía una petición GET para verificar la URL del webhook.
    Debemos devolver la cadena challenge si el token de verificación coincide.
    
    Args:
        hub_mode: Debe ser "subscribe"
        hub_challenge: Cadena aleatoria para hacer echo de vuelta
        hub_verify_token: Token para verificar la autenticidad del webhook
        
    Returns:
        PlainTextResponse: La cadena challenge si la verificación es exitosa
    """
    logger.info(f"Intento de verificación del webhook con token: {hub_verify_token}")
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Verificación del webhook exitosa")
        return PlainTextResponse(content=hub_challenge)
    else:
        logger.warning("Verificación del webhook falló")
        raise HTTPException(status_code=403, detail="Verificación falló")


@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Endpoint principal del webhook para recibir mensajes de WhatsApp
    
    Procesa mensajes entrantes, genera respuestas de IA, y envía respuestas.
    
    Args:
        request: Objeto request de FastAPI que contiene datos del webhook
        
    Returns:
        Dict: Respuesta de estado exitoso
    """
    try:
        # Parsear datos del webhook
        webhook_data = await request.json()
        logger.info(f"Datos del webhook recibidos: {webhook_data}")
        
        # Extraer información del mensaje
        message_data = extract_message_data(webhook_data)
        
        if not message_data:
            logger.info("No se encontró mensaje válido en los datos del webhook")
            return {"status": "ok"}
            
        user_phone = message_data["from"]
        user_message = message_data["text"]
        media_data = message_data.get("media_data")
        
        logger.info(f"Procesando mensaje de {user_phone}: {user_message}")
        
        # Si hay multimedia, intentar descargarlo
        if media_data and media_data.get("id") and media_data.get("type") in ["image", "document", "sticker"]:
            logger.info(f"Descargando {media_data.get('type')} con ID: {media_data.get('id')}")
            file_base64 = download_media_file(media_data.get("id"))
            if file_base64:
                media_data["base64"] = file_base64
                logger.info(f"Archivo descargado exitosamente para {media_data.get('type')}")
            else:
                logger.warning(f"No se pudo descargar el archivo {media_data.get('type')}")
        
        # Generar respuesta de IA con contexto multimedia
        ai_response = get_openai_response_with_media(user_message, media_data)
        
        # Primero enviar la respuesta de texto
        text_success = send_whatsapp_message(user_phone, ai_response)
        
        # Luego, si hay multimedia, reenviar el archivo multimedia
        media_success = True
        if media_data and media_data.get("id"):
            media_type = media_data.get("type")
            media_id = media_data.get("id")
            
            if media_type == "sticker":
                logger.info(f"Reenviando sticker con ID: {media_id}")
                media_success = send_whatsapp_media(user_phone, "sticker", media_id)
                
            elif media_type == "image":
                logger.info(f"Reenviando imagen con ID: {media_id}")
                caption = f"Recibí esta imagen. {ai_response[:100]}..." if len(ai_response) > 100 else ai_response
                media_success = send_whatsapp_media(user_phone, "image", media_id, caption)
                
            elif media_type == "audio":
                logger.info(f"Reenviando audio con ID: {media_id}")
                media_success = send_whatsapp_media(user_phone, "audio", media_id)
                
            elif media_type == "document":
                logger.info(f"Reenviando documento con ID: {media_id}")
                filename = media_data.get("filename", "documento")
                caption = f"Recibí este documento: {filename}"
                media_success = send_whatsapp_media(user_phone, "document", media_id, caption)
                
            elif media_type == "location":
                logger.info("Reenviando ubicación")
                lat = float(media_data.get("latitude", 0))
                lng = float(media_data.get("longitude", 0))
                name = media_data.get("name", "")
                address = media_data.get("address", "")
                media_success = send_whatsapp_location(user_phone, lat, lng, name, address)
        
        if text_success and media_success:
            logger.info("Procesamiento del mensaje completado exitosamente")
        else:
            if not text_success:
                logger.error("Falló el envío de la respuesta de texto")
            if not media_success:
                logger.error("Falló el envío del multimedia")
            
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.get("/")
async def root():
    """Endpoint de verificación de salud"""
    return {"message": "WhatsApp OpenAI Bot está ejecutándose", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Verificación de salud detallada con validación de entorno"""
    return {
        "status": "healthy",
        "environment_check": {
            "verify_token": "✓" if VERIFY_TOKEN else "✗",
            "whatsapp_token": "✓" if WHATSAPP_TOKEN else "✗",
            "phone_number_id": "✓" if PHONE_NUMBER_ID else "✗",
            "openai_key": "✓" if OPENAI_API_KEY else "✗"
        }
    }


@app.post("/test-whatsapp")
async def test_whatsapp_message(phone_number: str, message: str = "Mensaje de prueba"):
    """Endpoint para probar el envío de mensajes de WhatsApp directamente"""
    logger.info(f"Probando envío de mensaje a {phone_number}")
    success = send_whatsapp_message(phone_number, message)
    return {
        "success": success,
        "phone_number": phone_number,
        "message": message,
        "whatsapp_api_url": WHATSAPP_API_URL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)