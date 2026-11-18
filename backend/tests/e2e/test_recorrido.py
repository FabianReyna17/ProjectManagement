"""TEC-02: recorrido completo en el navegador y regresión de permisos en la interfaz.

login → proyecto → tareas → bloqueo → aviso → cierre, con las personas que lo harían en la
organización, cada una con su propia sesión.
"""
import re
from datetime import date, timedelta

from playwright.sync_api import expect

CLAVE_ADMIN = "Admin-Segura-2026"


def preparar_admin(persona):
    """Primer ingreso de una instalación nueva: el admin debe cambiar la contraseña inicial."""
    adm = persona()
    p = adm.pagina
    adm.entrar("admin", "Admin123!")
    p.wait_for_url("**/#/cambiar-contrasena")
    expect(p.get_by_text("Entraste con una contraseña temporal")).to_be_visible()
    p.fill("#f-password [name=actual]", "Admin123!")
    p.fill("#f-password [name=nueva]", CLAVE_ADMIN)
    p.fill("#f-password [name=repetida]", CLAVE_ADMIN)
    p.click("#f-password button.boton")
    p.wait_for_url("**/#/proyectos")
    return adm


def registrar(adm, usuario, nombre, funcion):
    p = adm.pagina
    adm.ir("#/usuarios")
    p.fill("#f-usuario [name=usuario]", usuario)
    p.fill("#f-usuario [name=nombre]", nombre)
    p.fill("#f-usuario [name=password]", "clave123")
    p.select_option("#f-usuario [name=funcion_id]", label=funcion)
    p.click("#f-usuario button.boton")
    expect(p.locator("#tabla-usuarios")).to_contain_text(nombre)


def test_recorrido_completo(persona):
    hoy = date.today()
    adm = preparar_admin(persona)
    registrar(adm, "ana", "Ana López", "Responsable")
    registrar(adm, "beto", "Beto Ramírez", "Integrante")
    adm.salir()

    # Ana crea el proyecto, da acceso a Beto y le asigna una tarea
    ana = adm
    p = ana.pagina
    ana.entrar("ana", "clave123")
    p.wait_for_url("**/#/proyectos")
    p.get_by_role("link", name="Nuevo proyecto").first.click()
    p.fill("#f-proyecto [name=nombre]", "Portal de clientes")
    p.fill("#f-proyecto [name=objetivo]", "Publicar el portal para clientes")
    p.fill("#f-proyecto [name=fecha_inicio]", hoy.isoformat())
    p.fill("#f-proyecto [name=fecha_fin]", (hoy + timedelta(days=60)).isoformat())
    p.click("#f-proyecto button.boton")
    p.wait_for_url(re.compile(r"#/proyectos/\d+$"))
    url_proyecto = p.url
    p.select_option("#f-participante [name=usuario_id]", label="Beto Ramírez (Integrante)")
    p.click("#f-participante button")
    expect(p.locator(".lista-personas")).to_contain_text("Beto Ramírez")
    p.get_by_role("link", name="Nueva tarea").first.click()
    p.fill("#f-tarea [name=nombre]", "Diseñar la portada")
    p.fill("#f-tarea [name=descripcion]", "Maqueta de la página de inicio")
    p.select_option("#f-tarea [name=responsable_id]", label="Beto Ramírez")
    p.fill("#f-tarea [name=fecha_limite]", (hoy + timedelta(days=10)).isoformat())
    p.click("#f-tarea button.boton")
    p.wait_for_url(re.compile(r"#/tareas/\d+$"))
    url_tarea = p.url
    ana.salir()

    # Beto recibe el aviso de asignación, inicia la tarea y reporta un bloqueo
    beto = ana
    p = beto.pagina
    beto.entrar("beto", "clave123")
    p.wait_for_url("**/#/proyectos")
    expect(p.locator(".nav-principal [data-contador-avisos]")).to_contain_text("1")
    beto.ir("#/avisos")
    p.get_by_role("link", name=re.compile("Diseñar la portada")).first.click()
    p.wait_for_url(url_tarea)
    p.click("#prop-estado [data-estado=en_curso]")
    expect(p.locator("#prop-estado")).to_contain_text("En curso")
    p.get_by_role("button", name="Reportar bloqueo").click()
    p.fill("#f-bloqueo [name=motivo]", "Falta el logotipo del cliente")
    p.click("#f-bloqueo button.boton")
    expect(p.locator(".bloqueo-abierto")).to_contain_text("Falta el logotipo del cliente")
    beto.salir()

    # Ana recibe el aviso del bloqueo, lo resuelve, termina la tarea y cierra el proyecto
    p = ana.pagina
    ana.entrar("ana", "clave123")
    p.wait_for_url("**/#/proyectos")
    ana.ir("#/avisos")
    expect(p.locator(".no-leido").first).to_contain_text("Falta el logotipo")
    p.locator(".no-leido a").first.click()
    p.wait_for_url(url_tarea)
    p.fill("#f-resolver [name=resolucion]", "El cliente envió el logotipo")
    p.click("#f-resolver button.boton")
    expect(p.locator(".bloqueo-abierto")).to_have_count(0)
    p.click("#prop-estado [data-estado=terminada]")
    expect(p.locator("#prop-estado")).to_contain_text("Terminada")
    p.goto(url_proyecto)
    p.get_by_role("link", name="Cerrar proyecto").click()
    expect(p.get_by_text("Todas las tareas están terminadas")).to_be_visible()
    p.fill("#f-cierre [name=justificacion]", "Portal publicado")
    p.click("#f-cierre button.boton")
    ana.confirmar()
    p.wait_for_url(url_proyecto)
    expect(p.locator("h1 + .chip, .titulo-con-chip").first).to_contain_text("Cerrado")
    ana.ir("#/proyectos?cerrados")
    expect(p.locator("main")).to_contain_text("Portal de clientes")
    # el proyecto cerrado ya no admite tareas nuevas
    expect(p.get_by_role("link", name="Nueva tarea")).to_have_count(0)


def test_permisos_en_la_interfaz(persona):
    adm = preparar_admin(persona)
    registrar(adm, "ana", "Ana López", "Responsable")
    registrar(adm, "carla", "Carla Díaz", "Integrante")

    ana = persona()
    p = ana.pagina
    ana.entrar("ana", "clave123")
    p.wait_for_url("**/#/proyectos")
    ana.ir("#/proyectos/nuevo")
    p.fill("#f-proyecto [name=nombre]", "Interno")
    p.fill("#f-proyecto [name=objetivo]", "Uso interno")
    p.fill("#f-proyecto [name=fecha_inicio]", "2026-11-01")
    p.fill("#f-proyecto [name=fecha_fin]", "2026-12-31")
    p.click("#f-proyecto button.boton")
    p.wait_for_url(re.compile(r"#/proyectos/\d+$"))
    ruta_proyecto = "#" + p.url.split("#", 1)[1]

    # quien no participa no lo ve ni con el enlace; el Admin tampoco por su función
    carla = persona()
    c = carla.pagina
    carla.entrar("carla", "clave123")
    c.wait_for_url("**/#/proyectos")
    expect(c.locator("main")).not_to_contain_text("Interno")
    carla.ir(ruta_proyecto)
    expect(c.get_by_role("heading", name="Sin acceso")).to_be_visible()
    expect(c.locator("main")).not_to_contain_text("Interno")
    carla.ir("#/usuarios")
    expect(c.get_by_role("heading", name="Sin acceso")).to_be_visible()
    adm.ir(ruta_proyecto)
    expect(adm.pagina.get_by_role("heading", name="Sin acceso")).to_be_visible()

    # el Admin desactiva a Carla: su sesión abierta deja de servir en la siguiente acción
    a = adm.pagina
    adm.ir("#/usuarios")
    a.locator("tr", has_text="Carla Díaz").get_by_role("button", name="Desactivar").click()
    adm.confirmar()
    expect(a.locator("tr", has_text="Carla Díaz")).to_contain_text("Cuenta desactivada")
    carla.ir("#/mis-tareas")
    c.wait_for_url("**/#/login")
    expect(c.get_by_text("Tu sesión ya no es válida")).to_be_visible()
    carla.entrar("carla", "clave123")
    expect(c.locator("#error-login")).to_contain_text("Usuario o contraseña incorrectos")

    # el Admin restablece el acceso de Ana: su sesión se cierra y entra con la temporal
    a.locator("tr", has_text="Ana López").get_by_role("button", name="Restablecer acceso").click()
    adm.confirmar()
    temporal = a.locator(".credencial-valor code").inner_text()
    assert len(temporal) == 12
    ana.ir("#/proyectos")
    p.wait_for_url("**/#/login")
    ana.entrar("ana", temporal)
    p.wait_for_url("**/#/cambiar-contrasena")
    ana.ir("#/proyectos")  # no puede saltarse el cambio
    p.wait_for_url("**/#/cambiar-contrasena")
    p.fill("#f-password [name=actual]", temporal)
    p.fill("#f-password [name=nueva]", "nueva-clave")
    p.fill("#f-password [name=repetida]", "nueva-clave")
    p.click("#f-password button.boton")
    p.wait_for_url("**/#/proyectos")
    expect(p.locator("main")).to_contain_text("Interno")  # conserva su proyecto

    # el historial de accesos muestra lo ocurrido con actor y valores
    adm.ir("#/cambios-acceso")
    tabla = a.locator("#tabla-accesos")
    expect(tabla).to_contain_text("Cuenta desactivada")
    expect(tabla).to_contain_text("Acceso restablecido")
    expect(tabla.locator("tr", has_text="Acceso al proyecto")).to_contain_text("Interno")


def test_se_usa_desde_el_telefono(persona):
    adm = preparar_admin(persona)
    registrar(adm, "ana", "Ana López", "Responsable")
    tel = persona(telefono=True)
    p = tel.pagina
    tel.entrar("ana", "clave123")
    p.wait_for_url("**/#/proyectos")
    expect(p.locator(".nav-inferior")).to_be_visible()
    tel.ir("#/proyectos/nuevo")
    p.fill("#f-proyecto [name=nombre]", "Desde el teléfono")
    p.fill("#f-proyecto [name=objetivo]", "Probar la vista móvil")
    p.fill("#f-proyecto [name=fecha_inicio]", "2026-11-01")
    p.fill("#f-proyecto [name=fecha_fin]", "2026-12-31")
    p.click("#f-proyecto button.boton")
    p.wait_for_url(re.compile(r"#/proyectos/\d+$"))
    for ruta in ("#/proyectos", "#/mis-tareas", "#/avisos", "#/estado-proyectos", "#/carga"):
        tel.ir(ruta)
        p.locator("main h1").first.wait_for()
        assert not p.evaluate("document.documentElement.scrollWidth > innerWidth"), ruta
    tel_adm = persona(telefono=True)
    tel_adm.entrar("admin", CLAVE_ADMIN)
    tel_adm.pagina.wait_for_url("**/#/proyectos")
    for ruta in ("#/usuarios", "#/respaldos", "#/cambios-acceso"):
        tel_adm.ir(ruta)
        tel_adm.pagina.locator("main h1").first.wait_for()
        assert not tel_adm.pagina.evaluate("document.documentElement.scrollWidth > innerWidth"), ruta
