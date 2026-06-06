FICHA TÉCNICA DE LA ENTREVISTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Candidato: {{ candidato }}
• Posición: {{ posicion }}
• Fecha: {{ fecha }}
• Entrevistador: {{ entrevistador }}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{% for eval in evaluaciones %}
Competencia a Evaluar: {{ eval.competencia }}

Pregunta STAR: "{{ eval.pregunta }}"

| Componente | Evidencias | Notas del Entrevistador |
|------------|------------|-------------------------|
| Situación  | {{ eval.situacion or '—' }} | |
| Tarea      | {{ eval.tarea or '—' }} | |
| Acción     | {{ eval.accion or '—' }} | |
| Resultado  | {{ eval.resultado or '—' }} | |

Calificación: {{ eval.calificacion }}/4 — {{ eval.calificacion_label }}

{% endfor %}
{% if conclusion %}
Conclusión del Reclutador: {{ conclusion }}
{% endif %}
