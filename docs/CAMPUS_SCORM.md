# Configuración del curso EPE en Campus/Moodle

## Antes de subir archivos

1. Comprobar `https://DOMINIO_PUBLICO_ERP/api/health` desde el equipo del profesor.
2. Confirmar que los 21 ZIP han sido generados con `python -m runtime.configurar_scorms --servidor https://DOMINIO_PUBLICO_ERP` y conservan un `imsmanifest.xml`.
3. Confirmar que `EPE_ALLOWED_ORIGINS` en `/etc/epe/epe.env` coincide **exactamente** con el origen de Moodle (`https://dominio`, sin ruta ni barra final).
4. Utilizar cuentas individuales en Moodle y en EPE. La creación de un grupo en Campus **no** crea por sí sola una empresa en EPE.

## Crear las actividades

Como **profesor editor**, activar edición y crear siete secciones (Unidad 1 a Unidad 7). En cada sección añadir, por este orden, tres actividades **Paquete SCORM**:

- `Ux · Portafolio cooperativo`: importar `EPE_Ux_Portafolio_INTEGRADO.zip`.
- `Ux · Examen individual`: importar `EPE_Ux_Examen_INTEGRADO.zip`.
- `Ux · Recuperación por criterios`: importar `EPE_Ux_Recuperacion_INTEGRADO.zip`; mantener oculto/restringido hasta su asignación.

Cada archivo se sube **sin descomprimir**. No subir el ZIP maestro, ni el TAR de exportación de SCORM, como actividades.

## Ajustes iniciales recomendados de SCORM 1.2

| Campo | Valor inicial de prueba |
|---|---|
| Paquete | ZIP SCORM individual |
| Intentos Moodle | 1, permitiendo reentrada al mismo intento |
| Forzar nuevo intento | No |
| Forzar finalización | No |
| Calificación máxima | 100 |
| Método de calificación | Calificación más alta |
| Presentación | Ventana actual amplia / 100 %; probar alternativa si falla |
| Recuperación | Excluir del promedio ordinario / ponderación 0 |

**Importante:** los intentos internos del ERP no equivalen a intentos del reproductor Moodle; no forzar un nuevo intento por cada reentrada.

## Grupos, participación individual y evaluación

Crear equipos de 4–5 alumnos mediante el menú `Participantes > Grupos` y vincular manualmente cada grupo Moodle con su empresa correspondiente en el ERP. No se comparten contraseñas de empresa; cada alumno accede con su cuenta personal.

Dentro de cada unidad: **60 % portafolio cooperativo + 40 % examen individual**. Pesos de los RA/unidades sobre el módulo:

| RA/Unidad | Peso |
|---|---:|
| U1 | 15 % |
| U2 | 12 % |
| U3 | 12 % |
| U4 | 31 % |
| U5 | 15 % |
| U6 | 8 % |
| U7 | 7 % |
| **Total** | **100 %** |

En el libro de calificaciones, crear categorías RA1–RA7 con esos pesos y ponderar portafolio/examen 60/40 dentro de cada categoría, **si los permisos y versión Moodle lo permiten**.

SCORM 1.2 remite **una calificación por actividad**, no todas las calificaciones desagregadas por criterio. Consultar los informes del ERP. La condición `todos los criterios y RA superados` requiere comprobación expresa, no únicamente promedio numérico. No incorporar la recuperación como tercera nota ordinaria.

## Prueba piloto obligatoria antes de evaluar

Con usuarios ficticios y dos empresas de 4 y 5 miembros comprobar:

1. Abrir, completar parcialmente, guardar, salir y volver a entrar al portafolio U1; verificar persistencia.
2. Comprobar en informe de actividad de Campus la nota `cmi.core.score.raw` y la identidad del alumno.
3. Acceder desde U5 al Historial ERP y encontrar un documento validado en U4 por la misma empresa.
4. Confirmar que otra empresa no puede verlo ni enlazarlo.
5. Probar suplencias, autoría y evaluación individual.
6. Comprobar examen individual, recuperación solo de criterios pendientes e informe docente.
7. Comprobar que RA7 no se considera superado sin la rúbrica docente cuando corresponda.

Si falla guardado, identidad, nota, aislamiento o un criterio de seguridad, suspender el uso en evaluación real y revisar las incidencias. La integración **todavía no se ha certificado en el Moodle real**.
