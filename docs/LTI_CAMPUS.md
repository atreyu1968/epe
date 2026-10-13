# Empresa en el Aula (0446) — LTI 1.3 para Campus Moodle

**Estado: implementado y comprobado localmente con lanzamientos OIDC firmados; aún no certificado en Campus real.** La instalación en el Moodle institucional exige completar el registro de la herramienta y verificar el primer lanzamiento.

## 1. Qué aporta

El mismo ERP de las siete unidades puede abrirse mediante una **actividad Herramienta externa LTI 1.3** del curso. Moodle autentica mediante OpenID Connect y firma la información de lanzamiento con RS256. El servidor de EPE valida `issuer`, `audience`, `nonce`, `deployment_id`, `resource_link`, `context` y una ventana temporal. Enlace de cuentas **supervisado por el profesor**: un estudiante no puede elegir su empresa ni suplantar a otro simplemente enviando un nombre. Tras vincular su identidad con una cuenta ERP ya provisionada, accede al portafolio sin una segunda contraseña.

- OIDC LTI: `/lti/login`, `/lti/launch`, `/lti/portal`.
- Claves públicas de la herramienta: `/lti/.well-known/jwks.json`.
- Portafolios en las siete unidades: `/lti/app/u1/portfolio/` … `/lti/app/u7/portfolio/`.
- Panel docente de asignación: `/lti/admin/` (protegido con la clave docente del ERP).
- Servicios LTI Advantage: NRPS opcional (`/lti/admin/remote-members?context_id=...`) y AGS opcional para portafolios.
- La aplicación **no crea automáticamente equipos desde Moodle**: NRPS no garantiza la pertenencia a grupos. Cada cuenta ERP ya pertenece a una empresa de cuatro o cinco integrantes y el docente vincula cada identidad del Campus con esa cuenta.
- Se mantienen los 21 SCORM originales, las siete bases de datos y los expedientes. Examen individual y recuperación continúan en sus paquetes SCORM propios.

## 2. Variables de configuración privadas del servidor

Configurar **únicamente en** `/etc/epe/epe.env` del LXC EPE (no en GitHub):

```ini
EPE_PUBLIC_URL=https://erp.TU-DOMINIO.es
EPE_LTI_ISSUER=https://CAMPUS_REAL.es
EPE_LTI_CLIENT_ID=IDENTIFICADOR_CLIENTE_ENTREGADO_POR_MOODLE
EPE_LTI_DEPLOYMENT_ID=DESPLIEGUE_ENTREGADO_POR_MOODLE
EPE_LTI_AUTH_URL=https://CAMPUS_REAL.es/mod/lti/auth.php
EPE_LTI_JWKS_URL=https://CAMPUS_REAL.es/mod/lti/certs.php
EPE_LTI_TOKEN_URL=https://CAMPUS_REAL.es/mod/lti/token.php
EPE_LTI_PRIVATE_KEY_FILE=/etc/epe/lti-private.pem
EPE_LTI_GRADE_MODE=disabled
```

Las URL de Moodle son **ejemplos de rutas habituales**, no valores confirmados de Campus. Copiarlas de la información de registro del propio Moodle si difieren. `EPE_PUBLIC_URL` es la dirección HTTPS externa real que dirige el Cloudflare Tunnel existente hacia el LXC ERP. **No crear un segundo túnel**. Los nombres `EPE_LTI_CLIENT_ID` y `EPE_LTI_DEPLOYMENT_ID` se completan después del registro, nunca se inventan.

La clave privada RSA se genera localmente por el instalador y debe tener permisos de lectura solo para `root` y el grupo `epe`. No publicarla ni almacenarla dentro del ZIP de alumnos. Al cambiar esa clave, actualizar las claves públicas registradas en Moodle y considerar los tokens emitidos anteriormente.

## 3. Registrar LTI desde el perfil de profesor

Se ha comprobado visualmente que en tu Campus aparece `Añadir herramienta externa LTI > Versión LTI 1.3`, `Servicios` y `Privacidad`. Rellena **cuando el servidor HTTPS esté operativo**:

| Campo | Valor |
| --- | --- |
| Nombre | `Empresa en el Aula FP` |
| URL de herramienta / destino | `https://erp.TU-DOMINIO.es/lti/launch` |
| Versión | **LTI 1.3** |
| Tipo de clave pública | URL del conjunto de claves |
| Conjunto de claves públicas | `https://erp.TU-DOMINIO.es/lti/.well-known/jwks.json` |
| URL de inicio de sesión | `https://erp.TU-DOMINIO.es/lti/login` |
| URL(s) de redirección | `https://erp.TU-DOMINIO.es/lti/launch` |
| Servicio de calificación | Sincronización de notas y administración de columnas si la política del Campus lo permite |
| Aprovisionamiento de nombres/roles | Según política de privacidad del Campus |
| Privacidad | Compartir solo los datos estrictamente necesarios; el correo electrónico no es necesario para el vínculo |
| Contenedor de inicio | **Ventana nueva**, especialmente si el navegador bloquea cookies de terceros en iframes |

Moodle puede requerir autorización o registro completo por parte del administrador, incluso si permite al profesor abrir y rellenar el formulario. Al finalizar, buscar los valores reales **Client ID**, **Deployment ID** y las direcciones de plataforma emitidas por Moodle. Añadirlos a `/etc/epe/epe.env` y ejecutar:

```bash
systemctl restart epe
systemctl status epe --no-pager
curl -fsS https://erp.TU-DOMINIO.es/lti/health
curl -fsS https://erp.TU-DOMINIO.es/lti/.well-known/jwks.json
```

No existe una conexión LTI válida hasta que Moodle envía el primer `id_token` firmado y se supera la validación criptográfica en el servidor.

## 4. Crear empresas y vincular estudiantes

Una sola vez, y solo con las bases de datos vacías, utilizar el asistente ya incluido en EPE, por ejemplo:

```bash
cd /opt/epe/app
runuser -u epe -- /opt/epe/venv/bin/python -m runtime.manage crear \
  --equipos 2 --tamanos 4,5 --salida /var/lib/epe/private/credenciales_epe.csv
```

No repetir `crear` en cursos con expedientes existentes. Si el servidor ya dispone de estudiantes de otros ciclos o cursos, planificar expresamente el aislamiento de cohortes antes de incorporar nuevos cursos.

1. Crear la actividad LTI en el curso Moodle y probar con una cuenta de alumno ficticio, en **ventana nueva**.
2. Al abrirla, verá «Tu profesor debe asignarte a una empresa». Este estado es deliberado, no es un error de inicio de sesión.
3. Abrir `https://erp.TU-DOMINIO.es/lti/admin/` con la credencial docente configurada en `/etc/epe/epe.env` (usuario HTTP Basic: `profesor`). La clave se conserva exclusivamente en el servidor.
4. Elegir para cada identidad LTI la cuenta EPE que corresponde al equipo/empresa. El panel impide vincular dos personas a la misma cuenta y no permite que el alumno elija libremente su empresa.
5. Pedir al alumno que reabra la actividad desde Campus. Verá las siete unidades y entrará en el portafolio de su empresa sin segunda contraseña.

La vinculación es deliberadamente irreversible desde la interfaz del profesor: una modificación por traslado debe auditarse en administración, no se cambia silenciosamente.

## 5. Envío de calificaciones AGS sin duplicarlas

**Por defecto `EPE_LTI_GRADE_MODE=disabled`.** Primero verificar, con alumno ficticio, el acceso, la terminación de portafolio y los permisos AGS. Solo entonces configurar `EPE_LTI_GRADE_MODE=portfolio` y reiniciar el servicio.

Cuando un portafolio está completamente acreditado, el servidor genera o reutiliza un elemento de calificación específico (por unidad) y comunica **exclusivamente la nota del portafolio** a Moodle. No transmite la nota del examen mediante AGS: el examen individual permanece en el SCORM independiente. No activar simultáneamente el SCORM portafolio tradicional y su equivalente LTI como dos notas ponderadas: **se duplicaría la calificación**.

Libro de calificaciones sugerido: por cada RA, portafolio LTI **60 %**, examen SCORM **40 %**; recuperación por CE sin porcentaje añadido. Pesos globales: U1=15 %, U2=12 %, U3=12 %, U4=31 %, U5=15 %, U6=8 %, U7=7 %. **Un promedio >= 5 no reemplaza la comprobación de que todos los CE del RA están superados.**

Las notas se envían solo si Moodle autoriza el servicio `AGS` de creación de columnas y publicación de puntuaciones, y después de completar el portafolio. Si la conexión con Campus falla, la evidencia local se conserva; debe revisarse la sincronización antes de cerrar el acta. El envío puede necesitar ajustes según la política real de Moodle, que aún no está comprobada.

## 6. Seguridad, datos y recuperación

- LTI exige HTTPS y URL de plataforma previamente autorizada; no aceptar claves públicas de una URL indicada dinámicamente por un alumno.
- Almacenar claves, expedientes, identificadores LMS y bases SQLite **en el servidor privado**, no en GitHub ni en el ZIP de alumnos.
- La nueva base `lti.sqlite` se guarda junto a las siete bases de unidades y `course.sqlite`; el sistema de copia ya realiza backups de todos los `*.sqlite` de la carpeta.
- Los identificadores LTI de usuarios están separados de `lms_id` de los antiguos SCORM y se vinculan explícitamente a un `username` EPE ya existente.
- Si el navegador no permite enviar las cookies de sesión en un iframe de otro dominio, establecer la actividad en **ventana nueva**. La sesión no se puede autenticar simplemente desactivando esas comprobaciones.
- Cerrar el acceso desde Campus y no compartir enlaces de las actividades LTI fuera del curso.
- Probar dos equipos de 4 y 5, pérdida de conectividad, suplencias, un alumno pendiente, replay de token, acceso a otros equipos y envío correcto de notas antes del uso oficial.
- Las URL de ejemplo y las cuentas ficticias no constituyen una instalación funcional en el Campus real.
