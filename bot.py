import discord
from discord import app_commands
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from webserver import keep_alive  # servidor para mantener activo

# Cargar variables de entorno
TOKEN = os.getenv("DISCORD_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Convertir variable JSON en dict
creds_dict = json.loads(CREDS_JSON)

# Conexión con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Porcentajes de mejoras
PCT_FULL = 0.20
PCT_ESTETICO = 0.03
PCT_RENDIMIENTO = 0.05

# Intents y bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Mantener el bot activo en Render
keep_alive()

# Función para buscar coches o servicios por código
def buscar_item(codigo):
    datos = sheet.get_all_records()
    codigo_buscar = codigo.strip().upper()
    for fila in datos:
        if fila["Codigo"].strip().upper() == codigo_buscar:
            nombre_real = fila["Nombre"].strip()
            precio = float(fila["Precio"])
            return nombre_real, precio
    return None, None

# Conexión y sincronización de comandos slash
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Comandos slash sincronizados ({len(synced)} comandos)")
    except Exception as e:
        print(e)

# Comando slash Full Tuning
@bot.tree.command(name="full", description="Calcula el precio del full tuning de un coche")
@app_commands.describe(codigo="Código del coche")
async def full(interaction: discord.Interaction, codigo: str):
    nombre, precio = buscar_item(codigo)
    if not nombre:
        await interaction.response.send_message(f"No encontré el coche con código '{codigo}'", ephemeral=True)
        return
    total = precio * PCT_FULL
    total_fmt = f"{total:,.2f}".replace(",", ".")
    await interaction.response.send_message(f"💥 Full tuning de {nombre} → {total_fmt} €")

# Comando slash Cambios estéticos
@bot.tree.command(name="est", description="Calcula el precio de cambios estéticos de un coche")
@app_commands.describe(cantidad="Número de cambios estéticos", codigo="Código del coche")
async def est(interaction: discord.Interaction, cantidad: int, codigo: str):
    nombre, precio = buscar_item(codigo)
    if not nombre:
        await interaction.response.send_message(f"No encontré el coche con código '{codigo}'", ephemeral=True)
        return
    total = precio * PCT_ESTETICO * cantidad
    total_fmt = f"{total:,.2f}".replace(",", ".")
    await interaction.response.send_message(f"💄 {cantidad} cambio(s) estético(s) en {nombre} → {total_fmt} €")

# Comando slash Cambios de rendimiento
@bot.tree.command(name="ren", description="Calcula el precio de cambios de rendimiento de un coche")
@app_commands.describe(cantidad="Número de cambios de rendimiento", codigo="Código del coche")
async def ren(interaction: discord.Interaction, cantidad: int, codigo: str):
    nombre, precio = buscar_item(codigo)
    if not nombre:
        await interaction.response.send_message(f"No encontré el coche con código '{codigo}'", ephemeral=True)
        return
    total = precio * PCT_RENDIMIENTO * cantidad
    total_fmt = f"{total:,.2f}".replace(",", ".")
    await interaction.response.send_message(f"⚙️ {cantidad} cambio(s) de rendimiento en {nombre} → {total_fmt} €")

# Comando slash Tune (rendimiento + estético)
@bot.tree.command(name="tune", description="Calcula el total de cambios de rendimiento y estéticos de un coche")
@app_commands.describe(
    rendimiento="Cantidad de cambios de rendimiento",
    estetico="Cantidad de cambios estéticos",
    codigo="Código del coche"
)
async def tune(interaction: discord.Interaction, rendimiento: int, estetico: int, codigo: str):
    nombre, precio = buscar_item(codigo)
    if not nombre:
        await interaction.response.send_message(f"No encontré el coche con código '{codigo}'", ephemeral=True)
        return
    
    total_rendimiento = precio * PCT_RENDIMIENTO * rendimiento
    total_estetico = precio * PCT_ESTETICO * estetico
    total = total_rendimiento + total_estetico

    total_rendimiento_fmt = f"{total_rendimiento:,.2f}".replace(",", ".")
    total_estetico_fmt = f"{total_estetico:,.2f}".replace(",", ".")
    total_fmt = f"{total:,.2f}".replace(",", ".")
    
    await interaction.response.send_message(
        f"⚙️ Cambios de rendimiento ({rendimiento}) → {total_rendimiento_fmt} €\n"
        f"💄 Cambios estéticos ({estetico}) → {total_estetico_fmt} €\n"
        f"🔹 Total → {total_fmt} €"
    )

# Comando slash Precio unificado (coches o servicios)
@bot.tree.command(name="precio", description="Muestra el precio de un coche o servicio usando el código")
@app_commands.describe(codigo="Código del coche o servicio")
async def precio(interaction: discord.Interaction, codigo: str):
    nombre_real, valor = buscar_item(codigo)
    if not nombre_real:
        await interaction.response.send_message(
            f"No encontré ningún coche o servicio con código '{codigo}'", ephemeral=True
        )
        return
    valor_fmt = f"{valor:,.2f}".replace(",", ".")
    await interaction.response.send_message(f"💰 Precio de {nombre_real} → {valor_fmt} €")

# Ejecutar el bot
bot.run(TOKEN)
