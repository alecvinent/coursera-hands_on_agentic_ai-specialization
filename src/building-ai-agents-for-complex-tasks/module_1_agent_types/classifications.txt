Para completar la **Tarea 1** basada en el documento de *Global Logistics Corp.*, aquí tienes una plantilla completa con la clasificación de las 6 aplicaciones típicas de IA en logística y mantenimiento, junto con sus justificaciones y propuestas de mejora.

---

### Clasificación de Aplicaciones de IA

**1. Sensor de Alerta Inmediata por Sobrecalentamiento del Motor**

* **Clasificación:** Reactivo.
* **Justificación:** Responde de forma directa e inmediata a un umbral de temperatura excedido sin mantener un historial de datos ni planificar acciones futuras.

**2. Optimizador de Rutas Basado en Tráfico en Tiempo Real y Entregas Pendientes**

* **Clasificación:** Híbrido.
* **Justificación:** Combina la capacidad deliberativa (planificación previa de secuencias de entrega) con respuestas reactivas ante eventos imprevistos como congestión vehicular.

**3. Sistema de Mantenimiento Predictivo Basado en Historial y Sensor de Kilometraje**

* **Clasificación:** Deliberativo.
* **Justificación:** Utiliza un modelo interno y memoria histórica para predecir fallas y planificar los servicios de taller antes de que ocurra una avería.



**4. Frenado Autónomo de Emergencia por Detección de Obstáculos**

* **Clasificación:** Reactivo.
* **Justificación:** Actúa mediante una regla estímulo-respuesta directa al detectar un objeto en la vía para evitar colisiones sin pasar por un proceso de razonamiento complejo.

**5. Planificador Semanal de Asignación de Flota y Cargas por Hub Regional**

* **Clasificación:** Deliberativo.
* **Justificación:** Analiza grandes volúmenes de datos proyectados, disponibilidad de camiones y restricciones para optimizar la distribución a largo plazo.

**6. Asistente de Conducción para Desvío Dinámico según Estado del Clima**

* **Clasificación:** Híbrido.
* **Justificación:** Mantiene la ruta planificada del viaje (deliberativo) mientras calcula ajustes dinámicos y desvíos instantáneos al detectar alertas meteorológicas (reactivo).

---

### Propuestas de Mejora Arquitectónica

**Mejora 1: De Reactivo a Híbrido (Sensor de Alerta por Sobrecalentamiento)**

* **Propuesta:** Integrar una memoria de lecturas térmicas y un módulo de predicción que no solo emita una alerta cuando el motor se sobrecaliente, sino que analice la tendencia de temperatura junto con la telemetría del camión para reprogramar automáticamente una parada de revisión en el punto de entrega más cercano.

**Mejora 2: De Híbrido a Más Deliberativo (Optimizador de Rutas en Tiempo Real)**

* **Propuesta:** Incorporar modelos de aprendizaje profundo que simulen múltiples escenarios dinámicos (patrones históricos de tráfico por hora/clima, tiempos de descarga por cliente y restricciones de descanso del conductor) para reconfigurar la estrategia global del hub regional en lugar de reaccionar solo con desvíos locales.