{{- define "weatherapp.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "weatherapp.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "weatherapp.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "weatherapp.labels" -}}
app.kubernetes.io/name: {{ include "weatherapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "weatherapp.imageRef" -}}
{{- $repository := .repository -}}
{{- if and (hasKey . "digest") .digest -}}
{{- printf "%s@%s" $repository .digest -}}
{{- else -}}
{{- printf "%s:%s" $repository .tag -}}
{{- end -}}
{{- end -}}
