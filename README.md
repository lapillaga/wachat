# 🤖 WaChat Bot - WhatsApp AI Assistant

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-009688.svg)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991.svg)](https://openai.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366.svg)](https://developers.facebook.com/docs/whatsapp)

Un bot inteligente de WhatsApp que utiliza la API de OpenAI para proporcionar respuestas conversacionales naturales. Admite múltiples tipos de contenido multimedia y búsqueda en documentos utilizando vector stores.

## ✨ Características Principales

- 🗣️ **Conversaciones naturales** con GPT-4.1
- 📷 **Análisis de imágenes** con visión artificial
- 📄 **Búsqueda inteligente** en documentos usando vector stores
- 🌍 **Soporte multimedia completo**: texto, imágenes, audio, documentos, ubicaciones, contactos y stickers
- 🔄 **Reenvío automático** de contenido multimedia
- 🚀 **Respuestas en tiempo real** a través de webhooks
- 🛡️ **Verificación segura** de webhooks
- 📊 **Logging detallado** para debugging
- 🔧 **Endpoints de prueba** integrados

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   WaChat Bot    │    │   OpenAI API    │
│   Cloud API     │◄──►│   (FastAPI)     │◄──►│   GPT-4.1       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Vector Store   │
                       │  File Search    │
                       └─────────────────┘
```

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd wachat
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto:

```env
# WhatsApp Cloud API
WHATSAPP_TOKEN=tu_token_de_whatsapp
PHONE_NUMBER_ID=tu_phone_number_id
VERIFY_TOKEN=tu_token_de_verificacion

# OpenAI API
OPENAI_API_KEY=tu_api_key_de_openai
VECTOR_STORE_ID=tu_vector_store_id

# Opcional
ENVIRONMENT=development
```

### 4. Ejecutar la aplicación
```bash
# Desarrollo
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app:app --host 0.0.0.0 --port 8000
```

## 📋 Configuración de WhatsApp Cloud API

1. **Crear una aplicación** en [Meta for Developers](https://developers.facebook.com/)
2. **Configurar WhatsApp Business API**
3. **Obtener credenciales**:
   - `WHATSAPP_TOKEN`: Token de acceso de la aplicación
   - `PHONE_NUMBER_ID`: ID del número de teléfono de WhatsApp Business
   - `VERIFY_TOKEN`: Token personalizado para verificación de webhook

4. **Configurar webhook**:
   - URL: `https://tu-dominio.com/webhook`
   - Verificar token: el mismo valor que `VERIFY_TOKEN`
   - Suscribirse a: `messages`

## 🧠 Configuración de OpenAI

1. **Obtener API Key** de [OpenAI Platform](https://platform.openai.com/)
2. **Crear Vector Store** (opcional) para búsqueda en documentos
3. **Cargar documentos** al vector store para respuestas basadas en conocimiento

## 📱 Tipos de Contenido Soportados

| Tipo | Descripción | Procesamiento IA | Reenvío |
|------|-------------|-----------------|---------|
| 📝 **Texto** | Mensajes de texto plano | ✅ Conversación natural | ❌ |
| 📷 **Imágenes** | Fotos y capturas | ✅ Análisis visual | ✅ Con descripción |
| 🎵 **Audio** | Mensajes de voz | ✅ Reconocimiento de contexto | ✅ |
| 📄 **Documentos** | PDFs, Word, etc. | ✅ Procesamiento de contenido | ✅ Con resumen |
| 📍 **Ubicaciones** | Coordenadas GPS | ✅ Información contextual | ✅ |
| 👤 **Contactos** | Información de contactos | ✅ Procesamiento de datos | ❌ |
| 😀 **Stickers** | Emojis animados | ✅ Interpretación emocional | ✅ |

## 🔗 API Endpoints

### Webhook Principal
- `GET /webhook` - Verificación de webhook de WhatsApp
- `POST /webhook` - Recepción de mensajes de WhatsApp

### Salud y Monitoreo
- `GET /` - Estado básico del bot
- `GET /health` - Verificación detallada del entorno

### Pruebas
- `POST /test-whatsapp` - Enviar mensaje de prueba
- `POST /test-file-search` - Probar búsqueda en documentos

## 🔧 Ejemplos de Uso

### Conversación de Texto
```
Usuario: "¿Cuál es la capital de Francia?"
Bot: "La capital de Francia es París. Es conocida como la Ciudad de la Luz y es famosa por la Torre Eiffel, el Louvre y su rica historia cultural."
```

### Análisis de Imagen
```
Usuario: [Envía foto de un gato]
Bot: "¡Qué hermoso gato! Puedo ver que es un felino doméstico con pelaje [descripción]. Los gatos son mascotas maravillosas conocidas por su independencia y cariño."
```

### Búsqueda en Documentos
```
Usuario: "¿Cuáles son las políticas de la empresa sobre trabajo remoto?"
Bot: [Busca en documentos cargados] "Según las políticas de la empresa, el trabajo remoto está permitido hasta 3 días por semana..."
```

## 🚀 Despliegue en Render

Este proyecto incluye configuración para despliegue en [Render](https://render.com/):

1. **Conectar repositorio** en Render
2. **Configurar variables de entorno** en el dashboard
3. **Desplegar automáticamente** con `render.yaml`

Las variables de entorno requeridas se configuran automáticamente según `render.yaml`.

## 🛠️ Desarrollo

### Estructura del Proyecto
```
wachat/
├── app.py              # Aplicación principal FastAPI
├── requirements.txt    # Dependencias Python
├── render.yaml        # Configuración de despliegue
├── .env              # Variables de entorno (crear)
└── README.md         # Este archivo
```

### Funciones Principales

- `get_openai_response_with_media()` - Genera respuestas IA con soporte multimedia
- `send_whatsapp_message()` - Envía mensajes de texto
- `send_whatsapp_media()` - Envía contenido multimedia
- `download_media_file()` - Descarga archivos de WhatsApp
- `extract_message_data()` - Procesa webhooks entrantes

### Logging

El bot incluye logging detallado para debugging:
- Mensajes entrantes y salientes
- Errores de API
- Procesamiento de multimedia
- Respuestas de OpenAI

## 🔒 Seguridad

- ✅ Verificación de tokens de webhook
- ✅ Validación de variables de entorno
- ✅ Manejo seguro de credenciales
- ✅ Logging sin exposición de datos sensibles

## 🤝 Contribución

1. **Fork** el proyecto
2. **Crear** una rama feature (`git checkout -b feature/nueva-caracteristica`)
3. **Commit** los cambios (`git commit -m 'Agregar nueva característica'`)
4. **Push** a la rama (`git push origin feature/nueva-caracteristica`)
5. **Abrir** un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si encuentras algún problema o tienes preguntas:

1. **Revisa los logs** del servidor para errores específicos
2. **Verifica las variables de entorno** con `/health`
3. **Prueba los endpoints** con `/test-whatsapp` y `/test-file-search`
4. **Abre un issue** en GitHub con detalles del problema

---

**WaChat Bot** - Transformando conversaciones de WhatsApp con IA 🚀